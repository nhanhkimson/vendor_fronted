"""M4 Products & inventory, M5 Categories & tags."""

import csv
import io

from fastapi import UploadFile
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.db import utcnow
from app.core.deps import Ctx
from app.core.errors import Conflict, NotFound, Unprocessable
from app.core.util import new_id, slugify, snapshot
from app.models import Category, OrderLine, Product, ProductTag, StockItem, Tag, Variant, Vendor
from app.services import files
from app.services.events import Notice, emit, vendor_staff_ids
from app.services.present import (
    available,
    categories_by_id,
    category_out,
    descendants,
    product_out,
    ratings,
    units_sold,
)
from app.services.tenancy import owned

PRODUCT_FIELDS = ["title", "description", "price_cents", "category_id", "low_stock_threshold", "active"]
CSV_COLUMNS = ["product_id", "title", "description", "price", "category", "tags", "sku", "size", "color", "stock", "active"]


# Products ------------------------------------------------------------------------


def _vendors(db: Session) -> dict[str, Vendor]:
    return {v.id: v for v in db.scalars(select(Vendor)).all()}


def serialize(db: Session, products: list[Product]) -> list[dict]:
    ids = [p.id for p in products]
    rates = ratings(db, ids)
    sold = units_sold(db, ids)
    vendors = _vendors(db)
    categories = categories_by_id(db)
    return [product_out(p, vendors, categories, rates.get(p.id, (None, 0)), sold.get(p.id, 0)) for p in products]


def one(db: Session, product: Product) -> dict:
    db.expire(product)
    return serialize(db, [product])[0]


def list_products(db: Session, *, vendor_id: str | None, q: str | None, status: str | None, category: str | None) -> list[dict]:
    query = select(Product).order_by(Product.created_at.desc())
    if vendor_id:
        query = query.where(Product.vendor_id == vendor_id)
    if q:
        like = f"%{q.lower()}%"
        query = query.where(or_(func.lower(Product.title).like(like), Product.id == q.upper()))
    if category:
        query = query.where(Product.category_id.in_(descendants(categories_by_id(db), category)))
    if status == "archived":
        query = query.where(Product.archived_at.is_not(None))
    elif status == "inactive":
        query = query.where(Product.active.is_(False), Product.archived_at.is_(None))
    elif status in ("active", "low"):
        query = query.where(Product.active.is_(True), Product.archived_at.is_(None))
    else:
        query = query.where(Product.archived_at.is_(None))
    products = list(db.scalars(query).all())
    if status == "low":
        products = [p for p in products if available(p) <= p.low_stock_threshold]
    return serialize(db, products)


def get_product(ctx: Ctx, product_id: str) -> Product:
    return owned(ctx, Product, product_id, "Product", "product", "product")


def _check_category(db: Session, category_id: str | None) -> None:
    if category_id and db.get(Category, category_id) is None:
        raise Unprocessable(f"Category {category_id} does not exist", code="unknown_category")


def _check_tags(db: Session, tag_ids: list[str]) -> list[str]:
    found = set(db.scalars(select(Tag.id).where(Tag.id.in_(tag_ids))).all())
    unknown = [t for t in tag_ids if t not in found]
    if unknown:
        raise Unprocessable(f"Unknown tags: {', '.join(unknown)}", code="unknown_tag")
    return list(dict.fromkeys(tag_ids))


def _check_sku(db: Session, vendor_id: str, sku: str, exclude_variant: str | None = None) -> None:
    query = select(Variant.id).where(Variant.vendor_id == vendor_id, func.lower(Variant.sku) == sku.lower())
    if exclude_variant:
        query = query.where(Variant.id != exclude_variant)
    if db.scalar(query):
        raise Conflict(f"SKU {sku} is already used in your shop", code="duplicate_sku")


def _add_variant(db: Session, product: Product, vendor: Vendor, sku: str, size: str, color: str, stock: int) -> Variant:
    _check_sku(db, vendor.id, sku)
    variant = Variant(
        id=f"{product.id}-{new_id('V', 4).split('-')[1].lower()}",
        product_id=product.id,
        vendor_id=vendor.id,
        sku=sku,
        size=size,
        color=color,
    )
    db.add(variant)
    db.flush()
    db.add(
        StockItem(
            variant_id=variant.id,
            vendor_id=vendor.id,
            warehouse_id=vendor.warehouse_id or "WH-EAST",
            on_hand=stock,
            reserved=0,
        )
    )
    return variant


