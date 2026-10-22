"""M9 Coupons: eligibility rules shared by the cart, checkout and the admin screens."""

from datetime import datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.db import system_scope, utcnow
from app.core.deps import Ctx
from app.core.errors import Conflict, Forbidden, NotFound, Unprocessable
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


# Management ---------------------------------------------------------------------------


def coupon_out(db: Session, coupon: Coupon, editable: bool) -> dict:
    vendor = db.get(Vendor, coupon.vendor_id) if coupon.vendor_id else None
    return {
        "code": coupon.code,
        "funded_by": coupon.funded_by,
        "vendor_id": coupon.vendor_id,
        "vendor_name": vendor.name if vendor else None,
        "discount_type": coupon.discount_type,
        "percent_off": coupon.percent_off,
        "amount_off_cents": coupon.amount_off_cents,
        "min_subtotal_cents": coupon.min_subtotal_cents,
        "starts_at": coupon.starts_at,
        "ends_at": coupon.ends_at,
        "usage_limit": coupon.usage_limit,
        "per_customer_limit": coupon.per_customer_limit,
        "used_count": coupon.used_count,
        "is_flash": coupon.is_flash,
        "active": coupon.active,
        "note": coupon.note,
        "summary": describe(coupon),
        "editable": editable,
        "created_at": coupon.created_at,
    }


def _editable(ctx: Ctx, coupon: Coupon) -> bool:
    if ctx.scope == "platform":
        return True
    return coupon.funded_by == "vendor" and coupon.vendor_id == ctx.vendor_id


def list_coupons(ctx: Ctx, vendor_id: str | None, active_only: bool) -> list[dict]:
    query = select(Coupon).order_by(Coupon.created_at.desc())
    if ctx.scope == "vendor":
        query = query.where(Coupon.vendor_id == ctx.vendor_id, Coupon.funded_by == "vendor")
    elif vendor_id:
        query = query.where(Coupon.vendor_id == vendor_id)
    if active_only:
        query = query.where(Coupon.active.is_(True))
    return [coupon_out(ctx.db, c, _editable(ctx, c)) for c in ctx.db.scalars(query).all()]


def _window(starts: datetime, ends: datetime, is_flash: bool) -> None:
    if ends <= starts:
        raise Unprocessable("The end must be after the start", code="coupon_window")
    if is_flash and ends - starts > timedelta(days=7):
        raise Unprocessable("A flash coupon can run for at most 7 days", code="flash_window")


def _value(discount_type: str, percent: int | None, amount: int | None) -> tuple[int | None, int | None]:
    if discount_type == "percent":
        if percent is None or not 1 <= percent <= 90:
            raise Unprocessable("Percent off must be between 1 and 90", code="coupon_value")
        return percent, None
    if not amount or amount <= 0:
        raise Unprocessable("Enter the amount off in cents", code="coupon_value")
    return None, amount


def _normalize_code(code: str) -> str:
    code = code.strip().upper()
    if not code.replace("-", "").isalnum() or not code[0].isalnum():
        raise Unprocessable("Use letters, numbers and dashes, like SPRING15", code="bad_code")
    return code


def _guard_edit(ctx: Ctx, coupon: Coupon) -> None:
    if ctx.scope == "vendor" and not _editable(ctx, coupon):
        raise Forbidden("You can only change coupons funded by your shop", code="tenancy")


