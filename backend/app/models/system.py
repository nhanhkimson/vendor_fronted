from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow


class _AuditColumns:
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(40), index=True)
    actor_name: Mapped[str] = mapped_column(String(120), default="Anonymous")
    actor_roles: Mapped[list[str]] = mapped_column(JSONB, default=list)
    actor_vendor_id: Mapped[str | None] = mapped_column(String(40))
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    module: Mapped[str] = mapped_column(String(30), index=True)
    action: Mapped[str] = mapped_column(String(60), index=True)
    resource_type: Mapped[str] = mapped_column(String(40))
    resource_id: Mapped[str | None] = mapped_column(String(80), index=True)
    before: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(40), index=True)
    # success, denied, failed
    outcome: Mapped[str] = mapped_column(String(20), default="success", index=True)
    reason: Mapped[str | None] = mapped_column(String(255))


class AuditLog(_AuditColumns, Base):
    """Append-only: the runtime role has INSERT and SELECT only."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class AuditLogArchive(_AuditColumns, Base):
    """Filled only by the archive_audit_logs() SECURITY DEFINER function."""

    __tablename__ = "audit_logs_archive"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str | None] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(String(255))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class OutboxEvent(Base):
    """Domain events written in the same transaction as the change that caused them."""

    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(60), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
