"""Load the demo world into an empty database.

Runs as the owner role, which bypasses row-level security. Orders go through
`place_order`, the same code the checkout uses, so the seeded commission lines
and ledger follow the real rules.
"""

import random
import shutil
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import Base, owner_engine, utcnow
from app.core.permissions import CATALOGUE, SYSTEM_ROLES
from app.core.security import hash_password
from app.core.util import slugify
from app.domain import ledger
from app.domain.pricing import CouponTerms, QuoteLine, build_quote
from app.models import (
    AuditLog,
    Category,
    CommissionRule,
    CommissionTier,
    Conversation,
    ConversationMessage,
    Coupon,
    Dispute,
    Notification,
    Order,
    Payout,
    PayoutApproval,
    PayoutEvent,
    Permission,
    Product,
    ProductTag,
    Review,
    ReviewEvent,
    Role,
    RolePermission,
    StockItem,
    SubOrder,
    SubOrderEvent,
    Tag,
    User,
    UserRole,
    Variant,
    Vendor,
    VendorDocument,
    VendorStatusEvent,
    Warehouse,
    WishlistItem,
)
from app.seed import data as D
from app.seed.files import sample_pdf
from app.services.placement import place_order, refresh_order_status

RULES_FROM = datetime(2025, 1, 1, tzinfo=UTC)
DESKTOP_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
PHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
FLOW = ["pending_acceptance", "accepted", "packing", "shipped", "delivered"]
STEP_OFFSET = {
    "accepted": timedelta(hours=4),
    "packing": timedelta(days=1),
    "shipped": timedelta(days=2),
    "delivered": timedelta(days=5),
}
STEP_NOTE = {
    "accepted": "Vendor accepted the order",
    "packing": "Packing started",
    "shipped": "Handed to the carrier",
    "delivered": "Delivered to the buyer",
}
CARRIERS = {"US": "USPS", "CA": "Canada Post", "UK": "Royal Mail"}
ADDRESSES = {
    "maya": "St. 240, Daun Penh, Phnom Penh, Cambodia",
    "theo": "Rua Augusta 112, Lisbon, Portugal",
    "priya": "12 Orchard Rd, Singapore",
}


def truncate_all(db: Session) -> None:
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    db.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
    db.execute(text("ALTER SEQUENCE order_number_seq RESTART WITH 1007"))


def clear_files() -> None:
    shutil.rmtree(settings.media_dir / "uploads", ignore_errors=True)
    shutil.rmtree(settings.private_dir, ignore_errors=True)
    (settings.media_dir / "uploads").mkdir(parents=True, exist_ok=True)
    settings.private_dir.mkdir(parents=True, exist_ok=True)


def reset_database(engine: Engine | None = None, now: datetime | None = None) -> dict[str, int]:
    engine = engine or owner_engine()
    clear_files()
    with Session(engine, autoflush=False, expire_on_commit=False) as db:
        truncate_all(db)
        counts = Seeder(db, now).run()
        db.commit()
    return counts


