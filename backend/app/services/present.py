"""Shared row-to-response helpers for catalogue, shops and reviews."""

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import system_scope
from app.models import Category, OrderLine, Product, Review, SubOrder, User, Vendor

LIVE_SUB_ORDER = ("pending_acceptance", "accepted", "packing", "shipped", "delivered")


def ratings(db: Session, product_ids: Iterable[str] | None = None) -> dict[str, tuple[float | None, int]]:
    query = (
        select(Review.product_id, func.avg(Review.rating), func.count(Review.id))
        .where(Review.status == "published")
        .group_by(Review.product_id)
    )
    if product_ids is not None:
        query = query.where(Review.product_id.in_(list(product_ids)))
    return {pid: (round(float(avg), 2) if avg is not None else None, int(n)) for pid, avg, n in db.execute(query)}


def units_sold(db: Session, product_ids: Iterable[str] | None = None) -> dict[str, int]:
    """Aggregate sales count. Read under platform scope: no buyer data leaves this function."""
    query = (
        select(OrderLine.product_id, func.sum(OrderLine.qty))
        .join(SubOrder, SubOrder.id == OrderLine.sub_order_id)
        .where(SubOrder.status.in_(LIVE_SUB_ORDER))
        .group_by(OrderLine.product_id)
    )
    if product_ids is not None:
        query = query.where(OrderLine.product_id.in_(list(product_ids)))
    with system_scope(db):
        return {pid: int(n or 0) for pid, n in db.execute(query)}


def product_counts(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(Product.vendor_id, func.count(Product.id))
        .where(Product.active.is_(True), Product.archived_at.is_(None))
        .group_by(Product.vendor_id)
    )
    return {vid: int(n) for vid, n in rows}


def categories_by_id(db: Session) -> dict[str, Category]:
    return {c.id: c for c in db.scalars(select(Category)).all()}


def available(product: Product) -> int:
    return sum(v.available for v in product.variants if v.active)


def is_low(product: Product) -> bool:
    return available(product) <= product.low_stock_threshold


def shop_card(vendor: Vendor, product_count: int = 0) -> dict:
    return {
        "id": vendor.id,
        "name": vendor.name,
        "slug": vendor.slug,
        "country": vendor.country,
        "city": vendor.city,
        "headline": vendor.headline,
        "about": vendor.about,
        "catalog_size": vendor.catalog_size,
        "image_url": vendor.image_url,
        "hue": vendor.hue,
        "rating": float(vendor.rating) if vendor.rating is not None else None,
        "rating_flag": vendor.rating_flag,
        "review_count": vendor.review_count,
        "lifetime_sales": vendor.lifetime_sales,
        "since": vendor.since,
        "response_hours": vendor.response_hours,
        "tier_id": vendor.tier_id,
        "tier_name": vendor.tier.name if vendor.tier else vendor.tier_id,
        "product_count": product_count,
        "shipping_fee_cents": vendor.shipping_fee_cents,
        "processing_days": vendor.processing_days,
    }


def variant_out(variant) -> dict:
    return {
        "id": variant.id,
        "sku": variant.sku,
        "size": variant.size,
        "color": variant.color,
        "active": variant.active,
        "on_hand": variant.on_hand,
        "reserved": variant.reserved,
        "available": variant.available,
    }


def product_out(
    product: Product,
    vendors: dict[str, Vendor],
    categories: dict[str, Category],
    rating: tuple[float | None, int] = (None, 0),
    sold: int = 0,
) -> dict:
    vendor = vendors[product.vendor_id]
    category = categories.get(product.category_id or "")
    return {
        "id": product.id,
        "vendor_id": product.vendor_id,
        "vendor_name": vendor.name,
        "vendor_slug": vendor.slug,
        "vendor_country": vendor.country,
        "category_id": product.category_id,
        "category_name": category.name if category else None,
        "title": product.title,
        "description": product.description,
        "price_cents": product.price_cents,
        "low_stock_threshold": product.low_stock_threshold,
        "image_url": product.image_url,
        "active": product.active,
        "archived_at": product.archived_at,
        "tags": [{"id": t.id, "name": t.name, "slug": t.slug} for t in product.tags],
        "variants": [variant_out(v) for v in product.variants],
        "available": available(product),
        "low_stock": is_low(product),
        "rating": rating[0],
        "review_count": rating[1],
        "units_sold": sold,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }


def product_card(product: Product, vendors: dict[str, Vendor], categories: dict[str, Category], rating, sold: int = 0) -> dict:
    full = product_out(product, vendors, categories, rating, sold)
    full["tags"] = [t.name for t in product.tags]
    return full


def review_card(review: Review, products: dict[str, Product], vendors: dict[str, Vendor], users: dict[str, User]) -> dict:
    product = products.get(review.product_id)
    vendor = vendors.get(review.vendor_id)
    buyer = users.get(review.buyer_id)
    return {
        "id": review.id,
        "product_id": review.product_id,
        "product_title": product.title if product else review.product_id,
        "vendor_id": review.vendor_id,
        "vendor_name": vendor.name if vendor else review.vendor_id,
        "buyer_name": buyer.name if buyer else "Customer",
        "rating": float(review.rating) if review.rating is not None else None,
        "body": review.body,
        "sentiment": review.sentiment,
        "theme": review.theme,
        "source": review.source,
        "status": review.status,
        "moderation_reason": review.moderation_reason,
        "verified_purchase": review.sub_order_id is not None,
        "sub_order_id": review.sub_order_id,
        "vendor_response": review.vendor_response,
        "vendor_responded_at": review.vendor_responded_at,
        "created_at": review.created_at,
    }


def review_cards(db: Session, reviews: list[Review]) -> list[dict]:
    product_ids = {r.product_id for r in reviews}
    vendor_ids = {r.vendor_id for r in reviews}
    user_ids = {r.buyer_id for r in reviews}
    products = {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(product_ids))).all()}
    vendors = {v.id: v for v in db.scalars(select(Vendor).where(Vendor.id.in_(vendor_ids))).all()}
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_(user_ids))).all()}
    return [review_card(r, products, vendors, users) for r in reviews]


def category_out(category: Category, categories: dict[str, Category], count: int = 0) -> dict:
    path: list[str] = []
    seen: set[str] = set()
    current: Category | None = category
    while current is not None and current.id not in seen:
        seen.add(current.id)
        path.insert(0, current.name)
        current = categories.get(current.parent_id or "")
    return {
        "id": category.id,
        "name": category.name,
        "name_kh": category.name_kh,
        "slug": category.slug,
        "parent_id": category.parent_id,
        "sort": category.sort,
        "product_count": count,
        "path": path,
    }


def descendants(categories: dict[str, Category], root_id: str) -> set[str]:
    result = {root_id}
    changed = True
    while changed:
        changed = False
        for c in categories.values():
            if c.parent_id in result and c.id not in result:
                result.add(c.id)
                changed = True
    return result
