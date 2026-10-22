"""Turn a frozen quote into a parent order, sub-orders, commission lines and ledger entries.

Shared by payment confirmation and the seed, so demo orders follow exactly
the same money rules as real checkouts.
"""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import utcnow
from app.domain import ledger
from app.domain.commission import active_rules, category_chain, describe, pick_rule
from app.domain.money import commission_fee
from app.domain.pricing import Quote
from app.domain.states import ORDER, derive_order_status
from app.models import CommissionLine, CouponRedemption, Order, OrderLine, SubOrder, SubOrderEvent, Vendor


def place_order(
    db: Session,
    *,
    order_id: str,
    buyer_id: str,
    quote: Quote,
    placed_at: datetime,
    source: str = "organic",
    ship_name: str = "",
    ship_address: str = "",
    card_last4: str | None = None,
    payment_intent_id: str | None = None,
) -> Order:
    vendor_ids = [g.vendor_id for g in quote.groups]
    vendors = {v.id: v for v in db.scalars(select(Vendor).where(Vendor.id.in_(vendor_ids))).all()}
    rules = active_rules(db, placed_at)

    order = Order(
        id=order_id,
        buyer_id=buyer_id,
        payment_intent_id=payment_intent_id,
        status="paid",
        items_subtotal_cents=quote.items_subtotal_cents,
        shipping_cents=quote.shipping_cents,
        discount_cents=quote.discount_cents,
        platform_discount_cents=quote.platform_discount_cents,
        vendor_discount_cents=quote.vendor_discount_cents,
        total_cents=quote.total_cents,
        coupon_code=quote.coupon.code if quote.coupon else None,
        source=source,
        ship_name=ship_name,
        ship_address=ship_address,
        card_last4=card_last4,
        placed_at=placed_at,
    )
    db.add(order)
    db.flush()

    subs: list[SubOrder] = []
    for group in quote.groups:
        vendor = vendors[group.vendor_id]
        priced = []
        for qline in group.lines:
            rule = pick_rule(rules, vendor.id, vendor.tier_id, category_chain(db, qline.category_id))
            base = qline.commission_base_cents
            priced.append((qline, rule, base, commission_fee(base, rule.rate_bps, rule.min_fee_cents)))
        commission = sum(fee for *_, fee in priced)

        sub = SubOrder(
            id=f"{order_id}-{vendor.id}",
            order_id=order_id,
            vendor_id=vendor.id,
            buyer_id=buyer_id,
            status="pending_acceptance",
            items_subtotal_cents=group.items_subtotal_cents,
            shipping_cents=group.shipping_cents,
            vendor_discount_cents=group.vendor_discount_cents,
            platform_discount_cents=group.platform_discount_cents,
            charged_cents=group.charged_cents,
            commission_cents=commission,
            vendor_net_cents=group.items_subtotal_cents
            + group.shipping_cents
            - group.vendor_discount_cents
            - commission,
            warehouse_id=vendor.warehouse_id,
            created_at=placed_at,
        )
        db.add(sub)
        db.flush()

        for qline, rule, base, fee in priced:
            line = OrderLine(
                sub_order_id=sub.id,
                order_id=order_id,
                vendor_id=vendor.id,
                buyer_id=buyer_id,
                product_id=qline.product_id,
                variant_id=qline.variant_id,
                category_id=qline.category_id,
                title=qline.title,
                sku=qline.sku,
                size=qline.size,
                color=qline.color,
                image_url=qline.image_url,
                unit_price_cents=qline.unit_price_cents,
                qty=qline.qty,
                line_total_cents=qline.line_total_cents,
                vendor_discount_cents=qline.vendor_discount_cents,
                platform_discount_cents=qline.platform_discount_cents,
            )
            db.add(line)
            db.flush()
            db.add(
                CommissionLine(
                    order_line_id=line.id,
                    sub_order_id=sub.id,
                    order_id=order_id,
                    vendor_id=vendor.id,
                    rule_id=rule.id,
                    rule_version=rule.version,
                    rule_target=describe(rule),
                    rate_bps=rule.rate_bps,
                    min_fee_cents=rule.min_fee_cents,
                    base_cents=base,
                    fee_cents=fee,
                    computed_at=placed_at,
                )
            )
        db.add(
            SubOrderEvent(
                sub_order_id=sub.id,
                from_status=None,
                to_status="pending_acceptance",
                actor_id=buyer_id,
                actor_role="customer",
                note="Order placed and paid",
                at=placed_at,
            )
        )
        subs.append(sub)

    if quote.coupon:
        db.add(
            CouponRedemption(
                coupon_code=quote.coupon.code,
                customer_id=buyer_id,
                order_id=order_id,
                discount_cents=quote.discount_cents,
                at=placed_at,
            )
        )
    db.flush()
    ledger.post_order(db, order, subs, placed_at)
    db.flush()
    return order


def holdback_passed(subs: list[SubOrder], now: datetime | None = None) -> bool:
    now = now or utcnow()
    closed_at = [s.delivered_at or s.cancelled_at for s in subs if s.status != "refunded"]
    closed_at = [t for t in closed_at if t is not None]
    if not closed_at:
        return False
    return max(closed_at) + timedelta(days=settings.holdback_days) <= now


def refresh_order_status(
    db: Session, order: Order, now: datetime | None = None, *, validate: bool = True
) -> str:
    """Recompute the parent status. `validate=False` lets the seed jump straight to a final state."""
    subs = list(db.scalars(select(SubOrder).where(SubOrder.order_id == order.id)).all())
    open_dispute = any(s.in_dispute for s in subs)
    target = derive_order_status([s.status for s in subs], holdback_passed(subs, now) and not open_dispute)
    if target != order.status:
        if validate:
            ORDER.check(order.status, target, "Order")
        order.status = target
        if target == "completed":
            order.completed_at = now or utcnow()
    order.refunded_cents = sum(s.refunded_cents for s in subs)
    return order.status