def create_coupon(ctx: Ctx, body) -> dict:
    db = ctx.db
    code = _normalize_code(body.code)
    if db.get(Coupon, code):
        raise Conflict(f"{code} already exists", code="duplicate_code")
    funded_by = body.funded_by
    vendor_id = body.vendor_id
    if ctx.scope == "vendor":
        funded_by = "vendor"
        vendor_id = ctx.vendor_id
    elif funded_by == "vendor" and not vendor_id:
        raise Unprocessable("A vendor-funded coupon needs a shop", code="vendor_required")
    if vendor_id and db.get(Vendor, vendor_id) is None:
        raise NotFound("Vendor", vendor_id)
    percent, amount = _value(body.discount_type, body.percent_off, body.amount_off_cents)
    _window(body.starts_at, body.ends_at, body.is_flash)
    coupon = Coupon(
        code=code,
        funded_by=funded_by,
        vendor_id=vendor_id,
        discount_type=body.discount_type,
        percent_off=percent,
        amount_off_cents=amount,
        min_subtotal_cents=body.min_subtotal_cents,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        usage_limit=body.usage_limit,
        per_customer_limit=body.per_customer_limit,
        is_flash=body.is_flash,
        note=body.note.strip(),
        active=True,
        created_by=ctx.user_id,
        created_at=utcnow(),
    )
    db.add(coupon)
    ctx.audit("coupon", "create", "coupon", code, after={"funded_by": funded_by, "vendor_id": vendor_id, "summary": describe(coupon)})
    ctx.commit()
    return coupon_out(db, coupon, True)


def update_coupon(ctx: Ctx, code: str, body) -> dict:
    db = ctx.db
    coupon = db.get(Coupon, code.strip().upper())
    if coupon is None:
        raise NotFound("Coupon", code)
    _guard_edit(ctx, coupon)
    changes = body.model_dump(exclude_unset=True)
    before = {"active": coupon.active, "summary": describe(coupon), "ends_at": coupon.ends_at}
    discount_type = changes.get("discount_type", coupon.discount_type)
    percent = changes["percent_off"] if "percent_off" in changes else coupon.percent_off
    amount = changes["amount_off_cents"] if "amount_off_cents" in changes else coupon.amount_off_cents
    if {"discount_type", "percent_off", "amount_off_cents"} & changes.keys():
        percent, amount = _value(discount_type, percent, amount)
        coupon.discount_type = discount_type
        coupon.percent_off = percent
        coupon.amount_off_cents = amount
    starts = changes.get("starts_at", coupon.starts_at)
    ends = changes.get("ends_at", coupon.ends_at)
    is_flash = changes.get("is_flash", coupon.is_flash)
    if {"starts_at", "ends_at", "is_flash"} & changes.keys():
        _window(starts, ends, is_flash)
        coupon.starts_at = starts
        coupon.ends_at = ends
        coupon.is_flash = is_flash
    if "usage_limit" in changes:
        limit = changes["usage_limit"]
        if limit is not None and limit < coupon.used_count:
            raise Conflict(f"The limit can't be below the {coupon.used_count} uses already counted", code="below_used")
        coupon.usage_limit = limit
    if "per_customer_limit" in changes and changes["per_customer_limit"] is not None:
        coupon.per_customer_limit = changes["per_customer_limit"]
    if "min_subtotal_cents" in changes and changes["min_subtotal_cents"] is not None:
        coupon.min_subtotal_cents = changes["min_subtotal_cents"]
    if "active" in changes and changes["active"] is not None:
        coupon.active = changes["active"]
    if "note" in changes and changes["note"] is not None:
        coupon.note = changes["note"]
    if "vendor_id" in changes and ctx.scope == "platform" and coupon.funded_by == "platform":
        vendor_id = changes["vendor_id"]
        if vendor_id and db.get(Vendor, vendor_id) is None:
            raise NotFound("Vendor", vendor_id)
        coupon.vendor_id = vendor_id
    ctx.audit("coupon", "update", "coupon", coupon.code, before=before, after={"active": coupon.active, "summary": describe(coupon), "ends_at": coupon.ends_at})
    ctx.commit()
    return coupon_out(db, coupon, _editable(ctx, coupon))


def delete_coupon(ctx: Ctx, code: str) -> None:
    db = ctx.db
    coupon = db.get(Coupon, code.strip().upper())
    if coupon is None:
        raise NotFound("Coupon", code)
    _guard_edit(ctx, coupon)
    if coupon.used_count:
        raise Conflict(
            f"{coupon.code} has been used {coupon.used_count} times. Pause it instead of deleting it.",
            code="coupon_used",
        )
    ctx.audit("coupon", "delete", "coupon", coupon.code, before={"summary": describe(coupon), "funded_by": coupon.funded_by})
    db.delete(coupon)
    ctx.commit()
