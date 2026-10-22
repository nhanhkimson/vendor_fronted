"""M6 fulfilment: order views per audience and the sub-order state machine."""

from datetime import datetime, timedelta

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import system_scope, utcnow
from app.core.deps import Ctx
from app.core.errors import Conflict, NotFound
from app.core.util import money
from app.domain import ledger
from app.domain.states import CANCELLABLE_SUB_ORDER, SUB_ORDER
from app.models import CommissionLine, Dispute, Order, Review, StockItem, SubOrder, SubOrderEvent, User, Vendor
from app.services.events import Notice, emit, users_with_permission, vendor_staff_ids
from app.services.placement import refresh_order_status
from app.services.tenancy import not_found

CARRIERS = {"US": "USPS", "CA": "Canada Post", "UK": "Royal Mail"}
VENDOR_NEXT = {
    "pending_acceptance": "Accept the order so the buyer knows you have it",
    "accepted": "Start packing",
    "packing": "Ship it and add the tracking number",
    "shipped": "Waiting for the carrier to deliver",
    "delivered": "Done. Earnings become payable after the holdback period",
    "cancelled": "Cancelled and refunded",
    "refunded": "Refunded to the buyer",
}
CUSTOMER_NEXT = {
    "pending_acceptance": "Waiting for the shop to accept",
    "accepted": "The shop accepted your order",
    "packing": "The shop is packing your order",
    "shipped": "On its way",
    "delivered": "Delivered",
    "cancelled": "Cancelled and refunded",
    "refunded": "Refunded",
}


def dispute_window_open(sub: SubOrder, now: datetime | None = None) -> bool:
    now = now or utcnow()
    if sub.status == "shipped":
        return True
    return sub.status == "delivered" and sub.delivered_at is not None and sub.delivered_at + timedelta(days=settings.holdback_days) > now


def dispute_out(db: Session, dispute: Dispute, names: dict[str, str] | None = None) -> dict:
    from app.services.payouts import held_for

    buyer = db.get(User, dispute.buyer_id)
    vendor = db.get(Vendor, dispute.vendor_id)
    sub = db.get(SubOrder, dispute.sub_order_id)
    return {
        "id": dispute.id,
        "order_id": dispute.order_id,
        "sub_order_id": dispute.sub_order_id,
        "buyer_id": dispute.buyer_id,
        "buyer_name": buyer.name if buyer else dispute.buyer_id,
        "vendor_id": dispute.vendor_id,
        "vendor_name": vendor.name if vendor else dispute.vendor_id,
        "reason": dispute.reason,
        "note": dispute.note,
        "status": dispute.status,
        "resolution_note": dispute.resolution_note,
        "resolved_by": dispute.resolved_by,
        "resolved_at": dispute.resolved_at,
        "created_at": dispute.created_at,
        "charged_cents": sub.charged_cents if sub else 0,
        "held_payouts": held_for(db, dispute.vendor_id) if dispute.status == "open" else [],
    }


def _actions(sub: SubOrder, viewer: str, has_dispute: bool) -> list[str]:
    if viewer == "vendor":
        return {
            "pending_acceptance": ["accept", "cancel"],
            "accepted": ["pack", "cancel"],
            "packing": ["ship", "cancel"],
            "shipped": ["deliver"],
        }.get(sub.status, [])
    if viewer == "customer":
        actions = []
        if sub.status in ("pending_acceptance", "accepted"):
            actions.append("cancel")
        if sub.status == "shipped":
            actions.append("confirm_delivery")
        if not has_dispute and dispute_window_open(sub):
            actions.append("dispute")
        return actions + ["message"]
    actions = [t for t in SUB_ORDER.allowed(sub.status) if t in ("accepted", "packing", "shipped", "delivered")]
    if sub.status in CANCELLABLE_SUB_ORDER:
        actions.append("cancel")
    return actions


