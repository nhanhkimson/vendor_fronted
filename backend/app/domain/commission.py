"""M7 commission rule resolution.

Precedence (research FR-7.1): vendor override, then the vendor's tier, then
the category (nearest first), then the platform default. Only rules whose
effective window contains the order time are considered, so a rate change
never alters an order that was already placed.
"""

from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.errors import Conflict
from app.models.catalogue import Category
from app.models.finance import CommissionRule


def active_rules(db: Session, at: datetime) -> list[CommissionRule]:
    return list(
        db.scalars(
            select(CommissionRule)
            .where(
                CommissionRule.effective_from <= at,
                or_(CommissionRule.effective_to.is_(None), CommissionRule.effective_to > at),
            )
            .order_by(CommissionRule.effective_from.desc())
        ).all()
    )


def category_chain(db: Session, category_id: str | None) -> list[str]:
    chain: list[str] = []
    seen: set[str] = set()
    current = category_id
    while current and current not in seen:
        chain.append(current)
        seen.add(current)
        category = db.get(Category, current)
        current = category.parent_id if category else None
    return chain


def pick_rule(
    rules: list[CommissionRule], vendor_id: str, tier_id: str, chain: list[str]
) -> CommissionRule:
    index: dict[tuple[str, str], CommissionRule] = {}
    for rule in rules:
        index.setdefault((rule.target_type, rule.target_id), rule)
    candidates = [("vendor", vendor_id), ("tier", tier_id), *[("category", c) for c in chain], ("platform", "*")]
    for key in candidates:
        if key in index:
            return index[key]
    raise Conflict("No commission rule is active. Restore the platform default rule.", code="no_rule")


def describe(rule: CommissionRule) -> str:
    return f"{rule.target_type}:{rule.target_id}"
