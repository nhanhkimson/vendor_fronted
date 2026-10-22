"""M6 server-side cart. Prices and availability are always re-read, never trusted from the browser."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import utcnow
from app.core.deps import Ctx
from app.core.errors import Conflict, NotFound, Unprocessable
from app.core.util import new_id
from app.domain.pricing import Quote, QuoteLine, build_quote
from app.models import Cart, CartLine, Product, Variant, Vendor
from app.services import coupons

MAX_QTY = 10


def get_or_create(db: Session, user_id: str) -> Cart:
    cart = db.scalar(select(Cart).where(Cart.user_id == user_id))
    if cart is None:
        cart = Cart(id=new_id("CART", 10), user_id=user_id)
        db.add(cart)
        db.flush()
    return cart


def _sellable(db: Session, variant_id: str) -> tuple[Variant, Product, Vendor]:
    variant = db.get(Variant, variant_id)
    product = db.get(Product, variant.product_id) if variant else None
    vendor = db.get(Vendor, product.vendor_id) if product else None
    if (
        variant is None
        or product is None
        or vendor is None
        or not variant.active
        or not product.active
        or product.archived_at is not None
        or vendor.status != "active"
        or vendor.deleted_at is not None
    ):
        raise NotFound("Product option", variant_id)
    return variant, product, vendor


def build(db: Session, cart: Cart, user_id: str) -> tuple[Quote, dict[int, str], list[str], dict[str, Vendor]]:
    """Quote for the cart plus per-line problems (sold out, removed from sale)."""
    lines: list[QuoteLine] = []
    problems: dict[int, str] = {}
    vendors: dict[str, Vendor] = {}
    for cart_line in cart.lines:
        try:
            variant, product, vendor = _sellable(db, cart_line.variant_id)
        except NotFound:
            problems[cart_line.id] = "No longer available. Remove it to continue."
            continue
        vendors[vendor.id] = vendor
        if variant.available < cart_line.qty:
            problems[cart_line.id] = (
                "Sold out" if variant.available <= 0 else f"Only {variant.available} left. Lower the quantity."
            )
        lines.append(
            QuoteLine(
                variant_id=variant.id,
                product_id=product.id,
                vendor_id=vendor.id,
                title=product.title,
                sku=variant.sku,
                size=variant.size,
                color=variant.color,
                unit_price_cents=product.price_cents,
                qty=cart_line.qty,
                category_id=product.category_id,
                image_url=product.image_url,
                available=variant.available,
            )
        )

    coupon_terms = None
    coupon_problem = None
    if cart.coupon_code:
        coupon = coupons.find(db, cart.coupon_code)
        coupon_problem = coupons.problem(db, coupon, user_id)
        if coupon_problem is None:
            coupon_terms = coupons.terms(db, coupon)
    quote = build_quote(lines, {v.id: (v.name, v.shipping_fee_cents) for v in vendors.values()}, coupon_terms, coupon_problem)
    messages = [f"{_title(cart, lid, quote)}: {msg}" for lid, msg in problems.items()]
    return quote, problems, messages, vendors


def _title(cart: Cart, line_id: int, quote: Quote) -> str:
    variant_id = next((cl.variant_id for cl in cart.lines if cl.id == line_id), None)
    for group in quote.groups:
        for line in group.lines:
            if line.variant_id == variant_id:
                return line.title
    return "An item"


def out(db: Session, cart: Cart, user_id: str, notes: list[str] | None = None) -> dict:
    db.refresh(cart)
    quote, problems, messages, vendors = build(db, cart, user_id)
    by_variant = {cl.variant_id: cl for cl in cart.lines}
    groups = []
    for group in quote.groups:
        groups.append(
            {
                "vendor_id": group.vendor_id,
                "vendor_name": group.vendor_name,
                "vendor_slug": vendors[group.vendor_id].slug,
                "shipping_cents": group.shipping_cents,
                "items_subtotal_cents": group.items_subtotal_cents,
                "vendor_discount_cents": group.vendor_discount_cents,
                "platform_discount_cents": group.platform_discount_cents,
                "charged_cents": group.charged_cents,
                "lines": [
                    {
                        "id": by_variant[line.variant_id].id,
                        "variant_id": line.variant_id,
                        "product_id": line.product_id,
                        "title": line.title,
                        "image_url": line.image_url,
                        "vendor_id": line.vendor_id,
                        "vendor_name": group.vendor_name,
                        "sku": line.sku,
                        "size": line.size,
                        "color": line.color,
                        "unit_price_cents": line.unit_price_cents,
                        "qty": line.qty,
                        "line_total_cents": line.line_total_cents,
                        "available": line.available,
                        "vendor_discount_cents": line.vendor_discount_cents,
                        "platform_discount_cents": line.platform_discount_cents,
                        "problem": problems.get(by_variant[line.variant_id].id),
                    }
                    for line in group.lines
                ],
            }
        )
    unavailable = [cl for cl in cart.lines if cl.id in problems and cl.variant_id not in {line.variant_id for g in quote.groups for line in g.lines}]
    if unavailable:
        groups.append(
            {
                "vendor_id": "unavailable",
                "vendor_name": "No longer available",
                "vendor_slug": "",
                "shipping_cents": 0,
                "items_subtotal_cents": 0,
                "vendor_discount_cents": 0,
                "platform_discount_cents": 0,
                "charged_cents": 0,
                "lines": [
                    {
                        "id": cl.id,
                        "variant_id": cl.variant_id,
                        "product_id": "",
                        "title": "Item removed from sale",
                        "image_url": None,
                        "vendor_id": "",
                        "vendor_name": "",
                        "sku": "",
                        "size": "",
                        "color": "",
                        "unit_price_cents": 0,
                        "qty": cl.qty,
                        "line_total_cents": 0,
                        "available": 0,
                        "vendor_discount_cents": 0,
                        "platform_discount_cents": 0,
                        "problem": problems[cl.id],
                    }
                    for cl in unavailable
                ],
            }
        )
    return {
        "item_count": sum(cl.qty for cl in cart.lines),
        "groups": groups,
        "coupon_code": cart.coupon_code,
        "coupon_applied": quote.coupon is not None,
        "coupon_message": quote.coupon_message,
        "items_subtotal_cents": quote.items_subtotal_cents,
        "shipping_cents": quote.shipping_cents,
        "vendor_discount_cents": quote.vendor_discount_cents,
        "platform_discount_cents": quote.platform_discount_cents,
        "discount_cents": quote.discount_cents,
        "total_cents": quote.total_cents,
        "problems": messages,
        "can_checkout": bool(cart.lines) and not problems,
        "notes": notes or [],
    }


def view(ctx: Ctx) -> dict:
    cart = get_or_create(ctx.db, ctx.user_id)
    ctx.commit()
    return out(ctx.db, cart, ctx.user_id)


def _touch(cart: Cart) -> None:
    cart.updated_at = utcnow()


def add(ctx: Ctx, variant_id: str, qty: int) -> dict:
    db = ctx.db
    variant, product, _vendor = _sellable(db, variant_id)
    cart = get_or_create(db, ctx.user_id)
    line = next((cl for cl in cart.lines if cl.variant_id == variant_id), None)
    wanted = (line.qty if line else 0) + qty
    if wanted > MAX_QTY:
        raise Unprocessable(f"You can buy at most {MAX_QTY} of one item per order", code="qty_limit")
    if wanted > variant.available:
        raise Conflict(
            f"Only {variant.available} of {product.title} left" if variant.available > 0 else f"{product.title} is sold out",
            code="out_of_stock",
            details={"available": variant.available},
        )
    if line:
        line.qty = wanted
    else:
        db.add(CartLine(cart_id=cart.id, variant_id=variant_id, qty=qty))
    _touch(cart)
    ctx.audit("order", "cart_add", "cart", cart.id, after={"variant_id": variant_id, "qty": wanted})
    ctx.commit()
    return out(db, cart, ctx.user_id)


def set_qty(ctx: Ctx, line_id: int, qty: int) -> dict:
    db = ctx.db
    cart = get_or_create(db, ctx.user_id)
    line = next((cl for cl in cart.lines if cl.id == line_id), None)
    if line is None:
        raise NotFound("Cart line", line_id)
    before = line.qty
    if qty == 0:
        db.delete(line)
    else:
        variant, product, _vendor = _sellable(db, line.variant_id)
        if qty > variant.available:
            raise Conflict(f"Only {variant.available} of {product.title} left", code="out_of_stock", details={"available": variant.available})
        line.qty = qty
    _touch(cart)
    ctx.audit("order", "cart_update" if qty else "cart_remove", "cart", cart.id, before={"variant_id": line.variant_id, "qty": before}, after={"qty": qty})
    ctx.commit()
    return out(db, cart, ctx.user_id)


def remove(ctx: Ctx, line_id: int) -> dict:
    return set_qty(ctx, line_id, 0)


def merge(ctx: Ctx, items: list) -> dict:
    """Merge the guest cart kept in the browser into the account cart after sign-in."""
    db = ctx.db
    cart = get_or_create(db, ctx.user_id)
    notes: list[str] = []
    merged = []
    for item in items:
        try:
            variant, product, _vendor = _sellable(db, item.variant_id)
        except NotFound:
            notes.append("One item from your guest cart is no longer sold and was skipped.")
            continue
        line = next((cl for cl in cart.lines if cl.variant_id == item.variant_id), None)
        wanted = min((line.qty if line else 0) + item.qty, MAX_QTY, variant.available)
        if wanted <= 0:
            notes.append(f"{product.title} is sold out and was not added.")
            continue
        if wanted < (line.qty if line else 0) + item.qty:
            notes.append(f"{product.title}: quantity lowered to {wanted} (stock or the {MAX_QTY}-per-item limit).")
        if line:
            line.qty = wanted
        else:
            line = CartLine(cart_id=cart.id, variant_id=item.variant_id, qty=wanted)
            db.add(line)
            db.flush()
            db.refresh(cart)
        merged.append({"variant_id": item.variant_id, "qty": wanted})
    _touch(cart)
    ctx.audit("order", "cart_merge", "cart", cart.id, after={"items": merged, "notes": notes})
    ctx.commit()
    return out(db, cart, ctx.user_id, notes)


def apply_coupon(ctx: Ctx, code: str) -> dict:
    db = ctx.db
    cart = get_or_create(db, ctx.user_id)
    coupon = coupons.find(db, code)
    reason = coupons.problem(db, coupon, ctx.user_id)
    if reason is None:
        before = cart.coupon_code
        cart.coupon_code = coupon.code
        quote, *_ = build(db, cart, ctx.user_id)
        if quote.coupon is None:
            reason = quote.coupon_message
            cart.coupon_code = before
    if reason:
        raise Unprocessable(reason, code="coupon_rejected", details={"code": code.upper()})
    _touch(cart)
    ctx.audit("coupon", "apply", "cart", cart.id, after={"code": coupon.code, "discount_cents": quote.discount_cents})
    ctx.commit()
    return out(db, cart, ctx.user_id)


def remove_coupon(ctx: Ctx) -> dict:
    db = ctx.db
    cart = get_or_create(db, ctx.user_id)
    before = cart.coupon_code
    cart.coupon_code = None
    _touch(cart)
    ctx.audit("coupon", "remove", "cart", cart.id, before={"code": before}, after={"code": None})
    ctx.commit()
    return out(db, cart, ctx.user_id)
