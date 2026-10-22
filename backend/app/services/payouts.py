"""M7 payouts: holdback, dispute freeze, two-person approval.

A vendor requests either a prepared statement (status `eligible`) or a new
payout built from delivered sub-orders whose holdback has passed. Two
different staff members must sign, and neither may be the person who asked.
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import system_scope, utcnow
from app.core.deps import Ctx
from app.core.errors import Conflict, NotFound
from app.core.util import money, new_id
from app.domain import ledger
from app.domain.states import PAYOUT
from app.models import Dispute, Payout, PayoutApproval, PayoutEvent, PayoutItem, SubOrder, User, Vendor
from app.services.events import Notice, emit, users_with_permission, vendor_staff_ids
from app.services.tenancy import owned

FREEZABLE = ("eligible", "requested", "pending_second_approval", "approved")
CLOSED_MONEY = ("cancelled", "refunded")
IN_FLIGHT = ("requested", "pending_second_approval", "approved", "held_for_dispute")


def _event(db: Session, payout: Payout, before: str | None, after: str, actor: str | None, note: str) -> None:
    db.add(PayoutEvent(payout_id=payout.id, from_status=before, to_status=after, actor_id=actor, note=note, at=utcnow()))


def hold_for_dispute(db: Session, vendor_id: str, dispute_id: str, actor_id: str | None) -> list[str]:
    held = []
    with system_scope(db):
        for payout in db.scalars(select(Payout).where(Payout.vendor_id == vendor_id, Payout.status.in_(FREEZABLE))).all():
            PAYOUT.check(payout.status, "held_for_dispute", f"Payout {payout.id}")
            _event(db, payout, payout.status, "held_for_dispute", actor_id, f"Dispute {dispute_id} opened")
            payout.held_from_status = payout.status
            payout.status = "held_for_dispute"
            held.append(payout.id)
    return held


def release_holds(db: Session, vendor_id: str, actor_id: str | None, note: str) -> list[str]:
    released = []
    with system_scope(db):
        still_open = db.scalar(select(Dispute.id).where(Dispute.vendor_id == vendor_id, Dispute.status == "open"))
        if still_open:
            return []
        for payout in db.scalars(select(Payout).where(Payout.vendor_id == vendor_id, Payout.status == "held_for_dispute")).all():
            target = payout.held_from_status or "eligible"
            PAYOUT.check(payout.status, target, f"Payout {payout.id}")
            _event(db, payout, payout.status, target, actor_id, note)
            payout.status = target
            payout.held_from_status = None
            released.append(payout.id)
    return released


def held_for(db: Session, vendor_id: str) -> list[str]:
    return list(db.scalars(select(Payout.id).where(Payout.vendor_id == vendor_id, Payout.status == "held_for_dispute")).all())


def _vendor(db: Session, vendor_id: str) -> Vendor:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise NotFound("Vendor", vendor_id)
    return vendor


def _name(db: Session, user_id: str | None) -> str | None:
    user = db.get(User, user_id) if user_id else None
    return user.name if user else None


def payout_out(db: Session, payout: Payout, viewer: str, user_id: str | None) -> dict:
    vendor = db.get(Vendor, payout.vendor_id)
    signed = {a.approver_id for a in payout.approvals}
    actions: list[str] = []
    if viewer == "vendor" and payout.status == "eligible":
        actions.append("request")
    if viewer == "platform" and payout.status in ("requested", "pending_second_approval"):
        if user_id and user_id != payout.requested_by and user_id not in signed:
            actions.append("approve")
    if viewer == "platform" and payout.status == "approved":
        actions.append("pay")
    return {
        "id": payout.id,
        "vendor_id": payout.vendor_id,
        "vendor_name": vendor.name if vendor else payout.vendor_id,
        "amount_cents": payout.amount_cents,
        "status": payout.status,
        "held_from_status": payout.held_from_status,
        "note": payout.note,
        "reference": payout.reference,
        "requested_by": payout.requested_by,
        "requested_by_name": _name(db, payout.requested_by),
        "requested_at": payout.requested_at,
        "approved_at": payout.approved_at,
        "paid_at": payout.paid_at,
        "created_at": payout.created_at,
        "approvals": [
            {"approver_id": a.approver_id, "approver_name": a.approver_name, "approver_roles": a.approver_roles, "at": a.at}
            for a in payout.approvals
        ],
        "items": [{"sub_order_id": item.sub_order_id, "amount_cents": item.amount_cents} for item in payout.items],
        "events": [
            {"from_status": e.from_status, "to_status": e.to_status, "actor_id": e.actor_id, "note": e.note, "at": e.at}
            for e in payout.events
        ],
        "allowed_actions": actions,
    }


def _refresh(db: Session, payout: Payout) -> None:
    db.flush()
    db.expire(payout, ["events", "approvals", "items"])


def position(db: Session, vendor_id: str, now: datetime | None = None) -> dict:
    """What the vendor can ask for, what is still in holdback, and what a dispute has frozen."""
    now = now or utcnow()
    cutoff = now - timedelta(days=settings.holdback_days)
    subs = db.scalars(select(SubOrder).where(SubOrder.vendor_id == vendor_id)).all()
    assigned = set(db.scalars(select(PayoutItem.sub_order_id).where(PayoutItem.vendor_id == vendor_id)).all())
    matured: list[SubOrder] = []
    held: list[SubOrder] = []
    disputed: list[SubOrder] = []
    for sub in subs:
        if sub.status in CLOSED_MONEY:
            continue
        if sub.in_dispute:
            disputed.append(sub)
        elif sub.status == "delivered" and sub.delivered_at and sub.delivered_at <= cutoff and sub.id not in assigned:
            matured.append(sub)
        elif sub.id not in assigned:
            held.append(sub)
    payouts = db.scalars(select(Payout).where(Payout.vendor_id == vendor_id)).all()
    eligible = [p for p in payouts if p.status == "eligible"]
    dispute_open = db.scalar(select(Dispute.id).where(Dispute.vendor_id == vendor_id, Dispute.status == "open")) is not None
    matured_cents = sum(s.vendor_net_cents for s in matured)
    held_dates = [s.delivered_at for s in held if s.status == "delivered" and s.delivered_at]
    return {
        "balance_cents": ledger.vendor_balance(db, vendor_id),
        "matured_cents": matured_cents,
        "held_back_cents": sum(s.vendor_net_cents for s in held),
        "in_dispute_cents": sum(s.vendor_net_cents for s in disputed),
        "reserved_cents": sum(p.amount_cents for p in payouts if p.status in IN_FLIGHT),
        "eligible_cents": sum(p.amount_cents for p in eligible),
        "eligible_count": len(eligible),
        "available_cents": 0 if dispute_open else matured_cents + sum(p.amount_cents for p in eligible),
        "open_dispute": dispute_open,
        "matured": matured,
        "next_payable_at": min(held_dates) + timedelta(days=settings.holdback_days) if held_dates else None,
        "payouts": payouts,
    }


def _bounds(date_from: date | None, date_to: date | None) -> tuple[datetime | None, datetime | None]:
    start = datetime.combine(date_from, time.min, utcnow().tzinfo) if date_from else None
    end = datetime.combine(date_to + timedelta(days=1), time.min, utcnow().tzinfo) if date_to else None
    return start, end


def statement(db: Session, vendor_id: str, date_from: date | None, date_to: date | None) -> dict:
    start, end = _bounds(date_from, date_to)
    query = select(SubOrder).where(SubOrder.vendor_id == vendor_id).order_by(SubOrder.created_at.desc())
    if start:
        query = query.where(SubOrder.created_at >= start)
    if end:
        query = query.where(SubOrder.created_at < end)
    subs = db.scalars(query).all()
    live = [s for s in subs if s.status not in CLOSED_MONEY]
    lines = [
        {
            "sub_order_id": s.id,
            "order_id": s.order_id,
            "placed_at": s.created_at,
            "status": s.status,
            "items_cents": s.items_subtotal_cents,
            "shipping_cents": s.shipping_cents,
            "vendor_discount_cents": s.vendor_discount_cents,
            "platform_discount_cents": s.platform_discount_cents,
            "charged_cents": s.charged_cents,
            "commission_cents": s.commission_cents,
            "net_cents": s.vendor_net_cents,
            "refunded_cents": s.refunded_cents,
        }
        for s in subs
    ]
    return {
        "date_from": date_from,
        "date_to": date_to,
        "orders": len(subs),
        "items_cents": sum(s.items_subtotal_cents for s in subs),
        "shipping_cents": sum(s.shipping_cents for s in subs),
        "vendor_discount_cents": sum(s.vendor_discount_cents for s in subs),
        "platform_discount_cents": sum(s.platform_discount_cents for s in subs),
        "charged_cents": sum(s.charged_cents for s in subs),
        "commission_cents": sum(s.commission_cents for s in live),
        "refunded_cents": sum(s.refunded_cents for s in subs),
        "net_cents": sum(s.vendor_net_cents for s in live),
        "lines": lines,
    }


def earnings(ctx: Ctx, vendor_id: str, date_from: date | None, date_to: date | None) -> dict:
    db = ctx.db
    vendor = _vendor(db, vendor_id)
    if ctx.scope == "vendor" and vendor_id != ctx.vendor_id:
        raise NotFound("Vendor", vendor_id)
    pos = position(db, vendor_id)
    viewer = "vendor" if ctx.scope == "vendor" else "platform"
    payouts = sorted(pos["payouts"], key=lambda p: p.created_at, reverse=True)
    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.name,
        "holdback_days": settings.holdback_days,
        "balance_cents": pos["balance_cents"],
        "available_cents": pos["available_cents"],
        "matured_cents": pos["matured_cents"],
        "held_back_cents": pos["held_back_cents"],
        "in_dispute_cents": pos["in_dispute_cents"],
        "reserved_cents": pos["reserved_cents"],
        "open_dispute": pos["open_dispute"],
        "next_payable_at": pos["next_payable_at"],
        "payable_orders": [
            {"sub_order_id": s.id, "order_id": s.order_id, "delivered_at": s.delivered_at, "vendor_net_cents": s.vendor_net_cents}
            for s in sorted(pos["matured"], key=lambda s: s.delivered_at or s.created_at)
        ],
        "payouts": [payout_out(db, p, viewer, ctx.user_id) for p in payouts],
        "statement": statement(db, vendor_id, date_from, date_to),
    }


def list_payouts(ctx: Ctx, status: str | None, vendor_id: str | None) -> list[dict]:
    query = select(Payout).order_by(Payout.created_at.desc())
    if ctx.scope == "vendor":
        query = query.where(Payout.vendor_id == ctx.vendor_id)
    elif vendor_id:
        query = query.where(Payout.vendor_id == vendor_id)
    if status:
        query = query.where(Payout.status == status)
    viewer = "vendor" if ctx.scope == "vendor" else "platform"
    return [payout_out(ctx.db, p, viewer, ctx.user_id) for p in ctx.db.scalars(query).all()]


def get_payout(ctx: Ctx, payout_id: str) -> dict:
    payout = owned(ctx, Payout, payout_id, "Payout", "commission", "payout")
    viewer = "vendor" if ctx.scope == "vendor" else "platform"
    return payout_out(ctx.db, payout, viewer, ctx.user_id)


def _guard_request(db: Session, vendor: Vendor) -> None:
    if not vendor.payout_account:
        raise Conflict("Add a payout account in your shop settings before requesting a payout.", code="no_payout_account")
    if db.scalar(select(Dispute.id).where(Dispute.vendor_id == vendor.id, Dispute.status == "open")):
        raise Conflict("Payouts are frozen while a dispute is open.", code="dispute_open")


def _notify_approvers(db: Session, payout: Payout, title: str) -> None:
    notices = [Notice(uid, title, "/admin/payouts") for uid in users_with_permission(db, "payout:approve")]
    emit(db, "payout.requested", {"payout_id": payout.id, "amount_cents": payout.amount_cents}, notices)


def request_payout(ctx: Ctx, payout_id: str) -> dict:
    db = ctx.db
    payout = owned(ctx, Payout, payout_id, "Payout", "commission", "payout")
    vendor = _vendor(db, payout.vendor_id)
    _guard_request(db, vendor)
    before = payout.status
    PAYOUT.check(before, "requested", f"Payout {payout.id}")
    payout.status = "requested"
    payout.requested_by = ctx.user_id
    payout.requested_at = utcnow()
    _event(db, payout, before, "requested", ctx.user_id, "Vendor requested the payout")
    ctx.audit("commission", "request_payout", "payout", payout.id, before={"status": before}, after={"status": "requested", "amount_cents": payout.amount_cents})
    _notify_approvers(db, payout, f"{vendor.name} requested {money(payout.amount_cents)} ({payout.id})")
    _refresh(db, payout)
    ctx.commit()
    return payout_out(db, payout, "vendor", ctx.user_id)


def request_matured(ctx: Ctx) -> dict:
    """Bundle every delivered sub-order past the holdback into one payout request."""
    db = ctx.db
    vendor = _vendor(db, ctx.vendor_id)
    _guard_request(db, vendor)
    cutoff = utcnow() - timedelta(days=settings.holdback_days)
    assigned = select(PayoutItem.sub_order_id)
    subs = db.scalars(
        select(SubOrder)
        .where(
            SubOrder.vendor_id == vendor.id,
            SubOrder.status == "delivered",
            SubOrder.in_dispute.is_(False),
            SubOrder.delivered_at <= cutoff,
            SubOrder.vendor_net_cents > 0,
            SubOrder.id.not_in(assigned),
        )
        .with_for_update()
    ).all()
    if not subs:
        raise Conflict(
            f"Nothing is payable yet. Delivered orders can be paid {settings.holdback_days} days after delivery.",
            code="nothing_payable",
        )
    now = utcnow()
    payout = Payout(
        id=new_id("PAY", 8),
        vendor_id=vendor.id,
        amount_cents=sum(s.vendor_net_cents for s in subs),
        status="requested",
        note=f"{len(subs)} delivered orders past the {settings.holdback_days}-day holdback",
        requested_by=ctx.user_id,
        requested_at=now,
        created_at=now,
    )
    db.add(payout)
    db.flush()
    for sub in subs:
        db.add(PayoutItem(payout_id=payout.id, vendor_id=vendor.id, sub_order_id=sub.id, amount_cents=sub.vendor_net_cents))
    _event(db, payout, None, "requested", ctx.user_id, payout.note)
    ctx.audit(
        "commission",
        "request_payout",
        "payout",
        payout.id,
        after={"amount_cents": payout.amount_cents, "sub_orders": [s.id for s in subs]},
    )
    _notify_approvers(db, payout, f"{vendor.name} requested {money(payout.amount_cents)} ({payout.id})")
    _refresh(db, payout)
    ctx.commit()
    return payout_out(db, payout, "vendor", ctx.user_id)


def approve(ctx: Ctx, payout_id: str, note: str | None) -> dict:
    db = ctx.db
    payout = db.get(Payout, payout_id, with_for_update=True)
    if payout is None:
        raise NotFound("Payout", payout_id)
    if payout.requested_by == ctx.user_id:
        raise Conflict("The person who requested a payout cannot approve it.", code="separation_of_duties")
    if any(a.approver_id == ctx.user_id for a in payout.approvals):
        raise Conflict("You already signed this payout. A different person must sign next.", code="already_signed")
    target = "pending_second_approval" if payout.status == "requested" else "approved"
    before = payout.status
    PAYOUT.check(before, target, f"Payout {payout.id}")
    payout.status = target
    if target == "approved":
        payout.approved_at = utcnow()
    db.add(
        PayoutApproval(
            payout_id=payout.id,
            approver_id=ctx.user_id,
            approver_name=ctx.user.name,
            approver_roles=ctx.principal.role_ids,
            at=utcnow(),
        )
    )
    signed = len(payout.approvals) + 1
    _event(db, payout, before, target, ctx.user_id, note or f"Signed by {ctx.user.name} ({signed} of 2)")
    ctx.audit(
        "commission",
        "approve_payout",
        "payout",
        payout.id,
        before={"status": before},
        after={"status": target, "approvals": signed},
        reason=note,
    )
    if target == "approved":
        notices = [Notice(uid, f"Payout {payout.id} is approved and ready to pay", "/admin/payouts") for uid in users_with_permission(db, "payout:approve")]
        notices += [Notice(uid, f"Payout {payout.id} ({money(payout.amount_cents)}) was approved", "/seller/payouts") for uid in vendor_staff_ids(db, payout.vendor_id)]
    else:
        notices = [
            Notice(uid, f"Payout {payout.id} needs a second signature", "/admin/payouts")
            for uid in users_with_permission(db, "payout:approve")
            if uid != ctx.user_id
        ]
    emit(db, "payout.approved" if target == "approved" else "payout.signed", {"payout_id": payout.id, "status": target}, notices)
    _refresh(db, payout)
    ctx.commit()
    return payout_out(db, payout, "platform", ctx.user_id)


def pay(ctx: Ctx, payout_id: str, reference: str, note: str | None) -> dict:
    db = ctx.db
    payout = db.get(Payout, payout_id, with_for_update=True)
    if payout is None:
        raise NotFound("Payout", payout_id)
    before = payout.status
    PAYOUT.check(before, "paid", f"Payout {payout.id}")
    balance = ledger.vendor_balance(db, payout.vendor_id)
    if balance < payout.amount_cents:
        raise Conflict(
            f"The shop's balance is {money(balance)}, which is less than this payout of {money(payout.amount_cents)}.",
            code="insufficient_balance",
        )
    now = utcnow()
    payout.status = "paid"
    payout.paid_at = now
    payout.reference = reference.strip()
    ledger.post_payout(db, payout, at=now)
    _event(db, payout, before, "paid", ctx.user_id, note or f"Bank transfer {payout.reference} sent")
    ctx.audit(
        "commission",
        "pay_payout",
        "payout",
        payout.id,
        before={"status": before},
        after={"status": "paid", "reference": payout.reference, "amount_cents": payout.amount_cents},
        reason=note,
    )
    emit(
        db,
        "payout.paid",
        {"payout_id": payout.id, "reference": payout.reference},
        [Notice(uid, f"Payout {payout.id} paid: {money(payout.amount_cents)} ({payout.reference})", "/seller/payouts") for uid in vendor_staff_ids(db, payout.vendor_id)],
    )
    _refresh(db, payout)
    ctx.commit()
    return payout_out(db, payout, "platform", ctx.user_id)
