"""Domain events (research section 6.6) and the in-app notification inbox.

Events are written to the outbox in the same transaction as the change and
dispatched to notifications immediately, so a rolled-back change never sends
a notification.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import system_scope, utcnow
from app.core.util import new_id, to_json
from app.models.identity import Role, User, UserRole
from app.models.system import Notification, OutboxEvent


@dataclass
class Notice:
    user_id: str
    title: str
    link: str | None = None
    body: str | None = None


def emit(db: Session, event_type: str, payload: dict[str, Any], notices: Iterable[Notice] = ()) -> None:
    now = utcnow()
    with system_scope(db):
        db.add(
            OutboxEvent(
                id=new_id("EV", 10),
                event_type=event_type,
                payload=to_json(payload),
                created_at=now,
                processed_at=now,
            )
        )
        seen: set[tuple[str, str]] = set()
        for notice in notices:
            if not notice.user_id or (notice.user_id, notice.title) in seen:
                continue
            seen.add((notice.user_id, notice.title))
            db.add(
                Notification(
                    id=new_id("N", 10),
                    user_id=notice.user_id,
                    kind=event_type,
                    title=notice.title,
                    body=notice.body,
                    link=notice.link,
                    created_at=now,
                )
            )


def vendor_staff_ids(db: Session, vendor_id: str) -> list[str]:
    rows = db.scalars(
        select(User.id)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(User.vendor_id == vendor_id, User.is_active.is_(True), Role.kind == "vendor")
    ).all()
    return sorted(set(rows))


def users_with_permission(db: Session, key: str) -> list[str]:
    from app.core.deps import effective_permissions

    roles = db.scalars(select(Role)).all()
    role_ids = [r.id for r in roles if key in effective_permissions([r])]
    if not role_ids:
        return []
    rows = db.scalars(
        select(UserRole.user_id)
        .join(User, User.id == UserRole.user_id)
        .where(UserRole.role_id.in_(role_ids), User.is_active.is_(True), User.vendor_id.is_(None))
    ).all()
    return sorted(set(rows))