def create_product(ctx: Ctx, body) -> dict:
    db = ctx.db
    vendor = db.get(Vendor, ctx.vendor_id)
    _check_category(db, body.category_id)
    tag_ids = _check_tags(db, body.tag_ids)
    product = Product(
        id=new_id("P", 6),
        vendor_id=vendor.id,
        category_id=body.category_id,
        title=body.title.strip(),
        description=body.description,
        price_cents=body.price_cents,
        low_stock_threshold=body.low_stock_threshold,
        active=body.active,
    )
    db.add(product)
    db.flush()
    variants = body.variants or []
    if not variants:
        _add_variant(db, product, vendor, f"{product.id}-STD", "One size", "Natural", 0)
    skus = [v.sku.lower() for v in variants]
    if len(skus) != len(set(skus)):
        raise Unprocessable("Each variant needs its own SKU", code="duplicate_sku")
    for v in variants:
        _add_variant(db, product, vendor, v.sku, v.size, v.color, v.stock)
    for tag_id in tag_ids:
        db.add(ProductTag(product_id=product.id, tag_id=tag_id))
    ctx.audit(
        "product",
        "create",
        "product",
        product.id,
        after=snapshot(product, PRODUCT_FIELDS) | {"variants": [v.sku for v in variants], "tags": tag_ids},
    )
    ctx.commit()
    return one(db, product)


def update_product(ctx: Ctx, product_id: str, body) -> dict:
    db = ctx.db
    product = get_product(ctx, product_id)
    if product.archived_at:
        raise Conflict("This product is archived. Restore it before editing.", code="product_archived")
    changes = body.model_dump(exclude_unset=True)
    if "category_id" in changes:
        _check_category(db, changes["category_id"])
    before = snapshot(product, PRODUCT_FIELDS)
    for field, value in changes.items():
        setattr(product, field, value)
    product.updated_at = utcnow()
    ctx.audit("product", "update", "product", product.id, before=before, after=snapshot(product, PRODUCT_FIELDS))
    ctx.commit()
    return one(db, product)


def archive_product(ctx: Ctx, product_id: str) -> None:
    product = get_product(ctx, product_id)
    if product.archived_at:
        raise Conflict("This product is already archived", code="product_archived")
    product.archived_at = utcnow()
    product.active = False
    ctx.audit("product", "delete", "product", product.id, before={"active": True, "archived_at": None}, after={"active": False, "archived_at": product.archived_at})
    ctx.commit()


def restore_product(ctx: Ctx, product_id: str) -> dict:
    product = get_product(ctx, product_id)
    if not product.archived_at:
        raise Conflict("This product is not archived", code="not_archived")
    before = product.archived_at
    product.archived_at = None
    ctx.audit("product", "restore", "product", product.id, before={"archived_at": before}, after={"archived_at": None, "active": product.active})
    ctx.commit()
    return one(ctx.db, product)


def moderate_product(ctx: Ctx, product_id: str, active: bool, reason: str, category_id: str | None) -> dict:
    db = ctx.db
    product = db.get(Product, product_id)
    if product is None:
        raise NotFound("Product", product_id)
    _check_category(db, category_id)
    before = snapshot(product, ["active", "category_id"])
    product.active = active
    if category_id:
        product.category_id = category_id
    ctx.audit("product", "moderate", "product", product.id, before=before, after=snapshot(product, ["active", "category_id"]), reason=reason)
    if not active:
        emit(
            db,
            "product.delisted",
            {"product_id": product.id, "reason": reason},
            [Notice(uid, f"{product.title} was hidden by Bazaar: {reason}", "/seller/products") for uid in vendor_staff_ids(db, product.vendor_id)],
        )
    ctx.commit()
    return one(db, product)


def add_variant(ctx: Ctx, product_id: str, body) -> dict:
    db = ctx.db
    product = get_product(ctx, product_id)
    vendor = db.get(Vendor, product.vendor_id)
    variant = _add_variant(db, product, vendor, body.sku, body.size, body.color, body.stock)
    ctx.audit("product", "add_variant", "variant", variant.id, after={"product_id": product.id, "sku": body.sku, "size": body.size, "color": body.color, "stock": body.stock})
    ctx.commit()
    return one(db, product)


