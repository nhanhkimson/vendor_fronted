"""Public catalogue reads. Only active products from active, verified shops are visible."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import system_scope, utcnow
from app.core.errors import NotFound
from app.models import Coupon, Order, Product, ProductTag, Review, Tag, UserRole, Vendor
from app.services.catalogue import category_tree, list_tags
from app.services.present import (
    categories_by_id,
    category_out,
    descendants,
    is_low,
    product_card,
    product_counts,
    ratings,
    review_cards,
    shop_card,
    units_sold,
)

SORTS = ("relevance", "popular", "rating", "price_asc", "price_desc", "newest")


def visible():
    return (
        select(Product)
        .join(Vendor, Vendor.id == Product.vendor_id)
        .where(
            Product.active.is_(True),
            Product.archived_at.is_(None),
            Vendor.status == "active",
            Vendor.deleted_at.is_(None),
        )
    )


def _vendors(db: Session) -> dict[str, Vendor]:
    return {v.id: v for v in db.scalars(select(Vendor)).all()}


def cards(db: Session, products: list[Product]) -> list[dict]:
    ids = [p.id for p in products]
    rates = ratings(db, ids)
    sold = units_sold(db, ids)
    vendors = _vendors(db)
    categories = categories_by_id(db)
    return [product_card(p, vendors, categories, rates.get(p.id, (None, 0)), sold.get(p.id, 0)) for p in products]


def search(
    db: Session,
    *,
    q: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    shop: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    in_stock: bool = False,
    sort: str = "relevance",
    page: int = 1,
    page_size: int = 24,
) -> dict:
    query = visible()
    if q:
        like = f"%{q.lower()}%"
        tagged = select(ProductTag.product_id).join(Tag, Tag.id == ProductTag.tag_id).where(func.lower(Tag.name).like(like))
        query = query.where(
            or_(
                func.lower(Product.title).like(like),
                func.lower(Product.description).like(like),
                func.lower(Vendor.name).like(like),
                Product.id.in_(tagged),
            )
        )
    if category:
        categories = categories_by_id(db)
        match = next((c for c in categories.values() if c.slug == category or c.id == category), None)
        if match is None:
            return {"items": [], "total": 0, "page": page, "page_size": page_size}
        query = query.where(Product.category_id.in_(descendants(categories, match.id)))
    if tag:
        query = query.where(
            Product.id.in_(select(ProductTag.product_id).join(Tag, Tag.id == ProductTag.tag_id).where(Tag.slug == tag))
        )
    if shop:
        query = query.where(Vendor.slug == shop)
    if min_price is not None:
        query = query.where(Product.price_cents >= min_price)
    if max_price is not None:
        query = query.where(Product.price_cents <= max_price)

    items = cards(db, list(db.scalars(query).unique().all()))
    if in_stock:
        items = [i for i in items if i["available"] > 0]
    needle = (q or "").lower()
    keys = {
        "relevance": lambda i: (not i["title"].lower().startswith(needle), needle not in i["title"].lower(), -i["units_sold"], i["title"]),
        "popular": lambda i: (-i["units_sold"], i["title"]),
        "rating": lambda i: (-(i["rating"] or 0), -i["review_count"], i["title"]),
        "price_asc": lambda i: (i["price_cents"], i["title"]),
        "price_desc": lambda i: (-i["price_cents"], i["title"]),
        "newest": lambda i: (-i["created_at"].timestamp(), i["title"]),
    }
    items.sort(key=keys.get(sort, keys["relevance"]))
    start = (page - 1) * page_size
    return {"items": items[start : start + page_size], "total": len(items), "page": page, "page_size": page_size}


def reviews_for(db: Session, *, product_id: str | None = None, vendor_id: str | None = None, limit: int = 20) -> list[dict]:
    query = select(Review).where(Review.status == "published").order_by(Review.created_at.desc()).limit(limit)
    if product_id:
        query = query.where(Review.product_id == product_id)
    if vendor_id:
        query = query.where(Review.vendor_id == vendor_id)
    return review_cards(db, list(db.scalars(query).all()))


def promotions(db: Session, vendor_id: str | None = None) -> list[dict]:
    now = utcnow()
    query = (
        select(Coupon)
        .where(Coupon.active.is_(True), Coupon.starts_at <= now, Coupon.ends_at > now)
        .order_by(Coupon.is_flash.desc(), Coupon.ends_at)
    )
    if vendor_id:
        query = query.where(or_(Coupon.vendor_id.is_(None), Coupon.vendor_id == vendor_id))
    vendors = _vendors(db)
    out = []
    for c in db.scalars(query).all():
        if c.usage_limit is not None and c.used_count >= c.usage_limit:
            continue
        out.append(
            {
                "code": c.code,
                "funded_by": c.funded_by,
                "vendor_id": c.vendor_id,
                "vendor_name": vendors[c.vendor_id].name if c.vendor_id in vendors else None,
                "discount_type": c.discount_type,
                "percent_off": c.percent_off,
                "amount_off_cents": c.amount_off_cents,
                "min_subtotal_cents": c.min_subtotal_cents,
                "ends_at": c.ends_at,
                "is_flash": c.is_flash,
                "note": c.note,
            }
        )
    return out


def product_detail(db: Session, product_id: str) -> dict:
    product = db.scalar(visible().where(Product.id == product_id))
    if product is None:
        raise NotFound("Product", product_id)
    card = cards(db, [product])[0]
    vendor = db.get(Vendor, product.vendor_id)
    categories = categories_by_id(db)
    path = []
    current = categories.get(product.category_id or "")
    while current is not None and current.id not in {p["id"] for p in path}:
        path.insert(0, category_out(current, categories))
        current = categories.get(current.parent_id or "")
    related_query = (
        visible()
        .where(Product.id != product.id, or_(Product.category_id == product.category_id, Product.vendor_id == product.vendor_id))
        .limit(8)
    )
    related = cards(db, list(db.scalars(related_query).unique().all()))[:4]
    card.update(
        description=product.description,
        low_stock=is_low(product),
        variants=[
            {"id": v.id, "sku": v.sku, "size": v.size, "color": v.color, "available": v.available}
            for v in product.variants
            if v.active
        ],
        shop=shop_card(vendor, product_counts(db).get(vendor.id, 0)),
        category_path=path,
        reviews=reviews_for(db, product_id=product.id),
        related=related,
    )
    return card


def shops(db: Session) -> list[dict]:
    counts = product_counts(db)
    vendors = db.scalars(
        select(Vendor).where(Vendor.status == "active", Vendor.deleted_at.is_(None)).order_by(Vendor.name)
    ).all()
    return [shop_card(v, counts.get(v.id, 0)) for v in vendors]


def shop_page(db: Session, slug: str) -> dict:
    vendor = db.scalar(select(Vendor).where(Vendor.slug == slug, Vendor.status == "active", Vendor.deleted_at.is_(None)))
    if vendor is None:
        raise NotFound("Shop", slug)
    products = list(db.scalars(visible().where(Product.vendor_id == vendor.id).order_by(Product.title)).unique().all())
    return {
        "shop": shop_card(vendor, len(products)),
        "products": cards(db, products),
        "reviews": reviews_for(db, vendor_id=vendor.id, limit=12),
        "promotions": [p for p in promotions(db, vendor.id) if p["vendor_id"] == vendor.id or p["vendor_id"] is None],
    }


def review_feed(db: Session, *, vendor: str | None, min_rating: float | None, theme: str | None, page: int, page_size: int) -> dict:
    query = select(Review).where(Review.status == "published")
    if vendor:
        query = query.join(Vendor, Vendor.id == Review.vendor_id).where(or_(Vendor.slug == vendor, Vendor.id == vendor))
    if min_rating is not None:
        query = query.where(Review.rating >= min_rating)
    if theme:
        query = query.where(Review.theme == theme)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(Review.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": review_cards(db, list(rows)), "total": int(total), "page": page, "page_size": page_size}


def home(db: Session) -> dict:
    everything = cards(db, list(db.scalars(visible()).unique().all()))
    featured = sorted(everything, key=lambda i: (-i["units_sold"], -(i["rating"] or 0), i["title"]))[:8]
    newest = sorted(everything, key=lambda i: i["created_at"], reverse=True)[:8]
    shop_list = sorted(shops(db), key=lambda s: (-(s["rating"] or 0), -s["review_count"]))[:6]
    roots = [c for c in category_tree(db) if c["parent_id"] is None]
    good_reviews = [r for r in reviews_for(db, limit=30) if (r["rating"] or 0) >= 4][:6]
    with system_scope(db):
        orders = db.scalar(select(func.count()).select_from(Order)) or 0
        customers = (
            db.scalar(select(func.count(func.distinct(UserRole.user_id))).where(UserRole.role_id == "customer")) or 0
        )
    return {
        "featured": featured,
        "new_arrivals": newest,
        "shops": shop_list,
        "categories": roots,
        "promotions": promotions(db),
        "reviews": good_reviews,
        "stats": {
            "shops": len(shops(db)),
            "products": len(everything),
            "orders": int(orders),
            "customers": int(customers),
        },
    }


def tags(db: Session) -> list[dict]:
    return list_tags(db)
