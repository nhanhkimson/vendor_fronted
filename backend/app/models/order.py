from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, utcnow


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    coupon_code: Mapped[str | None] = mapped_column(String(40))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    lines: Mapped[list["CartLine"]] = relationship(
        back_populates="cart", lazy="selectin", order_by="CartLine.id", cascade="all, delete-orphan"
    )


class CartLine(Base):
    __tablename__ = "cart_lines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cart_id: Mapped[str] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[str] = mapped_column(ForeignKey("variants.id", ondelete="CASCADE"))
    qty: Mapped[int] = mapped_column(Integer)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    cart: Mapped[Cart] = relationship(back_populates="lines")

    __table_args__ = (UniqueConstraint("cart_id", "variant_id", name="uq_cart_variant"),)


class PaymentIntent(Base):
    """Simulated card payment. Holds the frozen quote and the stock reservations."""

    __tablename__ = "payment_intents"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    # requires_payment, succeeded, failed, expired
    status: Mapped[str] = mapped_column(String(20), default="requires_payment")
    amount_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    coupon_code: Mapped[str | None] = mapped_column(String(40))
    ship_name: Mapped[str] = mapped_column(String(120), default="")
    ship_address: Mapped[str] = mapped_column(String(255), default="")
    quote: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    order_id: Mapped[str | None] = mapped_column(String(40), unique=True)
    card_last4: Mapped[str | None] = mapped_column(String(4))
    failure_reason: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Order(Base):
    """Parent order: what the customer paid once. Fulfilment happens per sub-order."""

    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    payment_intent_id: Mapped[str | None] = mapped_column(
        ForeignKey("payment_intents.id"), unique=True
    )
    # paid, partially_fulfilled, fulfilled, completed, cancelled, partially_refunded, refunded
    status: Mapped[str] = mapped_column(String(30), default="paid", index=True)
    items_subtotal_cents: Mapped[int] = mapped_column(Integer, default=0)
    shipping_cents: Mapped[int] = mapped_column(Integer, default=0)
    discount_cents: Mapped[int] = mapped_column(Integer, default=0)
    platform_discount_cents: Mapped[int] = mapped_column(Integer, default=0)
    vendor_discount_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_cents: Mapped[int] = mapped_column(Integer, default=0)
    refunded_cents: Mapped[int] = mapped_column(Integer, default=0)
    coupon_code: Mapped[str | None] = mapped_column(String(40))
    source: Mapped[str] = mapped_column(String(30), default="organic")
    ship_name: Mapped[str] = mapped_column(String(120), default="")
    ship_address: Mapped[str] = mapped_column(String(255), default="")
    card_last4: Mapped[str | None] = mapped_column(String(4))
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sub_orders: Mapped[list["SubOrder"]] = relationship(
        back_populates="order", lazy="selectin", order_by="SubOrder.id"
    )


class SubOrder(Base):
    """The part of an order that one vendor fulfils. Money is split here."""

    __tablename__ = "sub_orders"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    # pending_acceptance, accepted, packing, shipped, delivered, cancelled, refunded
    status: Mapped[str] = mapped_column(String(30), default="pending_acceptance", index=True)
    items_subtotal_cents: Mapped[int] = mapped_column(Integer, default=0)
    shipping_cents: Mapped[int] = mapped_column(Integer, default=0)
    vendor_discount_cents: Mapped[int] = mapped_column(Integer, default=0)
    platform_discount_cents: Mapped[int] = mapped_column(Integer, default=0)
    charged_cents: Mapped[int] = mapped_column(Integer, default=0)
    commission_cents: Mapped[int] = mapped_column(Integer, default=0)
    vendor_net_cents: Mapped[int] = mapped_column(Integer, default=0)
    refunded_cents: Mapped[int] = mapped_column(Integer, default=0)
    tracking_number: Mapped[str | None] = mapped_column(String(60))
    carrier: Mapped[str | None] = mapped_column(String(60))
    warehouse_id: Mapped[str | None] = mapped_column(ForeignKey("warehouses.id"))
    in_dispute: Mapped[bool] = mapped_column(Boolean, default=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    order: Mapped[Order] = relationship(back_populates="sub_orders")
    lines: Mapped[list["OrderLine"]] = relationship(
        back_populates="sub_order", lazy="selectin", order_by="OrderLine.id"
    )
    events: Mapped[list["SubOrderEvent"]] = relationship(
        lazy="selectin", order_by="SubOrderEvent.id"
    )


class OrderLine(Base):
    """Snapshot of what was bought. Titles and prices never change after checkout."""

    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sub_order_id: Mapped[str] = mapped_column(ForeignKey("sub_orders.id"), index=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    buyer_id: Mapped[str] = mapped_column(String(40), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    variant_id: Mapped[str] = mapped_column(ForeignKey("variants.id"))
    category_id: Mapped[str | None] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(160))
    sku: Mapped[str] = mapped_column(String(60))
    size: Mapped[str] = mapped_column(String(40))
    color: Mapped[str] = mapped_column(String(40))
    image_url: Mapped[str | None] = mapped_column(String(255))
    unit_price_cents: Mapped[int] = mapped_column(Integer)
    qty: Mapped[int] = mapped_column(Integer)
    line_total_cents: Mapped[int] = mapped_column(Integer)
    vendor_discount_cents: Mapped[int] = mapped_column(Integer, default=0)
    platform_discount_cents: Mapped[int] = mapped_column(Integer, default=0)

    sub_order: Mapped[SubOrder] = relationship(back_populates="lines")


class SubOrderEvent(Base):
    __tablename__ = "sub_order_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sub_order_id: Mapped[str] = mapped_column(ForeignKey("sub_orders.id"), index=True)
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[str | None] = mapped_column(String(40))
    actor_role: Mapped[str | None] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(Text)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