def update_variant(ctx: Ctx, variant_id: str, body) -> dict:
    db = ctx.db
    variant = owned(ctx, Variant, variant_id, "Variant", "product", "variant")
    changes = body.model_dump(exclude_unset=True)
    if "sku" in changes:
        _check_sku(db, variant.vendor_id, changes["sku"], exclude_variant=variant.id)
    before = snapshot(variant, ["sku", "size", "color", "active"])
    for field, value in changes.items():
        setattr(variant, field, value)
    ctx.audit("product", "update_variant", "variant", variant.id, before=before, after=snapshot(variant, ["sku", "size", "color", "active"]))
    ctx.commit()
    return one(db, db.get(Product, variant.product_id))


def upload_image(ctx: Ctx, product_id: str, upload: UploadFile) -> dict:
    product = get_product(ctx, product_id)
    before = product.image_url
    product.image_url = files.save_image(upload, "products", product.id)
    product.updated_at = utcnow()
    ctx.audit("product", "upload_image", "product", product.id, before={"image_url": before}, after={"image_url": product.image_url})
    ctx.commit()
    return one(ctx.db, product)


def set_tags(ctx: Ctx, product_id: str, tag_ids: list[str]) -> dict:
    db = ctx.db
    product = get_product(ctx, product_id) if ctx.scope == "vendor" else db.get(Product, product_id)
    if product is None:
        raise NotFound("Product", product_id)
    wanted = _check_tags(db, tag_ids)
    before = sorted(t.id for t in product.tags)
    db.execute(delete(ProductTag).where(ProductTag.product_id == product.id))
    for tag_id in wanted:
        db.add(ProductTag(product_id=product.id, tag_id=tag_id))
    ctx.audit("category", "assign_tags", "product", product.id, before={"tags": before}, after={"tags": sorted(wanted)})
    ctx.commit()
    return one(db, product)


# Inventory -------------------------------------------------------------------------


def inventory(db: Session, vendor_id: str | None, low_only: bool) -> list[dict]:
    query = (
        select(StockItem, Variant, Product)
        .join(Variant, Variant.id == StockItem.variant_id)
        .join(Product, Product.id == Variant.product_id)
        .where(Product.archived_at.is_(None))
        .order_by(Product.title, Variant.sku)
    )
    if vendor_id:
        query = query.where(StockItem.vendor_id == vendor_id)
    rows = []
    for stock, variant, product in db.execute(query).all():
        avail = stock.on_hand - stock.reserved
        low = avail <= product.low_stock_threshold
        if low_only and not low:
            continue
        rows.append(
            {
                "variant_id": variant.id,
                "product_id": product.id,
                "title": product.title,
                "sku": variant.sku,
                "size": variant.size,
                "color": variant.color,
                "image_url": product.image_url,
                "warehouse_id": stock.warehouse_id,
                "on_hand": stock.on_hand,
                "reserved": stock.reserved,
                "available": avail,
                "low_stock_threshold": product.low_stock_threshold,
                "low": low,
                "active": variant.active and product.active,
            }
        )
    return rows


def notify_low_stock(db: Session, product: Product, before_available: int) -> None:
    after = available(product)
    if after <= product.low_stock_threshold < before_available or (after == 0 < before_available):
        title = f"{product.title} is sold out" if after == 0 else f"{product.title} is down to {after} unit{'s' if after != 1 else ''}"
        emit(
            db,
            "stock.low",
            {"product_id": product.id, "available": after, "threshold": product.low_stock_threshold},
            [Notice(uid, title, "/seller/inventory", "Restock before it sells out.") for uid in vendor_staff_ids(db, product.vendor_id)],
        )


