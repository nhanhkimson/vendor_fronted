"""Double-entry ledger (research section 6.3, invariant 5 as amended).

Accounts: cash (platform bank clearing), vendor_payable (per vendor),
platform_revenue (commission) and platform_promotions (platform-funded
discounts). Per sub-order:

    vendor_net + commission = charged + platform_funded_discount
"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import utcnow
from app.models.finance import LedgerEntry, Payout
from app.models.order import Order, SubOrder

Entry = tuple[str, str | None, int, int, str]


def post(
    db: Session,
    journal_id: str,
    entries: list[Entry],
    *,
    at: datetime | None = None,
    order_id: str | None = None,
    sub_order_id: str | None = None,
    payout_id: str | None = None,
) -> None:
    entries = [e for e in entries if e[2] or e[3]]
    debits = sum(e[2] for e in entries)
    credits = sum(e[3] for e in entries)
    if debits != credits:
        raise ValueError(f"journal {journal_id} does not balance: {debits} != {credits}")
    for account, vendor_id, debit, credit, memo in entries:
        db.add(
            LedgerEntry(
                journal_id=journal_id,
                account=account,
                vendor_id=vendor_id,
                debit_cents=debit,
                credit_cents=credit,
                order_id=order_id,
                sub_order_id=sub_order_id,
                payout_id=payout_id,
                memo=memo,
                created_at=at or utcnow(),
            )
        )


def _sub_order_entries(sub: SubOrder) -> list[Entry]:
    return [
        ("cash", None, sub.charged_cents, 0, f"Customer payment for {sub.id}"),
        ("platform_promotions", None, sub.platform_discount_cents, 0, f"Platform-funded discount on {sub.id}"),
        ("vendor_payable", sub.vendor_id, 0, sub.vendor_net_cents, f"Owed to vendor for {sub.id}"),
        ("platform_revenue", None, 0, sub.commission_cents, f"Commission on {sub.id}"),
    ]


def post_order(db: Session, order: Order, subs: list[SubOrder], at: datetime) -> None:
    for sub in subs:
        post(db, f"J-{sub.id}", _sub_order_entries(sub), at=at, order_id=order.id, sub_order_id=sub.id)


def post_refund(db: Session, sub: SubOrder, reason: str, at: datetime | None = None) -> None:
    reversed_entries = [
        (account, vendor_id, credit, debit, f"Refund: {reason}")
        for account, vendor_id, debit, credit, _ in _sub_order_entries(sub)
    ]
    post(db, f"J-REF-{sub.id}", reversed_entries, at=at, order_id=sub.order_id, sub_order_id=sub.id)


def post_payout(db: Session, payout: Payout, at: datetime | None = None) -> None:
    post(
        db,
        f"J-{payout.id}",
        [
            ("vendor_payable", payout.vendor_id, payout.amount_cents, 0, f"Payout {payout.id}"),
            ("cash", None, 0, payout.amount_cents, f"Bank transfer {payout.reference or payout.id}"),
        ],
        at=at,
        payout_id=payout.id,
    )


def post_opening_balance(db: Session, vendor_id: str, cents: int, at: datetime) -> None:
    post(
        db,
        f"J-OPEN-{vendor_id}",
        [
            ("cash", None, cents, 0, "Opening balance: sales before this period"),
            ("vendor_payable", vendor_id, 0, cents, "Opening balance owed to vendor"),
        ],
        at=at,
    )


def vendor_balance(db: Session, vendor_id: str) -> int:
    value = db.scalar(
        select(func.coalesce(func.sum(LedgerEntry.credit_cents - LedgerEntry.debit_cents), 0)).where(
            LedgerEntry.account == "vendor_payable", LedgerEntry.vendor_id == vendor_id
        )
    )
    return int(value or 0)


def trial_balance(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            LedgerEntry.account,
            func.sum(LedgerEntry.debit_cents),
            func.sum(LedgerEntry.credit_cents),
        ).group_by(LedgerEntry.account)
    ).all()
    return [
        {"account": a, "debit_cents": int(d or 0), "credit_cents": int(c or 0), "balance_cents": int((d or 0) - (c or 0))}
        for a, d, c in sorted(rows)
    ]


def unbalanced_journals(db: Session) -> list[str]:
    rows = db.execute(
        select(LedgerEntry.journal_id)
        .group_by(LedgerEntry.journal_id)
        .having(func.sum(LedgerEntry.debit_cents) != func.sum(LedgerEntry.credit_cents))
    ).all()
    return [r[0] for r in rows]