def sub_order_out(db: Session, sub: SubOrder, viewer: str, order: Order | None = None) -> dict:
    order = order or db.get(Order, sub.order_id)
    vendor = db.get(Vendor, sub.vendor_id)
    buyer = db.get(User, sub.buyer_id)
    commissions = {}
    if viewer != "customer":
        commissions = {
            c.order_line_id: c
            for c in db.scalars(select(CommissionLine).where(CommissionLine.sub_order_id == sub.id)).all()
        }
    reviews = {}
    if viewer == "customer":
        reviews = {
            r.product_id: r.id
            for r in db.scalars(select(Review).where(Review.sub_order_id == sub.id, Review.buyer_id == sub.buyer_id)).all()
        }
    dispute = db.scalar(select(Dispute).where(Dispute.sub_order_id == sub.id).order_by(Dispute.created_at.desc()))
    lines = []
    for line in sub.lines:
        commission = commissions.get(line.id)
        lines.append(
            {
                "id": line.id,
                "product_id": line.product_id,
                "variant_id": line.variant_id,
                "title": line.title,
                "sku": line.sku,
                "size": line.size,
                "color": line.color,
                "image_url": line.image_url,
                "unit_price_cents": line.unit_price_cents,
                "qty": line.qty,
                "line_total_cents": line.line_total_cents,
                "vendor_discount_cents": line.vendor_discount_cents,
                "platform_discount_cents": line.platform_discount_cents,
                "commission_cents": commission.fee_cents if commission else None,
                "commission_rate_bps": commission.rate_bps if commission else None,
                "review_id": reviews.get(line.product_id),
                "can_review": viewer == "customer" and sub.status == "delivered" and line.product_id not in reviews,
            }
        )
    hide_money = viewer == "customer"
    next_step = (CUSTOMER_NEXT if viewer == "customer" else VENDOR_NEXT).get(sub.status)
    if sub.in_dispute:
        next_step = "Dispute open: Bazaar support is reviewing it"
    return {
        "id": sub.id,
        "order_id": sub.order_id,
        "vendor_id": sub.vendor_id,
        "vendor_name": vendor.name if vendor else sub.vendor_id,
        "vendor_slug": vendor.slug if vendor else "",
        "buyer_id": sub.buyer_id,
        "buyer_name": buyer.name if buyer else sub.buyer_id,
        "ship_name": order.ship_name if order else "",
        "ship_address": order.ship_address if order else "",
        "status": sub.status,
        "items_subtotal_cents": sub.items_subtotal_cents,
        "shipping_cents": sub.shipping_cents,
        "vendor_discount_cents": sub.vendor_discount_cents,
        "platform_discount_cents": sub.platform_discount_cents,
        "charged_cents": sub.charged_cents,
        "commission_cents": None if hide_money else sub.commission_cents,
        "vendor_net_cents": None if hide_money else sub.vendor_net_cents,
        "refunded_cents": sub.refunded_cents,
        "tracking_number": sub.tracking_number,
        "carrier": sub.carrier,
        "in_dispute": sub.in_dispute,
        "accepted_at": sub.accepted_at,
        "shipped_at": sub.shipped_at,
        "delivered_at": sub.delivered_at,
        "cancelled_at": sub.cancelled_at,
        "created_at": sub.created_at,
        "placed_at": order.placed_at if order else sub.created_at,
        "lines": lines,
        "events": [
            {"from_status": e.from_status, "to_status": e.to_status, "actor_role": e.actor_role, "note": e.note, "at": e.at}
            for e in sub.events
        ],
        "dispute": dispute_out(db, dispute) if dispute else None,
        "allowed_actions": _actions(sub, viewer, dispute is not None),
        "next_step": next_step,
    }


def order_out(db: Session, order: Order, viewer: str) -> dict:
    buyer = db.get(User, order.buyer_id)
    return {
        "id": order.id,
        "status": order.status,
        "buyer_id": order.buyer_id,
        "buyer_name": buyer.name if buyer else order.buyer_id,
        "placed_at": order.placed_at,
        "completed_at": order.completed_at,
        "items_subtotal_cents": order.items_subtotal_cents,
        "shipping_cents": order.shipping_cents,
        "discount_cents": order.discount_cents,
        "platform_discount_cents": order.platform_discount_cents,
        "vendor_discount_cents": order.vendor_discount_cents,
        "total_cents": order.total_cents,
        "refunded_cents": order.refunded_cents,
        "coupon_code": order.coupon_code,
        "source": order.source,
        "ship_name": order.ship_name,
        "ship_address": order.ship_address,
        "card_last4": order.card_last4,
        "sub_orders": [sub_order_out(db, s, viewer, order) for s in order.sub_orders],
    }