def adjust_stock(ctx: Ctx, variant_id: str, delta: int | None, set_to: int | None, reason: str) -> dict:
    db = ctx.db
    if (delta is None) == (set_to is None):
        raise Unprocessable("Send either delta or set_to", code="adjust_mode")
    variant = owned(ctx, Variant, variant_id, "Variant", "product", "variant")
    product = db.get(Product, variant.product_id)
    stock = variant.stock_items[0] if variant.stock_items else None
    if stock is None:
        raise Conflict("This variant has no stock location", code="no_stock_item")
    before_available = available(product)
    before = {"on_hand": stock.on_hand, "reserved": stock.reserved}
    target = stock.on_hand + delta if delta is not None else set_to
    if target < stock.reserved:
        raise Conflict(
            f"{stock.reserved} unit(s) are reserved by open checkouts, so on-hand cannot go below {stock.reserved}",
            code="below_reserved",
        )
    stock.on_hand = target
    stock.updated_at = utcnow()
    db.flush()
    db.expire(product)
    ctx.audit("product", "adjust_stock", "variant", variant.id, before=before, after={"on_hand": stock.on_hand, "reserved": stock.reserved}, reason=reason)
    notify_low_stock(db, product, before_available)
    ctx.commit()
    return next(r for r in inventory(db, variant.vendor_id, False) if r["variant_id"] == variant.id)


# CSV import / export -------------------------------------------------------------------


def export_csv(ctx: Ctx, vendor_id: str) -> str:
    db = ctx.db
    categories = categories_by_id(db)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(CSV_COLUMNS)
    products = db.scalars(
        select(Product).where(Product.vendor_id == vendor_id, Product.archived_at.is_(None)).order_by(Product.id)
    ).all()
    for product in products:
        category = categories.get(product.category_id or "")
        for variant in product.variants:
            writer.writerow(
                [
                    product.id,
                    product.title,
                    product.description,
                    f"{product.price_cents / 100:.2f}",
                    category.slug if category else "",
                    "|".join(t.name for t in product.tags),
                    variant.sku,
                    variant.size,
                    variant.color,
                    variant.on_hand,
                    "yes" if product.active and variant.active else "no",
                ]
            )
    ctx.audit("product", "export", "product", None, after={"vendor_id": vendor_id, "products": len(products)})
    ctx.commit()
    return out.getvalue()


def _price(value: str) -> int:
    try:
        cents = round(float(value.replace("$", "").replace(",", "").strip()) * 100)
    except ValueError as exc:
        raise ValueError(f"price '{value}' is not a number") from exc
    if cents <= 0:
        raise ValueError("price must be greater than 0")
    return cents


