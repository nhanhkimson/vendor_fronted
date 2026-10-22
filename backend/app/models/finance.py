from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, utcnow


class CommissionRule(Base):
    """Effective-dated rate. Editing a rule end-dates it and inserts a new version."""

    __tablename__ = "commission_rules"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    # platform, tier, category, vendor
    target_type: Mapped[str] = mapped_column(String(20), index=True)
    target_id: Mapped[str] = mapped_column(String(40))
    rate_bps: Mapped[int] = mapped_column(Integer)
    min_fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    applies_to: Mapped[str] = mapped_column(String(20), default="item")
    version: Mapped[int] = mapped_column(Integer, default=1)
    supersedes_id: Mapped[str | None] = mapped_column(ForeignKey("commission_rules.id"))
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        CheckConstraint("rate_bps >= 0 AND rate_bps <= 5000", name="rate_bps_range"),
        CheckConstraint("min_fee_cents >= 0", name="min_fee_non_negative"),
    )


class CommissionLine(Base):
    """Frozen commission for one order line. Never updated (UPDATE is revoked)."""

    __tablename__ = "commission_lines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_line_id: Mapped[int] = mapped_column(ForeignKey("order_lines.id"), unique=True)
    sub_order_id: Mapped[str] = mapped_column(ForeignKey("sub_orders.id"), index=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("commission_rules.id"))
    rule_version: Mapped[int] = mapped_column(Integer)
    rule_target: Mapped[str] = mapped_column(String(70))
    rate_bps: Mapped[int] = mapped_column(Integer)
    min_fee_cents: Mapped[int] = mapped_column(Integer)
    base_cents: Mapped[int] = mapped_column(Integer)
    fee_cents: Mapped[int] = mapped_column(Integer)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class LedgerEntry(Base):
    """Double-entry ledger. Every journal balances: sum(debit) == sum(credit)."""

    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    journal_id: Mapped[str] = mapped_column(String(60), index=True)
    # cash, vendor_payable, platform_revenue, platform_promotions
    account: Mapped[str] = mapped_column(String(40), index=True)
    vendor_id: Mapped[str | None] = mapped_column(ForeignKey("vendors.id"), index=True)
    debit_cents: Mapped[int] = mapped_column(Integer, default=0)
    credit_cents: Mapped[int] = mapped_column(Integer, default=0)
    order_id: Mapped[str | None] = mapped_column(String(40), index=True)
    sub_order_id: Mapped[str | None] = mapped_column(String(60))
    payout_id: Mapped[str | None] = mapped_column(String(40))
    memo: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    __table_args__ = (
        CheckConstraint(
            "debit_cents >= 0 AND credit_cents >= 0 AND (debit_cents = 0) <> (credit_cents = 0)",
            name="one_sided_entry",
        ),
    )


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    # eligible, requested, pending_second_approval, approved, paid, held_for_dispute
    status: Mapped[str] = mapped_column(String(30), index=True)
    held_from_status: Mapped[str | None] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(String(255), default="")
    reference: Mapped[str | None] = mapped_column(String(60))
    requested_by: Mapped[str | None] = mapped_column(String(40))
    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    approvals: Mapped[list["PayoutApproval"]] = relationship(
        lazy="selectin", order_by="PayoutApproval.at"
    )
    items: Mapped[list["PayoutItem"]] = relationship(lazy="selectin", order_by="PayoutItem.id")
    events: Mapped[list["PayoutEvent"]] = relationship(lazy="selectin", order_by="PayoutEvent.id")

    __table_args__ = (CheckConstraint("amount_cents > 0", name="payout_positive"),)


class PayoutItem(Base):
    __tablename__ = "payout_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    payout_id: Mapped[str] = mapped_column(ForeignKey("payouts.id"), index=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"))
    # A sub-order can be paid out once.
    sub_order_id: Mapped[str] = mapped_column(ForeignKey("sub_orders.id"), unique=True)
    amount_cents: Mapped[int] = mapped_column(Integer)


class PayoutApproval(Base):
    __tablename__ = "payout_approvals"

    payout_id: Mapped[str] = mapped_column(ForeignKey("payouts.id"), primary_key=True)
    approver_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    approver_name: Mapped[str] = mapped_column(String(120))
    approver_roles: Mapped[list[str]] = mapped_column(JSONB, default=list)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PayoutEvent(Base):
    __tablename__ = "payout_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    payout_id: Mapped[str] = mapped_column(ForeignKey("payouts.id"), index=True)
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[str | None] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(String(255))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Coupon(Base):
    __tablename__ = "coupons"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    # platform: the platform absorbs the discount; vendor: the vendor funds it.
    funded_by: Mapped[str] = mapped_column(String(20))
    # Optional scope: only this vendor's items are discounted. Required for vendor-funded.
    vendor_id: Mapped[str | None] = mapped_column(ForeignKey("vendors.id"), index=True)
    # percent or fixed
    discount_type: Mapped[str] = mapped_column(String(10), default="percent")
    percent_off: Mapped[int | None] = mapped_column(Integer)
    amount_off_cents: Mapped[int | None] = mapped_column(Integer)
    min_subtotal_cents: Mapped[int] = mapped_column(Integer, default=0)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usage_limit: Mapped[int | None] = mapped_column(Integer)
    per_customer_limit: Mapped[int] = mapped_column(Integer, default=1)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    is_flash: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str] = mapped_column(String(255), default="")
    created_by: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        CheckConstraint("funded_by IN ('platform', 'vendor')", name="coupon_funder"),
        CheckConstraint(
            "funded_by = 'platform' OR vendor_id IS NOT NULL", name="vendor_coupon_has_vendor"
        ),
        CheckConstraint(
            "(discount_type = 'percent' AND percent_off BETWEEN 1 AND 90)"
            " OR (discount_type = 'fixed' AND amount_off_cents > 0)",
            name="coupon_value",
        ),
        CheckConstraint("ends_at > starts_at", name="coupon_window"),
    )


class CouponRedemption(Base):
    __tablename__ = "coupon_redemptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    coupon_code: Mapped[str] = mapped_column(ForeignKey("coupons.code"), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"))
    discount_cents: Mapped[int] = mapped_column(Integer)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("coupon_code", "customer_id", "order_id", name="uq_redemption"),
    )
