"""M7 payouts: holdback, dispute freeze, two-person approval."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import system_scope, utcnow
from app.domain.states import PAYOUT
from app.models import Dispute, Payout, PayoutEvent

FREEZABLE = ("eligible", "requested", "pending_second_approval", "approved")


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