# Reads -------------------------------------------------------------------------------


def my_orders(ctx: Ctx) -> list[dict]:
    orders = ctx.db.scalars(select(Order).where(Order.buyer_id == ctx.user_id).order_by(Order.placed_at.desc())).all()
    return [order_out(ctx.db, o, "customer") for o in orders]


def my_order(ctx: Ctx, order_id: str) -> dict:
    order = ctx.db.get(Order, order_id)
    if order is None or order.buyer_id != ctx.user_id:
        raise not_found(ctx, Order, order_id, "Order", "order", "order")
    return order_out(ctx.db, order, "customer")


def vendor_orders(ctx: Ctx, status: str | None, q: str | None) -> list[dict]:
    query = select(SubOrder).where(SubOrder.vendor_id == ctx.vendor_id).order_by(SubOrder.created_at.desc())
    if status == "open":
        query = query.where(SubOrder.status.in_(("pending_acceptance", "accepted", "packing")))
    elif status:
        query = query.where(SubOrder.status == status)
    if q:
        query = query.where(or_(SubOrder.id.ilike(f"%{q}%"), SubOrder.tracking_number.ilike(f"%{q}%")))
    return [sub_order_out(ctx.db, s, "vendor") for s in ctx.db.scalars(query).all()]


def vendor_sub_order(ctx: Ctx, sub_id: str) -> SubOrder:
    sub = ctx.db.get(SubOrder, sub_id)
    if sub is None or sub.vendor_id != ctx.vendor_id:
        raise not_found(ctx, SubOrder, sub_id, "Order", "order", "sub_order")
    return sub


def staff_sub_order(ctx: Ctx, sub_id: str) -> SubOrder:
    sub = ctx.db.get(SubOrder, sub_id)
    if sub is None:
        raise NotFound("Order", sub_id)
    return sub


def customer_sub_order(ctx: Ctx, sub_id: str) -> SubOrder:
    sub = ctx.db.get(SubOrder, sub_id)
    if sub is None or sub.buyer_id != ctx.user_id:
        raise not_found(ctx, SubOrder, sub_id, "Order", "order", "sub_order")
    return sub


def staff_orders(ctx: Ctx, status: str | None, vendor_id: str | None, q: str | None, since: datetime | None) -> list[dict]:
    query = select(Order).order_by(Order.placed_at.desc())
    if status:
        query = query.where(Order.status == status)
    if vendor_id:
        query = query.where(Order.id.in_(select(SubOrder.order_id).where(SubOrder.vendor_id == vendor_id)))
    if q:
        like = f"%{q.lower()}%"
        query = query.where(
            or_(
                func.lower(Order.id).like(like),
                Order.buyer_id.in_(select(User.id).where(or_(func.lower(User.name).like(like), func.lower(User.email).like(like)))),
            )
        )
    if since:
        query = query.where(Order.placed_at >= since)
    return [order_out(ctx.db, o, "platform") for o in ctx.db.scalars(query.limit(200)).all()]


def staff_order(ctx: Ctx, order_id: str) -> dict:
    order = ctx.db.get(Order, order_id)
    if order is None:
        raise NotFound("Order", order_id)
    return order_out(ctx.db, order, "platform")


# Transitions --------------------------------------------------------------------------


def _event(db: Session, sub: SubOrder, before: str, after: str, actor_id: str | None, role: str, note: str) -> None:
    db.add(SubOrderEvent(sub_order_id=sub.id, from_status=before, to_status=after, actor_id=actor_id, actor_role=role, note=note, at=utcnow()))


def _notify(db: Session, sub: SubOrder, title_buyer: str | None, title_vendor: str | None, event: str) -> None:
    notices = []
    if title_buyer:
        notices.append(Notice(sub.buyer_id, title_buyer, f"/account/orders/{sub.order_id}"))
    if title_vendor:
        notices += [Notice(uid, title_vendor, "/seller/orders") for uid in vendor_staff_ids(db, sub.vendor_id)]
    emit(db, event, {"sub_order_id": sub.id, "status": sub.status}, notices)