def import_csv(ctx: Ctx, upload: UploadFile, dry_run: bool) -> dict:
    """Upsert products and variants by SKU. All rows apply, or none do."""
    db = ctx.db
    vendor = db.get(Vendor, ctx.vendor_id)
    raw = upload.file.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise Unprocessable("CSV files are limited to 1 MB", code="file_too_large")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise Unprocessable("Save the CSV as UTF-8", code="encoding") from exc
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in ("title", "price", "sku") if c not in (reader.fieldnames or [])]
    if missing:
        raise Unprocessable(f"Missing columns: {', '.join(missing)}. Expected: {', '.join(CSV_COLUMNS)}", code="csv_columns")

    categories = {c.slug: c.id for c in db.scalars(select(Category)).all()}
    tags = {t.name: t.id for t in db.scalars(select(Tag)).all()}
    by_sku = {v.sku.lower(): v for v in db.scalars(select(Variant).where(Variant.vendor_id == vendor.id)).all()}
    products_by_id = {p.id: p for p in db.scalars(select(Product).where(Product.vendor_id == vendor.id)).all()}
    created_by_title: dict[str, Product] = {}
    updated_ids: set[str] = set()
    result = {"created_products": 0, "updated_products": 0, "created_variants": 0, "updated_variants": 0}
    errors: list[dict] = []
    seen_skus: set[str] = set()

    for number, row in enumerate(reader, start=2):
        try:
            row = {k: (v or "").strip() for k, v in row.items() if k}
            sku = row.get("sku", "")
            if not sku:
                raise ValueError("sku is required")
            if sku.lower() in seen_skus:
                raise ValueError(f"SKU {sku} appears twice in the file")
            seen_skus.add(sku.lower())
            title = row.get("title", "")
            if len(title) < 3:
                raise ValueError("title must be at least 3 characters")
            price = _price(row.get("price", ""))
            category_id = None
            if row.get("category"):
                category_id = categories.get(row["category"])
                if category_id is None:
                    raise ValueError(f"category '{row['category']}' does not exist (use the slug, e.g. textiles)")
            tag_ids = []
            for name in filter(None, (t.strip() for t in row.get("tags", "").split("|"))):
                if name not in tags:
                    raise ValueError(f"tag '{name}' does not exist")
                tag_ids.append(tags[name])
            stock = int(row.get("stock") or 0)
            if stock < 0:
                raise ValueError("stock cannot be negative")
            active = row.get("active", "yes").lower() not in ("no", "false", "0")

            variant = by_sku.get(sku.lower())
            product = None
            if variant is not None:
                product = products_by_id[variant.product_id]
            elif row.get("product_id"):
                product = products_by_id.get(row["product_id"])
                if product is None:
                    raise ValueError(f"product {row['product_id']} is not in your shop")
            else:
                product = created_by_title.get(title.lower())

            if product is None:
                product = Product(
                    id=new_id("P", 6),
                    vendor_id=vendor.id,
                    title=title,
                    description=row.get("description", ""),
                    price_cents=price,
                    category_id=category_id,
                    active=active,
                )
                db.add(product)
                db.flush()
                products_by_id[product.id] = product
                created_by_title[title.lower()] = product
                for tag_id in tag_ids:
                    db.add(ProductTag(product_id=product.id, tag_id=tag_id))
                result["created_products"] += 1
            elif product.id not in {p.id for p in created_by_title.values()}:
                product.title = title
                product.description = row.get("description", product.description)
                product.price_cents = price
                product.category_id = category_id or product.category_id
                product.active = active
                product.archived_at = None if active else product.archived_at
                product.updated_at = utcnow()
                updated_ids.add(product.id)

            if variant is None:
                variant = _add_variant(db, product, vendor, sku, row.get("size") or "One size", row.get("color") or "Natural", stock)
                by_sku[sku.lower()] = variant
                result["created_variants"] += 1
            else:
                variant.size = row.get("size") or variant.size
                variant.color = row.get("color") or variant.color
                db.flush()
                item = db.scalar(select(StockItem).where(StockItem.variant_id == variant.id))
                if item and stock < item.reserved:
                    raise ValueError(f"stock {stock} is below the {item.reserved} unit(s) reserved by open checkouts")
                if item:
                    item.on_hand = stock
                result["updated_variants"] += 1
        except ValueError as exc:
            errors.append({"row": number, "message": str(exc)})
        except Conflict as exc:
            errors.append({"row": number, "message": exc.message})

    result["updated_products"] = len(updated_ids)
    if errors or dry_run:
        db.rollback()
        return {"dry_run": dry_run, **result, "errors": errors}
    ctx.audit("product", "import", "product", None, after={**result, "rows": len(seen_skus)})
    ctx.commit()
    return {"dry_run": False, **result, "errors": []}


# Categories and tags --------------------------------------------------------------------


def category_tree(db: Session, active_only: bool = True) -> list[dict]:
    categories = categories_by_id(db)
    query = select(Product.category_id, func.count(Product.id)).group_by(Product.category_id)
    if active_only:
        query = (
            query.join(Vendor, Vendor.id == Product.vendor_id)
            .where(Product.active.is_(True), Product.archived_at.is_(None), Vendor.status == "active")
        )
    direct = {cid: int(n) for cid, n in db.execute(query) if cid}
    result = []
    for category in sorted(categories.values(), key=lambda c: (c.sort, c.name)):
        count = sum(direct.get(c, 0) for c in descendants(categories, category.id))
        result.append(category_out(category, categories, count))
    return result


def _unique_category_slug(db: Session, slug: str, exclude: str | None = None) -> str:
    slug = slugify(slug)
    query = select(Category.id).where(Category.slug == slug)
    if exclude:
        query = query.where(Category.id != exclude)
    if db.scalar(query):
        raise Conflict(f"The slug {slug} is already used by another category", code="duplicate_slug")
    return slug


def _check_category_parent(db: Session, category_id: str | None, parent_id: str) -> None:
    categories = categories_by_id(db)
    if parent_id not in categories:
        raise Unprocessable(f"Parent category {parent_id} does not exist", code="unknown_category")
    current: str | None = parent_id
    seen: set[str] = set()
    while current:
        if current == category_id:
            raise Conflict("That parent would put the category inside itself", code="category_cycle")
        if current in seen:
            break
        seen.add(current)
        current = categories[current].parent_id if current in categories else None


