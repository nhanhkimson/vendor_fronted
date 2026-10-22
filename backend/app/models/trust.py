from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, utcnow


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    # Verified purchase link. Null only for reviews imported from the public sample.
    sub_order_id: Mapped[str | None] = mapped_column(ForeignKey("sub_orders.id"))
    rating: Mapped[float | None] = mapped_column(Numeric(2, 1))
    body: Mapped[str] = mapped_column(Text)
    sentiment: Mapped[str | None] = mapped_column(String(20))
    theme: Mapped[str | None] = mapped_column(String(40))
    # bazaar, ebay, etsy
    source: Mapped[str] = mapped_column(String(20), default="bazaar")
    # published, flagged, removed
    status: Mapped[str] = mapped_column(String(20), default="published", index=True)
    moderation_reason: Mapped[str | None] = mapped_column(String(255))
    vendor_response: Mapped[str | None] = mapped_column(Text)
    vendor_responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("buyer_id", "sub_order_id", "product_id", name="uq_review_per_purchase"),
    )


class ReviewEvent(Base):
    __tablename__ = "review_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), index=True)
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str | None] = mapped_column(String(40))
    reason: Mapped[str | None] = mapped_column(String(255))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    sub_order_id: Mapped[str] = mapped_column(ForeignKey("sub_orders.id"), index=True)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    # shipping_delay, not_as_described, damaged, never_arrived, other
    reason: Mapped[str] = mapped_column(String(40))
    note: Mapped[str] = mapped_column(Text, default="")
    # open, resolved_refund, resolved_rejected
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    resolution_note: Mapped[str | None] = mapped_column(Text)
    resolved_by: Mapped[str | None] = mapped_column(String(40))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id"))
    subject: Mapped[str] = mapped_column(String(160))
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_sender_role: Mapped[str] = mapped_column(String(20), default="customer")
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    messages: Mapped[list["ConversationMessage"]] = relationship(
        lazy="selectin", order_by="ConversationMessage.at"
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    buyer_id: Mapped[str] = mapped_column(String(40))
    vendor_id: Mapped[str] = mapped_column(String(40))
    sender_id: Mapped[str] = mapped_column(String(40))
    sender_name: Mapped[str] = mapped_column(String(120))
    # customer, vendor, staff
    sender_role: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
