from datetime import datetime

from pydantic import Field

from app.schemas.common import Schema

DISPUTE_REASONS = "^(shipping_delay|not_as_described|damaged|never_arrived|other)$"


class CartLineOut(Schema):
    id: int
    variant_id: str
    product_id: str
    title: str
    image_url: str | None
    vendor_id: str
    vendor_name: str
    sku: str
    size: str
    color: str
    unit_price_cents: int
    qty: int
    line_total_cents: int
    available: int
    vendor_discount_cents: int
    platform_discount_cents: int
    problem: str | None = None


class CartGroupOut(Schema):
    vendor_id: str
    vendor_name: str
    vendor_slug: str
    shipping_cents: int
    items_subtotal_cents: int
    vendor_discount_cents: int
    platform_discount_cents: int
    charged_cents: int
    lines: list[CartLineOut]


class CartOut(Schema):
    item_count: int
    groups: list[CartGroupOut]
    coupon_code: str | None
    coupon_applied: bool
    coupon_message: str | None
    items_subtotal_cents: int
    shipping_cents: int
    vendor_discount_cents: int
    platform_discount_cents: int
    discount_cents: int
    total_cents: int
    problems: list[str]
    can_checkout: bool
    notes: list[str] = []


class CartItemIn(Schema):
    variant_id: str
    qty: int = Field(default=1, ge=1, le=10)


class CartQtyIn(Schema):
    qty: int = Field(ge=0, le=10, description="0 removes the line")


class CartMergeIn(Schema):
    items: list[CartItemIn] = Field(default_factory=list, max_length=50)


class CouponIn(Schema):
    code: str = Field(min_length=2, max_length=40)


class CheckoutIn(Schema):
    ship_name: str = Field(min_length=2, max_length=120)
    ship_address: str = Field(min_length=5, max_length=255)


class IntentGroup(Schema):
    vendor_id: str
    vendor_name: str
    charged_cents: int
    items: int


class PaymentIntentOut(Schema):
    id: str
    status: str
    amount_cents: int
    currency: str
    coupon_code: str | None
    discount_cents: int
    shipping_cents: int
    expires_at: datetime
    order_id: str | None
    failure_reason: str | None
    groups: list[IntentGroup]
    test_cards: dict[str, str]


class ConfirmIn(Schema):
    card_number: str = Field(min_length=12, max_length=23, description="4242 4242 4242 4242 succeeds; 4000 0000 0000 0002 is declined")
    card_name: str | None = Field(default=None, max_length=120)
    expiry: str | None = Field(default=None, max_length=7, description="MM/YY")
    cvc: str | None = Field(default=None, max_length=4)


class OrderLineOut(Schema):
    id: int
    product_id: str
    variant_id: str
    title: str
    sku: str
    size: str
    color: str
    image_url: str | None
    unit_price_cents: int
    qty: int
    line_total_cents: int
    vendor_discount_cents: int
    platform_discount_cents: int
    commission_cents: int | None = None
    commission_rate_bps: int | None = None
    review_id: str | None = None
    can_review: bool = False


class EventOut(Schema):
    from_status: str | None
    to_status: str
    actor_role: str | None
    note: str | None
    at: datetime


class DisputeOut(Schema):
    id: str
    order_id: str
    sub_order_id: str
    buyer_id: str
    buyer_name: str
    vendor_id: str
    vendor_name: str
    reason: str
    note: str
    status: str
    resolution_note: str | None
    resolved_by: str | None
    resolved_at: datetime | None
    created_at: datetime
    charged_cents: int
    held_payouts: list[str] = []


class SubOrderOut(Schema):
    id: str
    order_id: str
    vendor_id: str
    vendor_name: str
    vendor_slug: str
    buyer_id: str
    buyer_name: str
    ship_name: str
    ship_address: str
    status: str
    items_subtotal_cents: int
    shipping_cents: int
    vendor_discount_cents: int
    platform_discount_cents: int
    charged_cents: int
    commission_cents: int | None
    vendor_net_cents: int | None
    refunded_cents: int
    tracking_number: str | None
    carrier: str | None
    in_dispute: bool
    accepted_at: datetime | None
    shipped_at: datetime | None
    delivered_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    placed_at: datetime
    lines: list[OrderLineOut]
    events: list[EventOut]
    dispute: DisputeOut | None = None
    allowed_actions: list[str]
    next_step: str | None = None


class OrderOut(Schema):
    id: str
    status: str
    buyer_id: str
    buyer_name: str
    placed_at: datetime
    completed_at: datetime | None
    items_subtotal_cents: int
    shipping_cents: int
    discount_cents: int
    platform_discount_cents: int
    vendor_discount_cents: int
    total_cents: int
    refunded_cents: int
    coupon_code: str | None
    source: str
    ship_name: str
    ship_address: str
    card_last4: str | None
    sub_orders: list[SubOrderOut]


class ShipIn(Schema):
    carrier: str | None = Field(default=None, max_length=60)
    tracking_number: str | None = Field(default=None, max_length=60)


class CancelIn(Schema):
    reason: str = Field(min_length=3, max_length=255)


class StaffStatusIn(Schema):
    status: str = Field(pattern="^(accepted|packing|shipped|delivered)$")
    note: str = Field(min_length=3, max_length=255)
    tracking_number: str | None = Field(default=None, max_length=60)
    carrier: str | None = Field(default=None, max_length=60)


class DisputeIn(Schema):
    reason: str = Field(pattern=DISPUTE_REASONS)
    note: str = Field(min_length=3, max_length=1000)


class ResolveIn(Schema):
    outcome: str = Field(pattern="^(refund|reject)$")
    note: str = Field(min_length=3, max_length=500)


class MessageOut(Schema):
    id: str
    sender_id: str
    sender_name: str
    sender_role: str
    body: str
    at: datetime


class ConversationOut(Schema):
    id: str
    buyer_id: str
    buyer_name: str
    vendor_id: str
    vendor_name: str
    order_id: str | None
    subject: str
    last_message_at: datetime
    last_sender_role: str
    message_count: int
    awaiting_reply_from: str
    messages: list[MessageOut]


class NewConversationIn(Schema):
    vendor_id: str
    order_id: str | None = None
    subject: str = Field(min_length=3, max_length=160)
    body: str = Field(min_length=1, max_length=2000)


class ReplyIn(Schema):
    body: str = Field(min_length=1, max_length=2000)
