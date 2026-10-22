from datetime import date, datetime
from typing import Literal

from app.schemas.common import Schema


class ReportTotals(Schema):
    orders: int
    sub_orders: int
    gmv_cents: int
    refunded_cents: int
    commission_cents: int
    net_cents: int
    aov_cents: int


class SalesRow(Schema):
    vendor_id: str
    vendor_name: str
    orders: int
    gmv_cents: int
    refunded_cents: int
    commission_cents: int
    net_cents: int


class RevenuePoint(Schema):
    date: str
    gmv_cents: int
    orders: int
    commission_cents: int


class ProductRank(Schema):
    product_id: str
    title: str
    vendor_id: str
    vendor_name: str
    units: int
    revenue_cents: int


class SourceRow(Schema):
    source: str
    orders: int = 0
    gmv_cents: int = 0
    customers: int = 0


class CommissionTotal(Schema):
    rule_target: str
    lines: int
    base_cents: int
    fee_cents: int


class OverviewOut(Schema):
    vendor_id: str | None
    date_from: date | None
    date_to: date | None
    generated_at: datetime
    totals: ReportTotals
    sales_by_vendor: list[SalesRow]
    revenue: list[RevenuePoint]
    top_products: list[ProductRank]
    sources: list[SourceRow]
    acquisition: list[SourceRow]
    commission: list[CommissionTotal]


class SummaryOut(Schema):
    area: Literal["customer", "vendor", "platform"]
    orders: int = 0
    open_orders: int = 0
    wishlist: int = 0
    unread: int = 0
    open_disputes: int = 0
    low_stock: int = 0
    waiting_messages: int = 0
    available_cents: int = 0
    eligible_payouts: int = 0
    vendors_to_review: int = 0
    payouts_to_sign: int = 0
    flagged_reviews: int = 0
