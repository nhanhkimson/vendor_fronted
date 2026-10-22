from fastapi import APIRouter, Depends
from sqlalchemy import func, select, update

from app.core.db import utcnow
from app.core.deps import Ctx, audit_meta, authenticated
from app.core.errors import NotFound
from app.models.system import Notification
from app.schemas.common import Message
from app.schemas.identity import NotificationList

router = APIRouter(prefix="/api/notifications", tags=["Notifications & Messages"])


@router.get("", response_model=NotificationList, summary="My notifications (newest first)")
def my_notifications(ctx: Ctx = Depends(authenticated())):
    items = ctx.db.scalars(
        select(Notification)
        .where(Notification.user_id == ctx.user_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    ).all()
    unread = ctx.db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == ctx.user_id, Notification.read_at.is_(None))
    )
    return {"items": items, "unread": unread or 0}


@router.post(
    "/{notification_id}/read",
    response_model=Message,
    summary="Mark one notification read",
    openapi_extra=audit_meta("notification", "read"),
)
def mark_read(notification_id: str, ctx: Ctx = Depends(authenticated())):
    note = ctx.db.get(Notification, notification_id)
    if note is None or note.user_id != ctx.user_id:
        raise NotFound("Notification", notification_id)
    note.read_at = note.read_at or utcnow()
    ctx.audit("notification", "read", "notification", notification_id)
    ctx.commit()
    return Message(detail="Marked read")


@router.post(
    "/read-all",
    response_model=Message,
    summary="Mark all my notifications read",
    openapi_extra=audit_meta("notification", "read_all"),
)
def mark_all_read(ctx: Ctx = Depends(authenticated())):
    result = ctx.db.execute(
        update(Notification)
        .where(Notification.user_id == ctx.user_id, Notification.read_at.is_(None))
        .values(read_at=utcnow())
    )
    ctx.audit("notification", "read_all", "notification", None, after={"count": result.rowcount})
    ctx.commit()
    return Message(detail=f"Marked {result.rowcount} notifications read")
