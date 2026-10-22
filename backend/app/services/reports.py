"""M10 reports. Vendors only ever see their own shop; staff can filter to one shop."""

import csv
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from io import StringIO

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.db import utcnow
from app.core.deps import Ctx
from app.models import (
    CommissionLine,
    Conversation,
    Dispute,
    Notification,
    Order,
    Payout,
    Product,
    Review,
    Role,
    SubOrder,
    User,
    UserRole,
    Vendor,
    WishlistItem,
)
from app.services.payouts import position
from app.services.present import is_low

CLOSED = ("cancelled", "refunded")
REPORTS = ("sales", "revenue", "products", "sources", "commission")


def _bounds(date_from: date | None, date_to: date | None) -> tuple[datetime | None, datetime | None]:
    start = datetime.combine(date_from, time.min, utcnow().tzinfo) if date_from else None
    end = datetime.combine(date_to + timedelta(days=1), time.min, utcnow().tzinfo) if date_to else None
    return start, end


def _subs(db: Session, vendor_id: str | None, date_from: date | None, date_to: date | None) -> list[SubOrder]:
    start, end = _bounds(date_from, date_to)
    query = select(SubOrder).options(selectinload(SubOrder.order)).order_by(SubOrder.created_at)
    if vendor_id:
        query = query.where(SubOrder.vendor_id == vendor_id)
    if start:
        query = query.where(SubOrder.created_at >= start)
    if end:
        query = query.where(SubOrder.created_at < end)
    return list(db.scalars(query).all())


def overview(db: Session, vendor_id: str | None, date_from: date | None, date_to: date | None) -> dict:
    subs = _subs(db, vendor_id, date_from, date_to)
    vendors = {v.id: v.name for v in db.scalars(select(Vendor)).all()}
    live = [s for s in subs if s.status not in CLOSED]
    gmv = sum(s.charged_cents for s in subs)
    parent_ids = {s.order_id for s in subs}
    by_vendor: dict[str, dict] = {}
    by_day: dict[str, dict] = defaultdict(lambda: {"gmv_cents": 0, "orders": 0, "commission_cents": 0})
    by_source: dict[str, dict] = defaultdict(lambda: {"orders": 0, "gmv_cents": 0, "customers": 0})
    products: dict[str, dict] = {}
    counted_orders: set[str] = set()
    for sub in subs:
        row = by_vendor.setdefault(
            sub.vendor_id,
            {"vendor_id": sub.vendor_id, "vendor_name": vendors.get(sub.vendor_id, sub.vendor_id), "orders": 0, "gmv_cents": 0, "refunded_cents": 0, "commission_cents": 0, "net_cents": 0},
        )
        row["orders"] += 1
        row["gmv_cents"] += sub.charged_cents
        row["refunded_cents"] += sub.refunded_cents
        day = by_day[sub.created_at.date().isoformat()]
        day["gmv_cents"] += sub.charged_cents
        day["orders"] += 1
        source = (sub.order.source if sub.order else None) or "organic"
        if sub.order_id not in counted_orders:
            by_source[source]["orders"] += 1
            counted_orders.add(sub.order_id)
        by_source[source]["gmv_cents"] += sub.charged_cents
        if sub.status in CLOSED:
            continue
        row["commission_cents"] += sub.commission_cents
        row["net_cents"] += sub.vendor_net_cents
        day["commission_cents"] += sub.commission_cents
        for line in sub.lines:
            rank = products.setdefault(
                line.product_id,
                {"product_id": line.product_id, "title": line.title, "vendor_id": sub.vendor_id, "vendor_name": vendors.get(sub.vendor_id, sub.vendor_id), "units": 0, "revenue_cents": 0},
            )
            rank["units"] += line.qty
            rank["revenue_cents"] += line.line_total_cents

    sub_ids = [s.id for s in live]
    commission: dict[str, dict] = {}
    if sub_ids:
        for line in db.scalars(select(CommissionLine).where(CommissionLine.sub_order_id.in_(sub_ids))).all():
            bucket = commission.setdefault(line.rule_target, {"rule_target": line.rule_target, "lines": 0, "base_cents": 0, "fee_cents": 0})
            bucket["lines"] += 1
            bucket["base_cents"] += line.base_cents
            bucket["fee_cents"] += line.fee_cents

    acquisition = []
    if vendor_id is None:
        rows = db.execute(
            select(User.source, func.count(User.id))
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(Role.kind == "customer")
            .group_by(User.source)
        ).all()
        acquisition = [{"source": source or "organic", "orders": 0, "gmv_cents": 0, "customers": int(n)} for source, n in rows]

    orders = len(parent_ids)
    return {
        "vendor_id": vendor_id,
        "date_from": date_from,
        "date_to": date_to,
        "generated_at": utcnow(),
        "totals": {
            "orders": orders,
            "sub_orders": len(subs),
            "gmv_cents": gmv,
            "refunded_cents": sum(s.refunded_cents for s in subs),
            "commission_cents": sum(s.commission_cents for s in live),
            "net_cents": sum(s.vendor_net_cents for s in live),
            "aov_cents": gmv // orders if orders else 0,
        },
        "sales_by_vendor": sorted(by_vendor.values(), key=lambda r: -r["gmv_cents"]),
        "revenue": [{"date": day, **values} for day, values in sorted(by_day.items())],
        "top_products": sorted(products.values(), key=lambda r: -r["revenue_cents"])[:8],
        "sources": [{"source": name, **values} for name, values in sorted(by_source.items())],
        "acquisition": acquisition,
        "commission": sorted(commission.values(), key=lambda r: -r["fee_cents"]),
    }