def create_category(ctx: Ctx, body) -> dict:
    db = ctx.db
    slug = _unique_category_slug(db, body.slug or body.name)
    if body.parent_id:
        _check_category_parent(db, None, body.parent_id)
    category = Category(id=new_id("cat", 6).lower(), name=body.name.strip(), name_kh=body.name_kh, slug=slug, parent_id=body.parent_id, sort=body.sort)
    db.add(category)
    db.flush()
    ctx.audit("category", "create", "category", category.id, after=snapshot(category, ["name", "slug", "parent_id"]))
    ctx.commit()
    return next(c for c in category_tree(db, False) if c["id"] == category.id)


def update_category(ctx: Ctx, category_id: str, body) -> dict:
    db = ctx.db
    category = db.get(Category, category_id)
    if category is None:
        raise NotFound("Category", category_id)
    before = snapshot(category, ["name", "name_kh", "slug", "parent_id", "sort"])
    if body.name is not None:
        category.name = body.name.strip()
    if body.name_kh is not None:
        category.name_kh = body.name_kh
    if body.slug is not None:
        category.slug = _unique_category_slug(db, body.slug, exclude=category_id)
    if body.sort is not None:
        category.sort = body.sort
    if body.clear_parent:
        category.parent_id = None
    elif body.parent_id is not None:
        _check_category_parent(db, category_id, body.parent_id)
        category.parent_id = body.parent_id
    ctx.audit("category", "update", "category", category_id, before=before, after=snapshot(category, ["name", "name_kh", "slug", "parent_id", "sort"]))
    ctx.commit()
    return next(c for c in category_tree(db, False) if c["id"] == category_id)


def delete_category(ctx: Ctx, category_id: str) -> None:
    db = ctx.db
    category = db.get(Category, category_id)
    if category is None:
        raise NotFound("Category", category_id)
    children = db.scalars(select(Category.name).where(Category.parent_id == category_id)).all()
    if children:
        raise Conflict(f"Move or delete the sub-categories first: {', '.join(children)}", code="category_has_children")
    products = db.scalar(select(func.count()).select_from(Product).where(Product.category_id == category_id)) or 0
    if products:
        raise Conflict(f"{products} product(s) still use {category.name}. Move them first.", code="category_in_use")
    used_in_orders = db.scalar(select(func.count()).select_from(OrderLine).where(OrderLine.category_id == category_id)) or 0
    ctx.audit("category", "delete", "category", category_id, before=snapshot(category, ["name", "slug", "parent_id"]) | {"order_lines": used_in_orders})
    db.delete(category)
    ctx.commit()


def list_tags(db: Session) -> list[dict]:
    counts = dict(db.execute(select(ProductTag.tag_id, func.count()).group_by(ProductTag.tag_id)).all())
    return [
        {"id": t.id, "name": t.name, "slug": t.slug, "product_count": int(counts.get(t.id, 0))}
        for t in db.scalars(select(Tag).order_by(Tag.name)).all()
    ]


def create_tag(ctx: Ctx, name: str) -> dict:
    db = ctx.db
    slug = slugify(name)
    if db.scalar(select(Tag).where(or_(Tag.slug == slug, func.lower(Tag.name) == name.lower()))):
        raise Conflict(f"The tag {name} already exists", code="duplicate_tag")
    tag = Tag(id=f"t-{slug}"[:40], name=slug, slug=slug)
    db.add(tag)
    ctx.audit("category", "create_tag", "tag", tag.id, after={"name": slug})
    ctx.commit()
    return {"id": tag.id, "name": tag.name, "slug": tag.slug, "product_count": 0}


def delete_tag(ctx: Ctx, tag_id: str) -> None:
    db = ctx.db
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise NotFound("Tag", tag_id)
    used = db.scalar(select(func.count()).select_from(ProductTag).where(ProductTag.tag_id == tag_id)) or 0
    db.execute(delete(ProductTag).where(ProductTag.tag_id == tag_id))
    ctx.audit("category", "delete_tag", "tag", tag_id, before={"name": tag.name, "products": used})
    db.delete(tag)
    ctx.commit()
