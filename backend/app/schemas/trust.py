from datetime import datetime

from pydantic import Field

from app.schemas.catalogue import ProductCard
from app.schemas.common import Email, Schema

SOURCES = "^(organic|coupon|social|referral)$"


class CustomerCreate(Schema):
    name: str = Field(min_length=2, max_length=120)
    email: Email
    password: str = Field(min_length=8, max_length=200)
    city: str | None = Field(default=None, max_length=120)
    source: str = Field(default="organic", pattern=SOURCES)
    blurb: str | None = Field(default=None, max_length=255)


class CustomerUpdate(Schema):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    email: Email | None = None
    city: str | None = Field(default=None, max_length=120)
    source: str | None = Field(default=None, pattern=SOURCES)
    blurb: str | None = Field(default=None, max_length=255)


class CustomerOrder(Schema):
    id: str
    status: str
    total_cents: int
    placed_at: datetime


class CustomerOut(Schema):
    id: str
    email: str
    name: str
    city: str | None
    source: str
    blurb: str | None
    is_active: bool
    banned: bool
    ban_reason: str | None
    created_at: datetime
    last_login_at: datetime | None
    orders: int
    spent_cents: int
    reviews: int


class CustomerDetail(CustomerOut):
    recent_orders: list[CustomerOrder]


class ReviewIn(Schema):
    sub_order_id: str
    product_id: str
    rating: float = Field(ge=1, le=5, description="1 to 5, half stars allowed")
    body: str = Field(min_length=10, max_length=2000)


class ReviewReplyIn(Schema):
    response: str = Field(min_length=2, max_length=1000)


class ReviewOut(Schema):
    id: str
    product_id: str
    product_title: str
    vendor_id: str
    vendor_name: str
    buyer_id: str
    buyer_name: str
    rating: float | None
    body: str
    sentiment: str | None
    theme: str | None
    source: str
    status: str
    moderation_reason: str | None
    verified_purchase: bool
    sub_order_id: str | None
    vendor_response: str | None
    vendor_responded_at: datetime | None
    created_at: datetime
    allowed_actions: list[str] = []


class WishlistIn(Schema):
    product_id: str


class WishlistItemOut(Schema):
    product_id: str
    added_at: datetime
    product: ProductCard
