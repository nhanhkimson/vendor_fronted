"""Cart quotes: per-vendor groups, shipping and coupon allocation. Pure functions, integer cents.

Policy (research FR-9.4, corrected Appendix B):
- A platform-funded discount is paid by the platform. It lowers what the
  customer pays but not the vendor's commission base or net.
- A vendor-funded discount is paid by that vendor. Commission is charged on
  the discounted amount.
- Shipping is a flat fee per vendor, passed through to the vendor and never
  commissionable.
- Discounts are split across vendors (and lines) by largest remainder, so the
  parts always add up to the whole cent amount.
"""

from dataclasses import dataclass, field

from app.core.util import money
from app.domain.money import allocate, percent_of


@dataclass
class QuoteLine:
    variant_id: str
    product_id: str
    vendor_id: str
    title: str
    sku: str
    size: str
    color: str
    unit_price_cents: int
    qty: int
    category_id: str | None = None
    image_url: str | None = None
    available: int = 0
    vendor_discount_cents: int = 0
    platform_discount_cents: int = 0

    @property
    def line_total_cents(self) -> int:
        return self.unit_price_cents * self.qty

    @property
    def commission_base_cents(self) -> int:
        return self.line_total_cents - self.vendor_discount_cents


@dataclass
class VendorGroup:
    vendor_id: str
    vendor_name: str
    shipping_cents: int
    lines: list[QuoteLine] = field(default_factory=list)
    vendor_discount_cents: int = 0
    platform_discount_cents: int = 0

    @property
    def items_subtotal_cents(self) -> int:
        return sum(line.line_total_cents for line in self.lines)

    @property
    def charged_cents(self) -> int:
        return (
            self.items_subtotal_cents
            + self.shipping_cents
            - self.vendor_discount_cents
            - self.platform_discount_cents
        )


@dataclass
class CouponTerms:
    code: str
    funded_by: str
    vendor_id: str | None
    discount_type: str
    percent_off: int | None
    amount_off_cents: int | None
    min_subtotal_cents: int
    vendor_name: str | None = None


@dataclass
class Quote:
    groups: list[VendorGroup]
    coupon: CouponTerms | None = None
    coupon_message: str | None = None

    @property
    def items_subtotal_cents(self) -> int:
        return sum(g.items_subtotal_cents for g in self.groups)

    @property
    def shipping_cents(self) -> int:
        return sum(g.shipping_cents for g in self.groups)

    @property
    def vendor_discount_cents(self) -> int:
        return sum(g.vendor_discount_cents for g in self.groups)

    @property
    def platform_discount_cents(self) -> int:
        return sum(g.platform_discount_cents for g in self.groups)

    @property
    def discount_cents(self) -> int:
        return self.vendor_discount_cents + self.platform_discount_cents

    @property
    def total_cents(self) -> int:
        return sum(g.charged_cents for g in self.groups)

    def to_json(self) -> dict:
        return {
            "coupon": self.coupon.__dict__ if self.coupon else None,
            "coupon_message": self.coupon_message,
            "groups": [
                {
                    "vendor_id": g.vendor_id,
                    "vendor_name": g.vendor_name,
                    "shipping_cents": g.shipping_cents,
                    "vendor_discount_cents": g.vendor_discount_cents,
                    "platform_discount_cents": g.platform_discount_cents,
                    "lines": [line.__dict__ for line in g.lines],
                }
                for g in self.groups
            ],
        }

    @classmethod
    def from_json(cls, data: dict) -> "Quote":
        groups = []
        for g in data["groups"]:
            lines = [QuoteLine(**line) for line in g["lines"]]
            groups.append(
                VendorGroup(
                    vendor_id=g["vendor_id"],
                    vendor_name=g["vendor_name"],
                    shipping_cents=g["shipping_cents"],
                    lines=lines,
                    vendor_discount_cents=g["vendor_discount_cents"],
                    platform_discount_cents=g["platform_discount_cents"],
                )
            )
        coupon = CouponTerms(**data["coupon"]) if data.get("coupon") else None
        return cls(groups=groups, coupon=coupon, coupon_message=data.get("coupon_message"))


def coupon_discount(terms: CouponTerms, groups: list[VendorGroup]) -> tuple[int, str | None]:
    eligible = [g for g in groups if terms.vendor_id is None or g.vendor_id == terms.vendor_id]
    eligible_subtotal = sum(g.items_subtotal_cents for g in eligible)
    if eligible_subtotal == 0:
        return 0, f"{terms.code} only applies to items from {terms.vendor_name or terms.vendor_id}"
    if eligible_subtotal < terms.min_subtotal_cents:
        scope = f" from {terms.vendor_name}" if terms.vendor_id else ""
        return 0, f"Spend at least {money(terms.min_subtotal_cents)} on items{scope} to use {terms.code}"
    if terms.discount_type == "percent":
        amount = percent_of(eligible_subtotal, terms.percent_off or 0)
    else:
        amount = min(terms.amount_off_cents or 0, eligible_subtotal)
    return amount, None


def build_quote(
    lines: list[QuoteLine],
    vendors: dict[str, tuple[str, int]],
    coupon: CouponTerms | None = None,
    coupon_problem: str | None = None,
) -> Quote:
    """`vendors` maps vendor id to (name, flat shipping fee in cents)."""
    groups: dict[str, VendorGroup] = {}
    for line in lines:
        line.vendor_discount_cents = 0
        line.platform_discount_cents = 0
        if line.vendor_id not in groups:
            name, shipping = vendors[line.vendor_id]
            groups[line.vendor_id] = VendorGroup(line.vendor_id, name, shipping)
        groups[line.vendor_id].lines.append(line)
    quote = Quote(groups=list(groups.values()))
    if coupon_problem:
        quote.coupon_message = coupon_problem
        return quote
    if coupon is None:
        return quote

    amount, problem = coupon_discount(coupon, quote.groups)
    if problem:
        quote.coupon_message = problem
        return quote
    eligible = [g for g in quote.groups if coupon.vendor_id is None or g.vendor_id == coupon.vendor_id]
    for group, share in zip(eligible, allocate(amount, [g.items_subtotal_cents for g in eligible])):
        line_shares = allocate(share, [line.line_total_cents for line in group.lines])
        if coupon.funded_by == "vendor":
            group.vendor_discount_cents = share
            for line, part in zip(group.lines, line_shares):
                line.vendor_discount_cents = part
        else:
            group.platform_discount_cents = share
            for line, part in zip(group.lines, line_shares):
                line.platform_discount_cents = part
    quote.coupon = coupon
    who = "the platform" if coupon.funded_by == "platform" else coupon.vendor_name or "the vendor"
    quote.coupon_message = f"{coupon.code} saves {money(amount)}, funded by {who}"
    return quote
