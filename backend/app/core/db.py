"""Engine, sessions and the per-request tenancy scope used by row-level security.

Every transaction on an app session starts with three transaction-local settings
(app.scope, app.user_id, app.vendor_id). The RLS policies in the migration read
them, so a query that forgets a tenant filter still cannot return another
vendor's rows. With no scope set, the policies deny everything.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from sqlalchemy import MetaData, create_engine, event, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

SCOPES = ("public", "customer", "vendor", "platform")


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def utcnow() -> datetime:
    return datetime.now(UTC)


engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

_owner_engine: Engine | None = None


def owner_engine() -> Engine:
    global _owner_engine
    if _owner_engine is None:
        _owner_engine = create_engine(settings.owner_database_url, pool_pre_ping=True)
    return _owner_engine


_SET_SCOPE = text(
    "SELECT set_config('app.scope', :scope, true),"
    " set_config('app.user_id', :user_id, true),"
    " set_config('app.vendor_id', :vendor_id, true)"
)


def _apply_scope(connection: Connection, values: dict[str, str]) -> None:
    connection.execute(_SET_SCOPE, values)


@event.listens_for(Session, "after_begin")
def _scope_on_begin(session: Session, transaction, connection: Connection) -> None:
    values = session.info.get("scope")
    if values:
        _apply_scope(connection, values)


def set_scope(
    db: Session, scope: str, *, user_id: str | None = None, vendor_id: str | None = None
) -> None:
    if scope not in SCOPES:
        raise ValueError(f"unknown scope {scope}")
    values = {"scope": scope, "user_id": user_id or "", "vendor_id": vendor_id or ""}
    db.info["scope"] = values
    if db.in_transaction():
        _apply_scope(db.connection(), values)


def current_scope(db: Session) -> dict[str, str]:
    return dict(db.info.get("scope") or {})


@contextmanager
def system_scope(db: Session) -> Iterator[None]:
    """Run a block as the platform (checkout orchestration, derived state, ledger).

    Pending changes are flushed before the scope is restored, so row-level
    security checks them under the platform scope.
    """
    previous = current_scope(db)
    set_scope(db, "platform", user_id=previous.get("user_id"))
    try:
        yield
        db.flush()
    finally:
        if previous:
            set_scope(
                db,
                previous["scope"],
                user_id=previous.get("user_id"),
                vendor_id=previous.get("vendor_id"),
            )


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