class Seeder:
    def __init__(self, db: Session, now: datetime | None = None):
        self.db = db
        self.now = now or utcnow()
        self.rng = random.Random(42)
        self.password_hash = hash_password("demo")
        self.users: dict[str, User] = {}
        self.vendors: dict[str, Vendor] = {}
        self.products: dict[str, Product] = {}
        self.variants: dict[str, Variant] = {}
        self.coupons: dict[str, Coupon] = {}
        self.audit_rows = 0

    def ago(self, days: float = 0, hours: float = 0, minutes: float = 0) -> datetime:
        return self.now - timedelta(days=days, hours=hours, minutes=minutes)

    def run(self) -> dict[str, int]:
        self.identity()
        self.supply()
        self.catalogue()
        self.rules_and_coupons()
        self.imported_reviews()
        self.orders()
        self.payouts()
        self.trust()
        self.notifications()
        self.audit_history()
        self.db.flush()
        return self.counts()

    # Identity ------------------------------------------------------------------

    def identity(self) -> None:
        db = self.db
        for i, (key, module, action, description) in enumerate(CATALOGUE):
            db.add(Permission(key=key, module=module, action=action, description=description, sort=i))
        for role_id, name, kind, _parent, locked, description, _grants in SYSTEM_ROLES:
            db.add(
                Role(
                    id=role_id,
                    name=name,
                    kind=kind,
                    description=description,
                    is_system=True,
                    is_locked=locked,
                    created_at=self.ago(days=400),
                )
            )
        db.flush()
        for role_id, _name, _kind, parent, _locked, _description, grants in SYSTEM_ROLES:
            if parent:
                db.get(Role, role_id).parent_id = parent
            for key in grants:
                db.add(
                    RolePermission(
                        role_id=role_id, permission_key=key, granted_by="system", granted_at=self.ago(days=400)
                    )
                )
        db.flush()

    def add_user(self, user_id: str, email: str, name: str, role: str, **fields) -> User:
        user = User(
            id=user_id,
            email=email,
            name=name,
            password_hash=self.password_hash,
            created_at=fields.pop("created_at", self.ago(days=self.rng.randint(120, 380))),
            **fields,
        )
        self.db.add(user)
        self.db.add(UserRole(user_id=user_id, role_id=role, assigned_by="system", assigned_at=user.created_at))
        self.users[user_id] = user
        return user

    # Vendors, documents, warehouses ---------------------------------------------

    def supply(self) -> None:
        db = self.db
        for i, tier in enumerate(D.TIERS):
            db.add(
                CommissionTier(
                    id=tier["id"],
                    name=tier["name"],
                    name_kh=tier["name_kh"],
                    min_sales=tier["min"],
                    max_sales=tier["max"],
                    sort=i,
                )
            )
        for wh_id, name, city in D.WAREHOUSES:
            db.add(Warehouse(id=wh_id, name=name, city=city))
        db.flush()

        for i, v in enumerate(D.VENDORS):
            status = v.get("status", "active")
            since = date.fromisoformat(v["since"])
            vendor = Vendor(
                id=v["id"],
                name=v["name"],
                slug=slugify(v["name"]),
                country=v["country"],
                city=v["city"],
                status=status,
                verified_at=self.ago(days=200 - i * 9) if status == "active" else None,
                tier_id=D.tier_for_sales(v["sales"]),
                warehouse_id=v["wh"],
                headline=v["headline"],
                about=v["about"],
                image_url=f"/media/shops/{v['id']}.jpg",
                hue=v["hue"],
                shipping_fee_cents=D.SHIPPING_FEE_CENTS[v["country"]],
                processing_days=self.rng.choice([1, 2, 3]),
                lifetime_sales=v["sales"],
                rating=v["rating"],
                rating_flag=v.get("rating_flag", "observed"),
                review_count=v["reviews"],
                since=since,
                response_hours=self.rng.choice([6, 12, 18, 24, 36]),
                catalog_size=v["catalog"],
                is_outlier=v.get("outlier", False),
                payout_account=f"acct_****{4100 + i * 37}" if status == "active" else None,
                created_at=datetime(since.year, since.month, since.day, tzinfo=UTC),
            )
            db.add(vendor)
            self.vendors[vendor.id] = vendor
        db.flush()

        for vendor in self.vendors.values():
            if vendor.status == "active":
                db.add(
                    VendorStatusEvent(
                        vendor_id=vendor.id,
                        from_status="under_review",
                        to_status="active",
                        actor_id="ava",
                        reason="Documents verified",
                        at=vendor.verified_at,
                    )
                )
            else:
                db.add(
                    VendorStatusEvent(
                        vendor_id=vendor.id,
                        from_status="draft",
                        to_status="under_review",
                        actor_id=None,
                        reason="Application submitted with documents",
                        at=self.ago(days=1, hours=3),
                    )
                )

        for doc_id, vendor_id, kind, name, status in D.DOCUMENTS:
            vendor = self.vendors[vendor_id]
            path = None
            if status in ("submitted", "verified"):
                path = f"documents/{vendor_id}/{doc_id}.pdf"
                file = settings.private_dir / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(
                    sample_pdf(
                        [
                            f"{name} - SAMPLE",
                            f"Shop: {vendor.name} ({vendor_id})",
                            "Demo document generated by the Bazaar seed.",
                            "Not a real identity document.",
                        ]
                    )
                )
            db.add(
                VendorDocument(
                    id=doc_id,
                    vendor_id=vendor_id,
                    kind=kind,
                    name=name,
                    status=status,
                    file_path=path,
                    original_filename=f"{kind}.pdf" if path else None,
                    content_type="application/pdf" if path else None,
                    uploaded_at=(vendor.verified_at or self.ago(days=1, hours=3)) - timedelta(days=2) if path else None,
                    reviewed_by="ava" if status == "verified" else None,
                    reviewed_at=vendor.verified_at if status == "verified" else None,
                )
            )

        for p in D.PERSONAS:
            self.add_user(
                p["id"],
                p["email"],
                p["name"],
                p["role"],
                blurb=p["blurb"],
                blurb_kh=p["blurb_kh"],
                city=p["city"],
                source=p.get("source", "organic"),
                vendor_id=p.get("vendor_id"),
                avatar_url=f"/media/people/{p['id']}.jpg" if p["avatar"] else None,
            )
        for user_id, name, city, source in D.HISTORY_CUSTOMERS:
            self.add_user(user_id, f"{user_id}@mail.local", name, "customer", city=city, source=source)
        db.flush()

    # Catalogue -----------------------------------------------------------------

    def catalogue(self) -> None:
        db = self.db
        for i, (cat_id, name, name_kh, slug, parent) in enumerate(D.CATEGORIES):
            db.add(Category(id=cat_id, name=name, name_kh=name_kh, slug=slug, parent_id=parent, sort=i))
        tag_ids = {}
        for tag_id, name in D.TAGS:
            db.add(Tag(id=tag_id, name=name, slug=name))
            tag_ids[name] = tag_id
        db.flush()

        for p in D.PRODUCTS:
            vendor = self.vendors[p["vendor"]]
            product = Product(
                id=p["id"],
                vendor_id=vendor.id,
                category_id=p["cat"],
                title=p["title"],
                description=p["blurb"],
                price_cents=p["price"] * 100,
                low_stock_threshold=p["low"],
                image_url=f"/media/products/{p['id']}.jpg",
                active=True,
                created_at=self.ago(days=self.rng.randint(60, 300)),
            )
            db.add(product)
            self.products[product.id] = product
            variants = p.get("variants") or [(f"{p['id']}-1", f"{p['id']}-STD", "One size", "Natural", p["stock"])]
            for variant_id, sku, size, color, _stock in variants:
                variant = Variant(
                    id=variant_id,
                    product_id=product.id,
                    vendor_id=vendor.id,
                    sku=sku,
                    size=size,
                    color=color,
                    created_at=product.created_at,
                )
                db.add(variant)
                self.variants[variant_id] = variant
            db.flush()
            for variant_id, *_rest, stock in variants:
                db.add(
                    StockItem(
                        variant_id=variant_id,
                        vendor_id=vendor.id,
                        warehouse_id=vendor.warehouse_id,
                        on_hand=stock,
                        reserved=0,
                    )
                )
            for tag in p["tags"]:
                db.add(ProductTag(product_id=product.id, tag_id=tag_ids[tag]))
        db.flush()

    # Commission rules and coupons -------------------------------------------------

    def rules_and_coupons(self) -> None:
        db = self.db
        for rule_id, name, target_type, target_id, rate, min_fee in D.COMMISSION_RULES:
            db.add(
                CommissionRule(
                    id=rule_id,
                    name=name,
                    target_type=target_type,
                    target_id=target_id,
                    rate_bps=rate,
                    min_fee_cents=min_fee,
                    effective_from=RULES_FROM,
                    created_by="system",
                    created_at=RULES_FROM,
                )
            )
        for code, funded_by, vendor_id, kind, value, min_dollars, start, days, limit, used, per_customer, flash, note in D.COUPONS:
            starts = self.now + timedelta(days=start) - (timedelta(hours=1) if flash else timedelta())
            coupon = Coupon(
                code=code,
                funded_by=funded_by,
                vendor_id=vendor_id,
                discount_type=kind,
                percent_off=value if kind == "percent" else None,
                amount_off_cents=value * 100 if kind == "fixed" else None,
                min_subtotal_cents=min_dollars * 100,
                starts_at=starts,
                ends_at=starts + timedelta(days=days),
                usage_limit=limit,
                per_customer_limit=per_customer,
                used_count=used,
                is_flash=flash,
                note=note,
                created_by="ava",
                created_at=starts - timedelta(days=2),
            )
            db.add(coupon)
            self.coupons[code] = coupon
        db.flush()

    def coupon_terms(self, code: str) -> CouponTerms:
        c = self.coupons[code]
        return CouponTerms(
            code=c.code,
            funded_by=c.funded_by,
            vendor_id=c.vendor_id,
            discount_type=c.discount_type,
            percent_off=c.percent_off,
            amount_off_cents=c.amount_off_cents,
            min_subtotal_cents=c.min_subtotal_cents,
            vendor_name=self.vendors[c.vendor_id].name if c.vendor_id else None,
        )

    # Reviews imported from the public sample ---------------------------------------

    def imported_reviews(self) -> None:
        for i, (review_id, source, rating, sentiment, theme, body, vendor_id, product_id, buyer) in enumerate(D.REVIEWS):
            created = self.ago(days=70 - i * 5)
            review = Review(
                id=review_id,
                product_id=product_id,
                vendor_id=vendor_id,
                buyer_id=buyer,
                sub_order_id=None,
                rating=rating,
                body=body,
                sentiment=sentiment,
                theme=theme,
                source=source,
                status="published",
                created_at=created,
            )
            if review_id == "R10":
                review.vendor_response = "Thank you so much, it made my week. Jess"
                review.vendor_responded_at = created + timedelta(days=1)
            self.db.add(review)
            self.db.add(
                ReviewEvent(review_id=review_id, from_status=None, to_status="published", actor_id=None, at=created)
            )
        self.db.flush()

    # Orders --------------------------------------------------------------------

    def quote_lines(self, lines: list[tuple[str, str | None, int]]) -> list[QuoteLine]:
        out = []
        for product_id, variant_id, qty in lines:
            product = self.products[product_id]
            variant = self.variants[variant_id or f"{product_id}-1"]
            out.append(
                QuoteLine(
                    variant_id=variant.id,
                    product_id=product.id,
                    vendor_id=product.vendor_id,
                    title=product.title,
                    sku=variant.sku,
                    size=variant.size,
                    color=variant.color,
                    unit_price_cents=product.price_cents,
                    qty=qty,
                    category_id=product.category_id,
                    image_url=product.image_url,
                )
            )
        return out

    def create_order(self, order_id: str, buyer_id: str, lines, placed_at: datetime, source: str, coupon: str | None):
        vendors = {v.id: (v.name, v.shipping_fee_cents) for v in self.vendors.values()}
        quote = build_quote(self.quote_lines(lines), vendors, self.coupon_terms(coupon) if coupon else None)
        if coupon and quote.coupon is None:
            raise ValueError(f"seed coupon {coupon} does not apply to {order_id}: {quote.coupon_message}")
        if coupon:
            self.coupons[coupon].used_count += 1
        buyer = self.users[buyer_id]
        return place_order(
            self.db,
            order_id=order_id,
            buyer_id=buyer_id,
            quote=quote,
            placed_at=placed_at,
            source=source,
            ship_name=buyer.name,
            ship_address=ADDRESSES.get(buyer_id, f"{buyer.city}"),
            card_last4="4242",
        )

    def vendor_actor(self, vendor_id: str) -> str | None:
        for user in self.users.values():
            if user.vendor_id == vendor_id:
                return user.id
        return None

    def progress(self, sub: SubOrder, target: str, placed_at: datetime, tracking: str | None = None) -> None:
        if target == sub.status:
            return
        vendor = self.vendors[sub.vendor_id]
        actor = self.vendor_actor(sub.vendor_id)
        previous = sub.status
        latest = self.now - timedelta(minutes=30)
        for step in FLOW[FLOW.index(previous) + 1 : FLOW.index(target) + 1]:
            at = min(placed_at + STEP_OFFSET[step], latest)
            if step == "accepted":
                sub.accepted_at = at
            elif step == "shipped":
                sub.shipped_at = at
                sub.carrier = CARRIERS.get(vendor.country, "USPS")
                sub.tracking_number = tracking or f"{vendor.country}-{self.rng.randint(10000, 99999)}"
            elif step == "delivered":
                sub.delivered_at = at
            self.db.add(
                SubOrderEvent(
                    sub_order_id=sub.id,
                    from_status=previous,
                    to_status=step,
                    actor_id=actor if step != "delivered" else sub.buyer_id,
                    actor_role="vendor" if step != "delivered" else "customer",
                    note=STEP_NOTE[step] + (f" ({sub.carrier} {sub.tracking_number})" if step == "shipped" else ""),
                    at=at,
                )
            )
            previous = step
        sub.status = target

    def orders(self) -> None:
        db = self.db
        active_products = [p for p in D.PRODUCTS if self.vendors[p["vendor"]].status == "active"]
        coupon_users: set[str] = set()
        history_buyers = [c[0] for c in D.HISTORY_CUSTOMERS]
        for n in range(30):
            buyer = self.rng.choice(history_buyers)
            placed = self.ago(days=125 - n * 3.5, hours=self.rng.randint(0, 10))
            picks = self.rng.sample(active_products, self.rng.choice([1, 1, 2, 2, 3]))
            lines = []
            for p in picks:
                variant = self.rng.choice(p["variants"])[0] if p.get("variants") else None
                lines.append((p["id"], variant, self.rng.choice([1, 1, 1, 2])))
            coupon = None
            subtotal = sum(self.products[pid].price_cents * qty for pid, _v, qty in lines)
            if self.users[buyer].source == "coupon" and buyer not in coupon_users and subtotal >= 2000:
                coupon = "WELCOME10"
                coupon_users.add(buyer)
            elif any(self.products[pid].vendor_id == "V06" for pid, _v, _q in lines) and n % 3 == 0:
                v06 = sum(self.products[pid].price_cents * q for pid, _v, q in lines if self.products[pid].vendor_id == "V06")
                coupon = "ANNE5" if v06 >= 1500 else None
            order = self.create_order(f"O-{900 + n:04d}", buyer, lines, placed, self.users[buyer].source, coupon)
            for sub in order.sub_orders:
                self.progress(sub, "delivered", placed)

        for spec in D.NAMED_ORDERS:
            placed = self.ago(days=spec["days_ago"], hours=2)
            order = self.create_order(
                spec["id"], spec["buyer"], spec["lines"], placed, spec["source"], spec.get("coupon")
            )
            for sub in order.sub_orders:
                self.progress(sub, spec["statuses"][sub.vendor_id], placed, spec.get("tracking", {}).get(sub.vendor_id))
        db.flush()

    # Payouts -------------------------------------------------------------------

    def payouts(self) -> None:
        db = self.db
        for vendor_id, cents in D.OPENING_BALANCES.items():
            ledger.post_opening_balance(db, vendor_id, cents, self.ago(days=45))
        for payout_id, vendor_id, amount, status, note in D.PAYOUTS:
            created = self.ago(days=9)
            payout = Payout(
                id=payout_id,
                vendor_id=vendor_id,
                amount_cents=amount,
                status=status,
                note=note,
                created_at=created,
                held_from_status="eligible" if status == "held_for_dispute" else None,
            )
            db.add(payout)
            db.flush()
            db.add(PayoutEvent(payout_id=payout_id, from_status=None, to_status="eligible", note="Statement closed", at=created))
            if status == "held_for_dispute":
                db.add(
                    PayoutEvent(
                        payout_id=payout_id,
                        from_status="eligible",
                        to_status="held_for_dispute",
                        note="Dispute D1 opened on O-1002-V07",
                        at=self.ago(days=2),
                    )
                )
            if status == "paid":
                steps = [
                    ("eligible", "requested", None, "Vendor requested the payout", self.ago(days=8)),
                    ("requested", "pending_second_approval", "daniel", "First approval: Daniel O.", self.ago(days=7, hours=20)),
                    ("pending_second_approval", "approved", "lin", "Second approval: Lin S.", self.ago(days=7, hours=18)),
                    ("approved", "paid", "daniel", "Bank transfer TRF-0909 sent", self.ago(days=7, hours=12)),
                ]
                for before, after, actor, event_note, at in steps:
                    db.add(PayoutEvent(payout_id=payout_id, from_status=before, to_status=after, actor_id=actor, note=event_note, at=at))
                for approver, at in (("daniel", steps[1][4]), ("lin", steps[2][4])):
                    user = self.users[approver]
                    db.add(
                        PayoutApproval(
                            payout_id=payout_id,
                            approver_id=approver,
                            approver_name=user.name,
                            approver_roles=[r.role_id for r in db.scalars(select(UserRole).where(UserRole.user_id == approver))],
                            at=at,
                        )
                    )
                payout.requested_at = steps[0][4]
                payout.approved_at = steps[2][4]
                payout.paid_at = steps[3][4]
                payout.reference = "TRF-0909"
                db.flush()
                ledger.post_payout(db, payout, at=payout.paid_at)
        db.flush()

    # Disputes, messages, wishlist ---------------------------------------------------

    def trust(self) -> None:
        db = self.db
        sub = db.get(SubOrder, "O-1002-V07")
        sub.in_dispute = True
        db.add(
            Dispute(
                id="D1",
                order_id="O-1002",
                sub_order_id=sub.id,
                buyer_id="maya",
                vendor_id="V07",
                reason="shipping_delay",
                note="Tracking US-77310 has not moved for over a week.",
                status="open",
                created_at=self.ago(days=2),
            )
        )
        conversations = [
            ("C-1", "maya", "V02", None, "Has my hair clip order shipped?", [("maya", "customer", "Hi! Has my order shipped yet? I need it by Friday.", 3)]),
            (
                "C-2",
                "maya",
                "V06",
                "O-1001",
                "Gift wrap for the coasters?",
                [
                    ("maya", "customer", "Could you gift-wrap the coasters? They are a birthday present.", 6),
                    ("jess", "vendor", "Of course. I'll add a linen ribbon before it ships. Jess", 5.8),
                ],
            ),
        ]
        for conv_id, buyer, vendor_id, order_id, subject, messages in conversations:
            last_at = self.ago(days=messages[-1][3])
            db.add(
                Conversation(
                    id=conv_id,
                    buyer_id=buyer,
                    vendor_id=vendor_id,
                    order_id=order_id,
                    subject=subject,
                    last_message_at=last_at,
                    last_sender_role=messages[-1][1],
                    message_count=len(messages),
                    created_at=self.ago(days=messages[0][3]),
                )
            )
            db.flush()
            for i, (sender, role, body, days) in enumerate(messages):
                db.add(
                    ConversationMessage(
                        id=f"{conv_id}-M{i + 1}",
                        conversation_id=conv_id,
                        buyer_id=buyer,
                        vendor_id=vendor_id,
                        sender_id=sender,
                        sender_name=self.users[sender].name,
                        sender_role=role,
                        body=body,
                        at=self.ago(days=days),
                    )
                )
        for product_id in ("P05", "P09", "P17"):
            db.add(WishlistItem(user_id="maya", product_id=product_id, created_at=self.ago(days=4)))

        for order in db.scalars(select(Order)).all():
            refresh_order_status(db, order, self.now, validate=False)
        db.flush()

    def notifications(self) -> None:
        items = [
            ("jess", "stock.low", "Quilted mug wrap is down to 1 unit", "Restock before it sells out.", "/seller/inventory", 0.2),
            ("jess", "order.placed", "New order O-1001-V06 to pack", "Wool felt coaster set, natural.", "/seller/orders", 6.9),
            ("daniel", "vendor.submitted", "SimplyCreativeJess submitted documents", "Review the application.", "/admin/vendors", 1.1),
            ("ava", "vendor.submitted", "SimplyCreativeJess submitted documents", "Review the application.", "/admin/vendors", 1.1),
            ("ava", "coupon.flash", "FLASH24 flash sale is live for 24 hours", "Platform-funded, 20% off orders over $30.", "/admin/coupons", 0.04),
            ("lin", "dispute.opened", "Dispute D1 opened on O-1002", "Shipping delay. Payout PAY-07 is on hold.", "/admin/disputes", 2),
            ("ava", "dispute.opened", "Dispute D1 opened on O-1002", "Shipping delay. Payout PAY-07 is on hold.", "/admin/disputes", 2),
            ("kein", "payout.eligible", "Payout PAY-04 is ready to request", "$9,200.00 is past the holdback.", "/seller/payouts", 1),
            ("maya", "order.delivered", "O-1003 was delivered", "Tell other buyers what you think.", "/account/orders/O-1003", 11),
            ("maya", "order.shipped", "O-1001-V03 is on its way", "Canada Post CA-44821.", "/account/orders/O-1001", 5),
        ]
        for i, (user_id, kind, title, body, link, days) in enumerate(items):
            created = self.ago(days=days)
            self.db.add(
                Notification(
                    id=f"N-SEED-{i + 1:02d}",
                    user_id=user_id,
                    kind=kind,
                    title=title,
                    body=body,
                    link=link,
                    read_at=created + timedelta(hours=2) if days > 6 else None,
                    created_at=created,
                )
            )
        self.db.flush()

    # Activity log ------------------------------------------------------------------

    def log(self, at: datetime, actor: str | None, module: str, action: str, resource_type: str, resource_id: str | None, **kw) -> None:
        user = self.users.get(actor) if actor else None
        persona = next((p for p in D.PERSONAS if p["id"] == actor), None)
        self.audit_rows += 1
        self.db.add(
            AuditLog(
                at=at,
                actor_id=actor,
                actor_name=user.name if user else "System",
                actor_roles=[r.role_id for r in self.db.scalars(select(UserRole).where(UserRole.user_id == actor))] if user else ["system"],
                actor_vendor_id=user.vendor_id if user else None,
                ip=kw.pop("ip", persona["ip"] if persona else "127.0.0.1"),
                user_agent=kw.pop("user_agent", PHONE_UA if user and user.id in ("maya", "theo", "priya") else DESKTOP_UA),
                module=module,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                request_id=f"seed-{self.audit_rows:04d}",
                outcome=kw.pop("outcome", "success"),
                **kw,
            )
        )

    def audit_history(self) -> None:
        db = self.db
        self.log(self.ago(days=50), "daniel", "commission", "impute_response_time", "vendor", "all", after={"method": "median of observed sellers", "vendors": 10})
        self.log(self.ago(days=45), "daniel", "vendor", "flag_outlier", "vendor", "V04", before={"is_outlier": False}, after={"is_outlier": True}, reason="220,578 sales is 30x the next shop")
        for vendor in sorted(self.vendors.values(), key=lambda v: v.verified_at or self.now):
            if vendor.verified_at:
                self.log(vendor.verified_at, "ava", "vendor", "verify", "vendor", vendor.id, before={"status": "under_review"}, after={"status": "active"})
        self.log(self.ago(days=1, hours=3), None, "vendor", "submit_application", "vendor", "V10", before={"status": "draft"}, after={"status": "under_review"})

        named = {spec["id"] for spec in D.NAMED_ORDERS}
        for order in db.scalars(select(Order).where(Order.id.in_(named)).order_by(Order.placed_at)).all():
            self.log(order.placed_at, order.buyer_id, "order", "create", "order", order.id, after={"total_cents": order.total_cents, "sub_orders": [s.id for s in order.sub_orders], "coupon": order.coupon_code})
            for sub in order.sub_orders:
                for event in sub.events[1:]:
                    self.log(event.at, event.actor_id, "order", "update_status", "sub_order", sub.id, before={"status": event.from_status}, after={"status": event.to_status, "tracking_number": sub.tracking_number if event.to_status == "shipped" else None})
        self.log(self.ago(days=8), None, "commission", "request_payout", "payout", "PAY-09", before={"status": "eligible"}, after={"status": "requested"})
        self.log(self.ago(days=7, hours=20), "daniel", "commission", "approve_payout", "payout", "PAY-09", before={"status": "requested"}, after={"status": "pending_second_approval", "approvals": 1})
        self.log(self.ago(days=7, hours=18), "lin", "commission", "approve_payout", "payout", "PAY-09", before={"status": "pending_second_approval"}, after={"status": "approved", "approvals": 2})
        self.log(self.ago(days=7, hours=12), "daniel", "commission", "pay_payout", "payout", "PAY-09", before={"status": "approved"}, after={"status": "paid", "reference": "TRF-0909"})
        self.log(self.ago(days=2), "maya", "order", "open_dispute", "dispute", "D1", after={"sub_order": "O-1002-V07", "reason": "shipping_delay"})
        self.log(self.ago(days=2), None, "commission", "hold_payout", "payout", "PAY-07", before={"status": "eligible"}, after={"status": "held_for_dispute"}, reason="Dispute D1 opened")
        self.log(self.ago(days=45), "jess", "customer", "respond_review", "review", "R10", after={"vendor_response": "Thank you so much, it made my week. Jess"})
        self.log(self.ago(hours=1, minutes=5), "ava", "coupon", "create", "coupon", "FLASH24", after={"percent_off": 20, "funded_by": "platform", "is_flash": True})
        self.log(self.ago(minutes=40), "kein", "order", "read", "sub_order", "O-1001-V06", outcome="denied", reason="Not visible to this vendor (tenant isolation)")
        db.flush()

    def counts(self) -> dict[str, int]:
        models = {
            "users": User,
            "vendors": Vendor,
            "products": Product,
            "orders": Order,
            "sub_orders": SubOrder,
            "reviews": Review,
            "payouts": Payout,
            "audit_logs": AuditLog,
        }
        return {name: int(self.db.scalar(select(func.count()).select_from(model)) or 0) for name, model in models.items()}
