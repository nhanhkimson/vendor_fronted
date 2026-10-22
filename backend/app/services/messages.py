"""Buyer-shop conversations. Staff can read every thread and reply as Bazaar support."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import utcnow
from app.core.deps import Ctx
from app.core.errors import NotFound
from app.core.util import new_id
from app.models import Conversation, ConversationMessage, Order, User, Vendor
from app.services.events import Notice, emit, vendor_staff_ids
from app.services.tenancy import not_found


def conversation_out(db: Session, conversation: Conversation, with_messages: bool = True) -> dict:
    buyer = db.get(User, conversation.buyer_id)
    vendor = db.get(Vendor, conversation.vendor_id)
    waiting = {"customer": "vendor", "vendor": "customer", "staff": "customer"}.get(conversation.last_sender_role)
    return {
        "id": conversation.id,
        "buyer_id": conversation.buyer_id,
        "buyer_name": buyer.name if buyer else conversation.buyer_id,
        "vendor_id": conversation.vendor_id,
        "vendor_name": vendor.name if vendor else conversation.vendor_id,
        "order_id": conversation.order_id,
        "subject": conversation.subject,
        "last_message_at": conversation.last_message_at,
        "last_sender_role": conversation.last_sender_role,
        "message_count": conversation.message_count,
        "awaiting_reply_from": waiting,
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "sender_name": m.sender_name,
                "sender_role": m.sender_role,
                "body": m.body,
                "at": m.at,
            }
            for m in conversation.messages
        ]
        if with_messages
        else [],
    }


def _scoped(ctx: Ctx):
    query = select(Conversation).order_by(Conversation.last_message_at.desc())
    if ctx.scope == "vendor":
        query = query.where(Conversation.vendor_id == ctx.vendor_id)
    elif ctx.scope == "customer":
        query = query.where(Conversation.buyer_id == ctx.user_id)
    return query


def list_conversations(ctx: Ctx, waiting_only: bool = False) -> list[dict]:
    rows = [conversation_out(ctx.db, c) for c in ctx.db.scalars(_scoped(ctx)).all()]
    if waiting_only:
        mine = {"vendor": "vendor", "customer": "customer"}.get(ctx.scope, "vendor")
        rows = [r for r in rows if r["awaiting_reply_from"] == mine]
    return rows


def get(ctx: Ctx, conversation_id: str) -> Conversation:
    conversation = ctx.db.get(Conversation, conversation_id)
    visible = conversation is not None and (
        ctx.scope == "platform"
        or (ctx.scope == "vendor" and conversation.vendor_id == ctx.vendor_id)
        or (ctx.scope == "customer" and conversation.buyer_id == ctx.user_id)
    )
    if not visible:
        raise not_found(ctx, Conversation, conversation_id, "Conversation", "order", "conversation")
    return conversation


def _add(db: Session, conversation: Conversation, sender: User, role: str, body: str) -> ConversationMessage:
    now = utcnow()
    message = ConversationMessage(
        id=new_id("M", 10),
        conversation_id=conversation.id,
        buyer_id=conversation.buyer_id,
        vendor_id=conversation.vendor_id,
        sender_id=sender.id,
        sender_name=sender.name,
        sender_role=role,
        body=body.strip(),
        at=now,
    )
    db.add(message)
    conversation.last_message_at = now
    conversation.last_sender_role = role
    conversation.message_count = (conversation.message_count or 0) + 1
    return message


def start(ctx: Ctx, vendor_id: str, order_id: str | None, subject: str, body: str) -> dict:
    db = ctx.db
    vendor = db.get(Vendor, vendor_id)
    if vendor is None or vendor.deleted_at is not None:
        raise NotFound("Shop", vendor_id)
    if order_id:
        order = db.get(Order, order_id)
        sells = order is not None and order.buyer_id == ctx.user_id and any(s.vendor_id == vendor_id for s in order.sub_orders)
        if not sells:
            raise NotFound("Order", order_id)
    conversation = Conversation(
        id=new_id("C", 8),
        buyer_id=ctx.user_id,
        vendor_id=vendor_id,
        order_id=order_id,
        subject=subject.strip(),
        created_at=utcnow(),
        message_count=0,
    )
    db.add(conversation)
    db.flush()
    _add(db, conversation, ctx.user, "customer", body)
    ctx.audit("order", "start_conversation", "conversation", conversation.id, after={"vendor_id": vendor_id, "order_id": order_id, "subject": subject})
    emit(
        db,
        "message.sent",
        {"conversation_id": conversation.id},
        [Notice(uid, f"New message from {ctx.user.name}: {subject}", "/seller/messages") for uid in vendor_staff_ids(db, vendor_id)],
    )
    ctx.commit()
    db.refresh(conversation)
    return conversation_out(db, conversation)


def reply(ctx: Ctx, conversation_id: str, body: str) -> dict:
    """Customer or vendor reply. Staff can read threads but do not post in them."""
    db = ctx.db
    conversation = get(ctx, conversation_id)
    role = "vendor" if ctx.scope == "vendor" else "customer"
    _add(db, conversation, ctx.user, role, body)
    ctx.audit("order", "reply_message", "conversation", conversation.id, after={"sender_role": role, "length": len(body.strip())})
    if role == "customer":
        notices = [Notice(uid, f"{ctx.user.name} replied: {conversation.subject}", "/seller/messages") for uid in vendor_staff_ids(db, conversation.vendor_id)]
    else:
        vendor = db.get(Vendor, conversation.vendor_id)
        notices = [Notice(conversation.buyer_id, f"{vendor.name} replied: {conversation.subject}", "/account/messages")]
    emit(db, "message.sent", {"conversation_id": conversation.id}, notices)
    ctx.commit()
    db.refresh(conversation)
    return conversation_out(db, conversation)
