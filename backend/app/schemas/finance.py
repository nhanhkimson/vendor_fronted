from datetime import date, datetime

from pydantic import Field

from app.schemas.common import Cents, Schema

TARGET_TYPES = "^(platform|tier|category|vendor)$"


class RuleIn(Schema):
    name: str = Field(min_length=2, max_length=120)
    target_type: str = Field(pattern=TARGET_TYPES)
    target_id: str = Field(min_length=1, max_length=40, description="`*` for the platform default, otherwise a tier, category or vendor id")
    rate_bps: int = Field(ge=0, le=5000, description="Basis points. 1500 = 15%.")
    min_fee_cents: Cents = 0


class RuleReviseIn(Schema):
    rate_bps: int = Field(ge=0, le=5000)
    min_fee_cents: Cents = 0
    name: str | None = Field(default=None, min_length=2, max_length=120)


class RuleOut(Schema):
    id: str
    name: str
    target_type: str
    target_id: str
    target_label: str
    rate_bps: int
    min_fee_cents: int
    version: int
    supersedes_id: str | None
    replaced_by: str | None = None
    effective_from: datetime
    effective_to: datetime | None
    open: bool
    created_by: str | None
    created_at: datetime


class CommissionLineOut(Schema):
    id: int
    order_line_id: int
    sub_order_id: str
    order_id: str
    vendor_id: str
    vendor_name: str
    rule_id: str
    rule_version: int
    rule_target: str
    rate_bps: int
    min_fee_cents: int
    base_cents: int
    fee_cents: int
    computed_at: datetime


class LedgerEntryOut(Schema):
    id: int
    journal_id: str
    account: str
    vendor_id: str | None
    debit_cents: int
    credit_cents: int
    order_id: str | None
    sub_order_id: str | None
    payout_id: str | None
    memo: str
    created_at: datetime


class TrialRow(Schema):
    account: str
    debit_cents: int
    credit_cents: int
    balance_cents: int


class TrialBalanceOut(Schema):
    rows: list[TrialRow]
    balanced: bool


class PayoutApprovalOut(Schema):
    approver_id: str
    approver_name: str
    approver_roles: list[str]
    at: datetime


class PayoutItemOut(Schema):
    sub_order_id: str
    amount_cents: int


class PayoutEventOut(Schema):
    from_status: str | None
    to_status: str
    actor_id: str | None
    note: str | None
    at: datetime


class PayoutOut(Schema):
    id: str
    vendor_id: str
    vendor_name: str
    amount_cents: int
    status: str
    held_from_status: str | None
    note: str
    reference: str | None
    requested_by: str | None
    requested_by_name: str | None
    requested_at: datetime | None
    approved_at: datetime | None
    paid_at: datetime | None
    created_at: datetime
    approvals: list[PayoutApprovalOut]
    items: list[PayoutItemOut]
    events: list[PayoutEventOut]
    allowed_actions: list[str]


class PayIn(Schema):
    reference: str = Field(
        min_length=3,
        max_length=60,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{2,59}$",
        description="Bank transfer reference, e.g. TRF-1008",
        examples=["TRF-1008"],
    )
    note: str | None = Field(default=None, max_length=255)


class PayableOrder(Schema):
    sub_order_id: str
    order_id: str
    delivered_at: datetime | None
    vendor_net_cents: int


class StatementLine(Schema):
    sub_order_id: str
    order_id: str
    placed_at: datetime
    status: str
    items_cents: int
    shipping_cents: int
    vendor_discount_cents: int
    platform_discount_cents: int
    charged_cents: int
    commission_cents: int
    net_cents: int
    refunded_cents: int


class StatementOut(Schema):
    date_from: date | None
    date_to: date | None
    orders: int
    items_cents: int
    shipping_cents: int
    vendor_discount_cents: int
    platform_discount_cents: int
    charged_cents: int
    commission_cents: int
    refunded_cents: int
    net_cents: int
    lines: list[StatementLine]


class EarningsOut(Schema):
    vendor_id: str
    vendor_name: str
    holdback_days: int
    balance_cents: int
    available_cents: int
    matured_cents: int
    held_back_cents: int
    in_dispute_cents: int
    reserved_cents: int
    open_dispute: bool
    next_payable_at: datetime | None
    payable_orders: list[PayableOrder]
    payouts: list[PayoutOut]
    statement: StatementOut


class CouponIn(Schema):
    code: str = Field(min_length=2, max_length=40, examples=["SPRING15"])
    funded_by: str = Field(default="platform", pattern="^(platform|vendor)$")
    vendor_id: str | None = Field(default=None, description="Required when the vendor funds the discount. Optional scope for a platform coupon.")
    discount_type: str = Field(default="percent", pattern="^(percent|fixed)$")
    percent_off: int | None = Field(default=None, ge=1, le=90)
    amount_off_cents: int | None = Field(default=None, ge=1)
    min_subtotal_cents: Cents = 0
    starts_at: datetime
    ends_at: datetime
    usage_limit: int | None = Field(default=None, ge=1)
    per_customer_limit: int = Field(default=1, ge=1, le=100)
    is_flash: bool = False
    note: str = Field(default="", max_length=255)


class CouponUpdate(Schema):
    discount_type: str | None = Field(default=None, pattern="^(percent|fixed)$")
    percent_off: int | None = Field(default=None, ge=1, le=90)
    amount_off_cents: int | None = Field(default=None, ge=1)
    min_subtotal_cents: Cents | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    usage_limit: int | None = Field(default=None, ge=1)
    per_customer_limit: int | None = Field(default=None, ge=1, le=100)
    is_flash: bool | None = None
    active: bool | None = None
    note: str | None = Field(default=None, max_length=255)
    vendor_id: str | None = None


class CouponOut(Schema):
    code: str
    funded_by: str
    vendor_id: str | None
    vendor_name: str | None
    discount_type: str
    percent_off: int | None
    amount_off_cents: int | None
    min_subtotal_cents: int
    starts_at: datetime
    ends_at: datetime
    usage_limit: int | None
    per_customer_limit: int
    used_count: int
    is_flash: bool
    active: bool
    note: str
    summary: str
    editable: bool
    created_at: datetime
