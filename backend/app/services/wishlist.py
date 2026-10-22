"""Saved products for a signed-in customer."""

from sqlalchemy import select

from app.core.deps import Ctx
from app.core.errors import NotFound
from app.models import Category, Product, Vendor, WishlistItem
from app.services.present import categories_by_id, product_card, ratings, units_sold


def _cards(db, items: list[WishlistItem]) -> list[dict]:
    products = {
        p.id: p
        for p in db.scalars(select(Product).where(Product.id.in_([i.product_id for i in items] or [""]))).all()
    }
    vendors = {v.id: v for v in db.scalars(select(Vendor).where(Vendor.id.in_({p.vendor_id for p in products.values()} or {""}))).all()}
    categories: dict[str, Category] = categories_by_id(db)
    scores = ratings(db, products)
    sold = units_sold(db, products)
    rows = []
    for item in items:
        product = products.get(item.product_id)
        if product is None or product.vendor_id not in vendors:
            continue
        card = product_card(product, vendors, categories, scores.get(product.id, (None, 0)), sold.get(product.id, 0))
        card["tags"] = [t.name for t in product.tags]
        rows.append({"product_id": item.product_id, "added_at": item.created_at, "product": card})
    return rows


def list_saved(ctx: Ctx) -> list[dict]:
    items = ctx.db.scalars(
        select(WishlistItem).where(WishlistItem.user_id == ctx.user_id).order_by(WishlistItem.created_at.desc())
    ).all()
    return _cards(ctx.db, items)


def add(ctx: Ctx, product_id: str) -> list[dict]:
    db = ctx.db
    product = db.get(Product, product_id)
    if product is None:
        raise NotFound("Product", product_id)
    existing = db.get(WishlistItem, (ctx.user_id, product_id))
    if existing is None:
        db.add(WishlistItem(user_id=ctx.user_id, product_id=product_id))
    ctx.audit("customer", "wishlist_add", "product", product_id, after={"saved": True, "already": existing is not None})
    ctx.commit()
    return list_saved(ctx)


def remove(ctx: Ctx, product_id: str) -> list[dict]:
    db = ctx.db
    item = db.get(WishlistItem, (ctx.user_id, product_id))
    if item is None:
        raise NotFound("Saved product", product_id)
    db.delete(item)
    ctx.audit("customer", "wishlist_remove", "product", product_id, before={"saved": True}, after={"saved": False})
    ctx.commit()
    return list_saved(ctx)
