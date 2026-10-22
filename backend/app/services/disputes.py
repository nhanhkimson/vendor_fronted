"""M6/M8 disputes: a buyer flags one sub-order, support refunds or rejects.

While a dispute is open the vendor's unpaid payouts are frozen (FR-7.6) and the
parent order cannot complete.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import system_scope, utcnow
from app.core.deps import Ctx
from app.core.errors import Conflict, NotFound
from app.core.util import money, new_id
from app.domain import ledger
from app.domain.states import DISPUTE, SUB_ORDER
from app.models import Dispute, Order, SubOrder, SubOrderEvent
from app.services import payouts
from app.services.events import Notice, emit, vendor_staff_ids
from app.services.fulfilment import dispute_out, dispute_window_open, notify_support
from app.services.placement import refresh_order_status

REASONS = {
    "shipping_delay": "Shipping delay",
    "not_as_described": "Not as described",
    "damaged": "Arrived damaged",
    "never_arrived": "Never arrived",
    "other": "Other",
}


def open_dispute(ctx: Ctx, sub: SubOrder, reason: str, note: str) -> dict:
    db = ctx.db
    if db.scalar(select(Dispute.id).where(Dispute.sub_order_id == sub.id)):
        raise Conflict("A dispute was already opened for this order", code="dispute_exists")
    if not dispute_window_open(sub):
        raise Conflict(
            "Disputes can be opened once the order has shipped and up to 7 days after delivery",
            code="dispute_window_closed",
        )
    dispute = Dispute(
        id=new_id("D", 8),
        order_id=sub.order_id,
        sub_order_id=sub.id,
        buyer_id=sub.buyer_id,
        vendor_id=sub.vendor_id,
        reason=reason,
        note=note.strip(),
        status="open",
        created_at=utcnow(),
    )
    with system_scope(db):
        db.add(dispute)
        sub.in_dispute = True
        db.add(
            SubOrderEvent(
                sub_order_id=sub.id,
                from_status=sub.status,
                to_status=sub.status,
                actor_id=ctx.user_id,
                actor_role="customer",
                note=f"Dispute opened: {REASONS[reason]}",
                at=utcnow(),
            )
        )
        held = payouts.hold_for_dispute(db, sub.vendor_id, dispute.id, ctx.user_id)
    ctx.audit(
        "order",
        "open_dispute",
        "dispute",
        dispute.id,
        after={"sub_order_id": sub.id, "reason": reason, "held_payouts": held},
        reason=note,
    )
    notices = [Notice(uid, f"Dispute {dispute.id} opened on {sub.id}: {REASONS[reason]}", "/seller/orders") for uid in vendor_staff_ids(db, sub.vendor_id)]
    notices += notify_support(db, f"New dispute {dispute.id} on {sub.id} ({money(sub.charged_cents)})", "/admin/disputes")
    emit(db, "dispute.opened", {"dispute_id": dispute.id, "sub_order_id": sub.id, "held_payouts": held}, notices)
    ctx.commit()
    return dispute_out(db, dispute)


def list_disputes(ctx: Ctx, status: str | None) -> list[dict]:
    query = select(Dispute).order_by(Dispute.created_at.desc())
    if status:
        query = query.where(Dispute.status == status)
    if ctx.scope == "vendor":
        query = query.where(Dispute.vendor_id == ctx.vendor_id)
    elif ctx.scope == "customer":
        query = query.where(Dispute.buyer_id == ctx.user_id)
    return [dispute_out(ctx.db, d) for d in ctx.db.scalars(query).all()]


def get(db: Session, dispute_id: str) -> Dispute:
    dispute = db.get(Dispute, dispute_id)
    if dispute is None:
        raise NotFound("Dispute", dispute_id)
    return dispute


def resolve(ctx: Ctx, dispute_id: str, outcome: str, note: str) -> dict:
    db = ctx.db
    dispute = db.get(Dispute, dispute_id, with_for_update=True)
    if dispute is None:
        raise NotFound("Dispute", dispute_id)
    target = "resolved_refund" if outcome == "refund" else "resolved_rejected"
    DISPUTE.check(dispute.status, target, f"Dispute {dispute.id}")
    sub = db.get(SubOrder, dispute.sub_order_id)
    with system_scope(db):
        dispute.status = target
        dispute.resolution_note = note.strip()
        dispute.resolved_by = ctx.user_id
        dispute.resolved_at = utcnow()
        sub.in_dispute = False
        if outcome == "refund":
            SUB_ORDER.check(sub.status, "refunded", f"Order {sub.id}")
            before = sub.status
            sub.status = "refunded"
            sub.refunded_cents = sub.charged_cents
            ledger.post_refund(db, sub, f"Dispute {dispute.id} refunded")
            db.add(SubOrderEvent(sub_order_id=sub.id, from_status=before, to_status="refunded", actor_id=ctx.user_id, actor_role="staff", note=f"Refunded after dispute {dispute.id}: {note}", at=utcnow()))
        else:
            db.add(SubOrderEvent(sub_order_id=sub.id, from_status=sub.status, to_status=sub.status, actor_id=ctx.user_id, actor_role="staff", note=f"Dispute {dispute.id} rejected: {note}", at=utcnow()))
        refresh_order_status(db, db.get(Order, sub.order_id))
    released = payouts.release_holds(db, dispute.vendor_id, ctx.user_id, f"Dispute {dispute.id} resolved")
    ctx.audit(
        "order",
        "resolve_dispute",
        "dispute",
        dispute.id,
        before={"status": "open"},
        after={"status": target, "refunded_cents": sub.refunded_cents if outcome == "refund" else 0, "released_payouts": released},
        reason=note,
    )
    buyer_title = (
        f"Dispute {dispute.id}: {money(sub.charged_cents)} refunded to your card"
        if outcome == "refund"
        else f"Dispute {dispute.id} was closed without a refund"
    )
    notices = [Notice(dispute.buyer_id, buyer_title, f"/account/orders/{dispute.order_id}", note)]
    notices += [Notice(uid, f"Dispute {dispute.id} {('refunded' if outcome == 'refund' else 'rejected')}", "/seller/orders", note) for uid in vendor_staff_ids(db, dispute.vendor_id)]
    emit(db, "dispute.resolved", {"dispute_id": dispute.id, "outcome": outcome, "released_payouts": released}, notices)
    ctx.commit()
    return dispute_out(db, dispute)