def _csv(header: list[str], rows: list[list]) -> str:
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue()


def export_csv(db: Session, report: str, vendor_id: str | None, date_from: date | None, date_to: date | None) -> str:
    data = overview(db, vendor_id, date_from, date_to)
    if report == "sales":
        return _csv(
            ["vendor_id", "vendor", "orders", "gmv_cents", "refunded_cents", "commission_cents", "net_cents"],
            [[r["vendor_id"], r["vendor_name"], r["orders"], r["gmv_cents"], r["refunded_cents"], r["commission_cents"], r["net_cents"]] for r in data["sales_by_vendor"]],
        )
    if report == "revenue":
        return _csv(
            ["date", "orders", "gmv_cents", "commission_cents"],
            [[r["date"], r["orders"], r["gmv_cents"], r["commission_cents"]] for r in data["revenue"]],
        )
    if report == "products":
        return _csv(
            ["product_id", "title", "vendor", "units", "revenue_cents"],
            [[r["product_id"], r["title"], r["vendor_name"], r["units"], r["revenue_cents"]] for r in data["top_products"]],
        )
    if report == "sources":
        return _csv(
            ["source", "orders", "gmv_cents", "customers"],
            [[r["source"], r["orders"], r["gmv_cents"], r["customers"]] for r in data["sources"]]
            + [["signup:" + r["source"], 0, 0, r["customers"]] for r in data["acquisition"]],
        )
    return _csv(
        ["rule", "lines", "base_cents", "fee_cents"],
        [[r["rule_target"], r["lines"], r["base_cents"], r["fee_cents"]] for r in data["commission"]],
    )


def _unread(db: Session, user_id: str) -> int:
    return int(
        db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == user_id, Notification.read_at.is_(None)))
        or 0
    )


def summary(ctx: Ctx) -> dict:
    db = ctx.db
    if ctx.scope == "customer":
        orders = db.scalars(select(Order).where(Order.buyer_id == ctx.user_id)).all()
        return {
            "area": "customer",
            "orders": len(orders),
            "open_orders": sum(1 for o in orders if o.status not in ("completed", "cancelled", "refunded")),
            "wishlist": int(db.scalar(select(func.count()).select_from(WishlistItem).where(WishlistItem.user_id == ctx.user_id)) or 0),
            "unread": _unread(db, ctx.user_id),
            "open_disputes": int(db.scalar(select(func.count()).select_from(Dispute).where(Dispute.buyer_id == ctx.user_id, Dispute.status == "open")) or 0),
        }
    if ctx.scope == "vendor":
        subs = db.scalars(select(SubOrder).where(SubOrder.vendor_id == ctx.vendor_id)).all()
        products = db.scalars(select(Product).where(Product.vendor_id == ctx.vendor_id, Product.archived_at.is_(None), Product.active.is_(True))).all()
        pos = position(db, ctx.vendor_id)
        return {
            "area": "vendor",
            "orders": len(subs),
            "open_orders": sum(1 for s in subs if s.status in ("pending_acceptance", "accepted", "packing")),
            "unread": _unread(db, ctx.user_id),
            "open_disputes": int(db.scalar(select(func.count()).select_from(Dispute).where(Dispute.vendor_id == ctx.vendor_id, Dispute.status == "open")) or 0),
            "low_stock": sum(1 for p in products if is_low(p)),
            "waiting_messages": int(
                db.scalar(
                    select(func.count()).select_from(Conversation).where(Conversation.vendor_id == ctx.vendor_id, Conversation.last_sender_role == "customer")
                )
                or 0
            ),
            "available_cents": pos["available_cents"],
            "eligible_payouts": pos["eligible_count"],
        }
    return {
        "area": "platform",
        "unread": _unread(db, ctx.user_id),
        "open_orders": int(db.scalar(select(func.count()).select_from(Order).where(Order.status.in_(("paid", "partially_fulfilled", "fulfilled")))) or 0),
        "open_disputes": int(db.scalar(select(func.count()).select_from(Dispute).where(Dispute.status == "open")) or 0),
        "vendors_to_review": int(db.scalar(select(func.count()).select_from(Vendor).where(Vendor.status == "under_review", Vendor.deleted_at.is_(None))) or 0),
        "payouts_to_sign": int(
            db.scalar(select(func.count()).select_from(Payout).where(Payout.status.in_(("requested", "pending_second_approval")))) or 0
        ),
        "flagged_reviews": int(db.scalar(select(func.count()).select_from(Review).where(Review.status == "flagged")) or 0),
    }
