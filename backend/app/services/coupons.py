"""M9 Coupons: eligibility rules shared by the cart, checkout and the admin screens."""

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.db import system_scope, utcnow
from app.core.util import money
from app.domain.pricing import CouponTerms
from app.models import Coupon, CouponRedemption, PaymentIntent, Vendor


def find(db: Session, code: str) -> Coupon | None:
    return db.scalar(select(Coupon).where(func.upper(Coupon.code) == code.strip().upper()))


def terms(db: Session, coupon: Coupon) -> CouponTerms:
    vendor = db.get(Vendor, coupon.vendor_id) if coupon.vendor_id else None
    return CouponTerms(
        code=coupon.code,
        funded_by=coupon.funded_by,
        vendor_id=coupon.vendor_id,
        discount_type=coupon.discount_type,
        percent_off=coupon.percent_off,
        amount_off_cents=coupon.amount_off_cents,
        min_subtotal_cents=coupon.min_subtotal_cents,
        vendor_name=vendor.name if vendor else None,
    )


def uses_by(db: Session, code: str, user_id: str, exclude_intent: str | None = None) -> int:
    """Redemptions plus checkouts still waiting for payment, so two tabs cannot double-spend."""
    redeemed = db.scalar(
        select(func.count()).select_from(CouponRedemption).where(
            CouponRedemption.coupon_code == code, CouponRedemption.customer_id == user_id
        )
    ) or 0
    pending_query = select(func.count()).select_from(PaymentIntent).where(
        PaymentIntent.coupon_code == code,
        PaymentIntent.user_id == user_id,
        PaymentIntent.status == "requires_payment",
    )
    if exclude_intent:
        pending_query = pending_query.where(PaymentIntent.id != exclude_intent)
    return int(redeemed) + int(db.scalar(pending_query) or 0)


def problem(db: Session, coupon: Coupon | None, user_id: str, now: datetime | None = None) -> str | None:
    now = now or utcnow()
    if coupon is None or not coupon.active:
        return "That code is not valid"
    if now < coupon.starts_at:
        return f"{coupon.code} starts on {coupon.starts_at:%d %b %Y}"
    if now >= coupon.ends_at:
        return f"{coupon.code} expired on {coupon.ends_at:%d %b %Y}"
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        return f"{coupon.code} has been fully used"
    if uses_by(db, coupon.code, user_id) >= coupon.per_customer_limit:
        times = "once" if coupon.per_customer_limit == 1 else f"{coupon.per_customer_limit} times"
        return f"You have already used {coupon.code} (limit: {times} per customer)"
    if coupon.vendor_id:
        vendor = db.get(Vendor, coupon.vendor_id)
        if vendor is None or vendor.status != "active":
            return f"{coupon.code} is not available right now"
    return None


def describe(coupon: Coupon) -> str:
    value = f"{coupon.percent_off}% off" if coupon.discount_type == "percent" else f"{money(coupon.amount_off_cents)} off"
    if coupon.min_subtotal_cents:
        value += f" orders over {money(coupon.min_subtotal_cents)}"
    return value


def take_use(db: Session, code: str) -> bool:
    """Atomically count one use against the total limit. False when the limit is already reached."""
    with system_scope(db):
        result = db.execute(
            update(Coupon)
            .where(
                Coupon.code == code,
                (Coupon.usage_limit.is_(None)) | (Coupon.used_count < Coupon.usage_limit),
            )
            .values(used_count=Coupon.used_count + 1)
            .returning(Coupon.code)
        ).first()
    return result is not None


def give_back_use(db: Session, code: str) -> None:
    with system_scope(db):
        db.execute(
            update(Coupon).where(Coupon.code == code, Coupon.used_count > 0).values(used_count=Coupon.used_count - 1)
        )