def move(
    ctx: Ctx,
    sub: SubOrder,
    target: str,
    *,
    role: str,
    action: str = "update_status",
    note: str | None = None,
    tracking: str | None = None,
    carrier: str | None = None,
) -> SubOrder:
    db = ctx.db
    SUB_ORDER.check(sub.status, target, f"Order {sub.id}")
    if target == "shipped" and not (tracking or "").strip():
        raise Conflict("Add the tracking number before marking the order shipped", code="tracking_required")
    before = sub.status
    now = utcnow()
    with system_scope(db):
        sub.status = target
        if target == "accepted":
            sub.accepted_at = now
        elif target == "shipped":
            vendor = db.get(Vendor, sub.vendor_id)
            sub.tracking_number = tracking.strip()
            sub.carrier = (carrier or "").strip() or CARRIERS.get(vendor.country if vendor else "US", "USPS")
            sub.shipped_at = now
        elif target == "delivered":
            sub.delivered_at = now
        text = note or {
            "accepted": "Shop accepted the order",
            "packing": "Packing started",
            "shipped": f"Shipped with {sub.carrier} {sub.tracking_number}",
            "delivered": "Delivered",
        }.get(target, target)
        _event(db, sub, before, target, ctx.user_id, role, text)
        refresh_order_status(db, db.get(Order, sub.order_id))
    ctx.audit(
        "order",
        action,
        "sub_order",
        sub.id,
        before={"status": before},
        after={"status": target, "tracking_number": sub.tracking_number if target == "shipped" else None},
        reason=note,
    )
    buyer_titles = {
        "accepted": f"{sub.id} was accepted by the shop",
        "shipped": f"{sub.id} shipped: {sub.carrier} {sub.tracking_number}",
        "delivered": f"{sub.id} was delivered. Tell others what you think.",
    }
    vendor_title = None
    if target == "delivered":
        vendor_title = f"{sub.id} was delivered. Earnings become payable after {settings.holdback_days} days."
    elif role == "staff":
        vendor_title = f"Bazaar support moved {sub.id} to {target.replace('_', ' ')}"
    _notify(db, sub, buyer_titles.get(target) if role != "customer" else None, vendor_title, f"sub_order.{target}")
    ctx.commit()
    return sub


def cancel(ctx: Ctx, sub: SubOrder, reason: str, role: str) -> SubOrder:
    db = ctx.db
    if sub.status not in CANCELLABLE_SUB_ORDER:
        SUB_ORDER.check(sub.status, "cancelled", f"Order {sub.id}")
    if role == "customer" and sub.status not in ("pending_acceptance", "accepted"):
        raise Conflict("The shop has started packing. Message the shop to ask them to cancel.", code="too_late_to_cancel")
    before = sub.status
    with system_scope(db):
        for line in sub.lines:
            db.execute(
                update(StockItem)
                .where(StockItem.variant_id == line.variant_id, StockItem.warehouse_id == sub.warehouse_id)
                .values(on_hand=StockItem.on_hand + line.qty, updated_at=utcnow())
            )
        sub.status = "cancelled"
        sub.cancelled_at = utcnow()
        sub.refunded_cents = sub.charged_cents
        ledger.post_refund(db, sub, f"Cancelled by {role}: {reason}")
        _event(db, sub, before, "cancelled", ctx.user_id, role, f"Cancelled: {reason}")
        refresh_order_status(db, db.get(Order, sub.order_id))
    ctx.audit(
        "order",
        "cancel",
        "sub_order",
        sub.id,
        before={"status": before},
        after={"status": "cancelled", "refunded_cents": sub.refunded_cents, "restocked": True},
        reason=reason,
    )
    _notify(
        db,
        sub,
        f"{sub.id} was cancelled. {money(sub.refunded_cents)} is refunded to your card." if role != "customer" else f"You cancelled {sub.id}. {money(sub.refunded_cents)} is refunded.",
        f"{sub.id} was cancelled: {reason}" if role != "vendor" else None,
        "sub_order.cancelled",
    )
    ctx.commit()
    return sub


def notify_support(db: Session, title: str, link: str) -> list[Notice]:
    return [Notice(uid, title, link) for uid in users_with_permission(db, "dispute:resolve")]


def confirm_delivery(ctx: Ctx, sub: SubOrder) -> SubOrder:
    return move(ctx, sub, "delivered", role="customer", action="confirm_delivery", note="Buyer confirmed delivery")
