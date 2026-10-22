"""M7 commission rules. Editing a rate closes the current version and opens the next one.

Orders already placed keep the commission line frozen at placement, so a rate
change never rewrites history.
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import utcnow
from app.core.deps import Ctx
from app.core.errors import Conflict, NotFound, Unprocessable
from app.core.util import new_id
from app.models import Category, CommissionLine, CommissionRule, CommissionTier, LedgerEntry, Vendor

OPEN = CommissionRule.effective_to.is_(None)


def _labels(db: Session):
    vendors = {v.id: v.name for v in db.scalars(select(Vendor)).all()}
    tiers = {t.id: t.name for t in db.scalars(select(CommissionTier)).all()}
    categories = {c.id: c.name for c in db.scalars(select(Category)).all()}

    def label(rule: CommissionRule) -> str:
        if rule.target_type == "platform":
            return "Every shop"
        table = {"tier": tiers, "category": categories, "vendor": vendors}[rule.target_type]
        return table.get(rule.target_id, rule.target_id)

    return label


def _check_target(db: Session, target_type: str, target_id: str) -> None:
    if target_type == "platform":
        if target_id != "*":
            raise Unprocessable("The platform default targets `*`", code="bad_target")
        return
    model = {"tier": CommissionTier, "category": Category, "vendor": Vendor}[target_type]
    if db.get(model, target_id) is None:
        raise NotFound(target_type.capitalize(), target_id)


def rule_out(rule: CommissionRule, label, replaced: dict[str, str]) -> dict:
    return {
        "id": rule.id,
        "name": rule.name,
        "target_type": rule.target_type,
        "target_id": rule.target_id,
        "target_label": label(rule),
        "rate_bps": rule.rate_bps,
        "min_fee_cents": rule.min_fee_cents,
        "version": rule.version,
        "supersedes_id": rule.supersedes_id,
        "replaced_by": replaced.get(rule.id),
        "effective_from": rule.effective_from,
        "effective_to": rule.effective_to,
        "open": rule.effective_to is None,
        "created_by": rule.created_by,
        "created_at": rule.created_at,
    }


def list_rules(db: Session, include_ended: bool) -> list[dict]:
    query = select(CommissionRule).order_by(CommissionRule.target_type, CommissionRule.target_id, CommissionRule.version)
    rules = list(db.scalars(query).all())
    replaced = {r.supersedes_id: r.id for r in rules if r.supersedes_id}
    label = _labels(db)
    rows = [rule_out(r, label, replaced) for r in rules]
    if not include_ended:
        rows = [r for r in rows if r["open"]]
    return rows


def _open_for(db: Session, target_type: str, target_id: str) -> CommissionRule | None:
    return db.scalar(
        select(CommissionRule).where(
            CommissionRule.target_type == target_type,
            CommissionRule.target_id == target_id,
            OPEN,
        )
    )


def create_rule(ctx: Ctx, body) -> dict:
    db = ctx.db
    _check_target(db, body.target_type, body.target_id)
    existing = _open_for(db, body.target_type, body.target_id)
    if existing:
        raise Conflict(
            f"{existing.name} (version {existing.version}) is already active for this target. Revise it to change the rate.",
            code="rule_exists",
            details={"rule_id": existing.id},
        )
    now = utcnow()
    rule = CommissionRule(
        id=new_id("CR", 8),
        name=body.name.strip(),
        target_type=body.target_type,
        target_id=body.target_id,
        rate_bps=body.rate_bps,
        min_fee_cents=body.min_fee_cents,
        version=1,
        effective_from=now,
        created_by=ctx.user_id,
        created_at=now,
    )
    db.add(rule)
    ctx.audit(
        "commission",
        "create_rule",
        "commission_rule",
        rule.id,
        after={"target": f"{rule.target_type}:{rule.target_id}", "rate_bps": rule.rate_bps, "min_fee_cents": rule.min_fee_cents},
    )
    ctx.commit()
    return rule_out(rule, _labels(db), {})


def _get(db: Session, rule_id: str) -> CommissionRule:
    rule = db.get(CommissionRule, rule_id)
    if rule is None:
        raise NotFound("Commission rule", rule_id)
    return rule


def revise_rule(ctx: Ctx, rule_id: str, body) -> dict:
    """Close the open version and insert the next one. Past orders keep the old rate."""
    db = ctx.db
    old = _get(db, rule_id)
    if old.effective_to is not None:
        raise Conflict("This version has already ended. Revise the current version instead.", code="rule_closed")
    now = utcnow()
    old.effective_to = now
    # Close the current version before the next one is inserted, so the target never has two open rules.
    db.flush()
    rule = CommissionRule(
        id=new_id("CR", 8),
        name=(body.name or old.name).strip(),
        target_type=old.target_type,
        target_id=old.target_id,
        rate_bps=body.rate_bps,
        min_fee_cents=body.min_fee_cents,
        version=old.version + 1,
        supersedes_id=old.id,
        effective_from=now,
        created_by=ctx.user_id,
        created_at=now,
    )
    db.add(rule)
    ctx.audit(
        "commission",
        "revise_rule",
        "commission_rule",
        rule.id,
        before={"id": old.id, "version": old.version, "rate_bps": old.rate_bps, "min_fee_cents": old.min_fee_cents},
        after={"version": rule.version, "rate_bps": rule.rate_bps, "min_fee_cents": rule.min_fee_cents, "frozen": "existing orders unchanged"},
    )
    ctx.commit()
    return rule_out(rule, _labels(db), {})


def end_rule(ctx: Ctx, rule_id: str, reason: str) -> dict:
    db = ctx.db
    rule = _get(db, rule_id)
    if rule.effective_to is not None:
        raise Conflict("This rule has already ended", code="rule_closed")
    if rule.target_type == "platform":
        raise Conflict(
            "The platform default can be revised but not removed. Every order needs a fallback rate.",
            code="platform_rule",
        )
    rule.effective_to = utcnow()
    ctx.audit(
        "commission",
        "end_rule",
        "commission_rule",
        rule.id,
        before={"effective_to": None, "rate_bps": rule.rate_bps},
        after={"effective_to": rule.effective_to},
        reason=reason,
    )
    ctx.commit()
    return rule_out(rule, _labels(db), {})


def _period(column, date_from: date | None, date_to: date | None):
    clauses = []
    if date_from:
        clauses.append(column >= datetime.combine(date_from, time.min, utcnow().tzinfo))
    if date_to:
        clauses.append(column < datetime.combine(date_to + timedelta(days=1), time.min, utcnow().tzinfo))
    return clauses


def list_lines(db: Session, vendor_id: str | None, date_from: date | None, date_to: date | None) -> list[dict]:
    query = select(CommissionLine).order_by(CommissionLine.computed_at.desc()).limit(300)
    if vendor_id:
        query = query.where(CommissionLine.vendor_id == vendor_id)
    for clause in _period(CommissionLine.computed_at, date_from, date_to):
        query = query.where(clause)
    lines = db.scalars(query).all()
    names = {v.id: v.name for v in db.scalars(select(Vendor).where(Vendor.id.in_({ln.vendor_id for ln in lines} or {""}))).all()}
    return [
        {
            "id": ln.id,
            "order_line_id": ln.order_line_id,
            "sub_order_id": ln.sub_order_id,
            "order_id": ln.order_id,
            "vendor_id": ln.vendor_id,
            "vendor_name": names.get(ln.vendor_id, ln.vendor_id),
            "rule_id": ln.rule_id,
            "rule_version": ln.rule_version,
            "rule_target": ln.rule_target,
            "rate_bps": ln.rate_bps,
            "min_fee_cents": ln.min_fee_cents,
            "base_cents": ln.base_cents,
            "fee_cents": ln.fee_cents,
            "computed_at": ln.computed_at,
        }
        for ln in lines
    ]


def list_ledger(db: Session, vendor_id: str | None, account: str | None, date_from: date | None, date_to: date | None) -> list[dict]:
    query = select(LedgerEntry).order_by(LedgerEntry.created_at.desc()).limit(300)
    if vendor_id:
        query = query.where(LedgerEntry.vendor_id == vendor_id)
    if account:
        query = query.where(LedgerEntry.account == account)
    for clause in _period(LedgerEntry.created_at, date_from, date_to):
        query = query.where(clause)
    return [
        {
            "id": entry.id,
            "journal_id": entry.journal_id,
            "account": entry.account,
            "vendor_id": entry.vendor_id,
            "debit_cents": entry.debit_cents,
            "credit_cents": entry.credit_cents,
            "order_id": entry.order_id,
            "sub_order_id": entry.sub_order_id,
            "payout_id": entry.payout_id,
            "memo": entry.memo,
            "created_at": entry.created_at,
        }
        for entry in db.scalars(query).all()
    ]
