"""Background upkeep, run every minute by the API process (and on demand in tests).

- Expired checkouts give back their reserved stock and coupon use.
- Orders whose sub-orders are all delivered complete once the holdback passes.
"""

from datetime import datetime

from sqlalchemy import select

from app.core.db import SessionLocal, set_scope, utcnow
from app.models import Order, PaymentIntent
from app.services.audit import record_system
from app.services.checkout import release
from app.services.placement import refresh_order_status


def expire_checkouts(db, now: datetime) -> list[str]:
    stale = db.scalars(
        select(PaymentIntent)
        .where(PaymentIntent.status == "requires_payment", PaymentIntent.expires_at <= now)
        .with_for_update(skip_locked=True)
    ).all()
    for intent in stale:
        release(db, intent, "expired", "Checkout window expired")
        record_system(
            db,
            "order",
            "expire_checkout",
            "payment_intent",
            intent.id,
            before={"status": "requires_payment"},
            after={"status": "expired", "stock_released": True, "coupon_released": intent.coupon_code},
            reason="Checkout window expired",
        )
    return [i.id for i in stale]


def complete_orders(db, now: datetime) -> list[str]:
    candidates = db.scalars(select(Order).where(Order.status.in_(("fulfilled", "partially_refunded")))).all()
    completed = []
    for order in candidates:
        before = order.status
        refresh_order_status(db, order, now)
        if order.status == "completed" and before != "completed":
            completed.append(order.id)
            record_system(
                db,
                "order",
                "complete",
                "order",
                order.id,
                before={"status": before},
                after={"status": "completed"},
                reason="All parcels delivered and the holdback period passed",
            )
    return completed


def tick(now: datetime | None = None) -> dict:
    now = now or utcnow()
    with SessionLocal() as db:
        set_scope(db, "platform")
        expired = expire_checkouts(db, now)
        completed = complete_orders(db, now)
        db.commit()
    return {"expired_checkouts": expired, "completed_orders": completed}
