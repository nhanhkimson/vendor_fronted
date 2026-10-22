from fastapi import APIRouter, Depends

from app.core.deps import Ctx, audit_meta, require
from app.schemas.orders import ConversationOut, NewConversationIn, ReplyIn
from app.services import messages

router = APIRouter(tags=["Notifications & Messages"])


@router.get("/api/account/messages", response_model=list[ConversationOut], summary="My conversations with shops")
def my_conversations(ctx: Ctx = Depends(require("message:read", "customer"))):
    return messages.list_conversations(ctx)


@router.post(
    "/api/account/messages",
    response_model=ConversationOut,
    status_code=201,
    summary="Message a shop (optionally about one of my orders)",
    openapi_extra=audit_meta("order", "start_conversation"),
)
def start_conversation(body: NewConversationIn, ctx: Ctx = Depends(require("message:create", "customer"))):
    return messages.start(ctx, body.vendor_id, body.order_id, body.subject, body.body)


@router.get("/api/account/messages/{conversation_id}", response_model=ConversationOut, summary="One of my conversations")
def my_conversation(conversation_id: str, ctx: Ctx = Depends(require("message:read", "customer"))):
    return messages.conversation_out(ctx.db, messages.get(ctx, conversation_id))


@router.post(
    "/api/account/messages/{conversation_id}/reply",
    response_model=ConversationOut,
    summary="Reply to a shop",
    openapi_extra=audit_meta("order", "reply_message"),
)
def customer_reply(conversation_id: str, body: ReplyIn, ctx: Ctx = Depends(require("message:create", "customer"))):
    return messages.reply(ctx, conversation_id, body.body)


@router.get("/api/seller/messages", response_model=list[ConversationOut], summary="Buyer conversations for my shop")
def seller_conversations(waiting: bool = False, ctx: Ctx = Depends(require("message:read", "vendor"))):
    return messages.list_conversations(ctx, waiting_only=waiting)


@router.get("/api/seller/messages/{conversation_id}", response_model=ConversationOut, summary="One buyer conversation")
def seller_conversation(conversation_id: str, ctx: Ctx = Depends(require("message:read", "vendor"))):
    return messages.conversation_out(ctx.db, messages.get(ctx, conversation_id))


@router.post(
    "/api/seller/messages/{conversation_id}/reply",
    response_model=ConversationOut,
    summary="Reply to a buyer",
    openapi_extra=audit_meta("order", "reply_message"),
)
def seller_reply(conversation_id: str, body: ReplyIn, ctx: Ctx = Depends(require("message:create", "vendor"))):
    return messages.reply(ctx, conversation_id, body.body)


@router.get("/api/messages", response_model=list[ConversationOut], summary="All buyer-shop conversations (read only)")
def all_conversations(ctx: Ctx = Depends(require("message:read"))):
    return messages.list_conversations(ctx)


@router.get("/api/messages/{conversation_id}", response_model=ConversationOut, summary="One conversation (read only)")
def any_conversation(conversation_id: str, ctx: Ctx = Depends(require("message:read"))):
    return messages.conversation_out(ctx.db, messages.get(ctx, conversation_id))
