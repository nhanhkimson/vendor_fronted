"""M6 checkout: stock reservation, simulated card payment, order placement.

1. POST /api/checkout freezes the cart quote in a payment intent and reserves
   stock with a conditional UPDATE (reserved + qty <= on_hand), so two buyers
   can never both get the last unit.
2. POST /api/payments/{id}/confirm locks the intent row. Confirming twice
   returns the same order; a declined card releases the stock and the coupon.
3. Unpaid intents expire after RESERVATION_MINUTES and are released by the
   maintenance loop.
"""

from datetime import datetime, timedelta

from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import system_scope, utcnow
from app.core.deps import Ctx
from app.core.errors import Conflict, NotFound, PaymentDeclined, Unprocessable
from app.core.util import money, new_id
from app.domain.pricing import Quote
from app.models import Cart, PaymentIntent, Product, StockItem, StockReservation
from app.services import cart as carts
from app.services import coupons
from app.services.catalogue import notify_low_stock
from app.services.events import Notice, emit, vendor_staff_ids
from app.services.placement import place_order

TEST_CARDS = {
    "4242 4242 4242 4242": "Approved",
    "4000 0000 0000 0002": "Declined (card_declined)",
    "4000 0000 0000 9995": "Declined (insufficient_funds)",
}
DECLINES = {"4000000000000002": "Your card was declined", "4000000000009995": "Your card has insufficient funds"}


def luhn_ok(number: str) -> bool:
    digits = [int(d) for d in number]
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def intent_out(intent: PaymentIntent) -> dict:
    quote = Quote.from_json(intent.quote)
    return {
        "id": intent.id,
        "status": intent.status,
        "amount_cents": intent.amount_cents,
        "currency": intent.currency,
        "coupon_code": intent.coupon_code,
        "discount_cents": quote.discount_cents,
        "shipping_cents": quote.shipping_cents,
        "expires_at": intent.expires_at,
        "order_id": intent.order_id,
        "failure_reason": intent.failure_reason,
        "groups": [
            {"vendor_id": g.vendor_id, "vendor_name": g.vendor_name, "charged_cents": g.charged_cents, "items": sum(line.qty for line in g.lines)}
            for g in quote.groups
        ],
        "test_cards": TEST_CARDS,
    }


def _reserve(db: Session, intent: PaymentIntent, quote: Quote, expires_at: datetime) -> None:
    with system_scope(db):
        for group in quote.groups:
            for line in group.lines:
                items = db.scalars(select(StockItem).where(StockItem.variant_id == line.variant_id).order_by(StockItem.id)).all()
                taken = None
                for item in items:
                    taken = db.execute(
                        update(StockItem)
                        .where(StockItem.id == item.id, StockItem.on_hand - StockItem.reserved >= line.qty)
                        .values(reserved=StockItem.reserved + line.qty, updated_at=utcnow())
                        .returning(StockItem.id)
                    ).scalar()
                    if taken:
                        break
                if not taken:
                    raise Conflict(
                        f"Someone just bought the last {line.title}. Update your cart and try again.",
                        code="out_of_stock",
                        details={"variant_id": line.variant_id},
                    )
                db.add(
                    StockReservation(
                        payment_intent_id=intent.id,
                        stock_item_id=taken,
                        variant_id=line.variant_id,
                        qty=line.qty,
                        status="active",
                        expires_at=expires_at,
                    )
                )


def release(db: Session, intent: PaymentIntent, status: str, reason: str | None) -> None:
    """Give back reserved stock and the coupon use of an unpaid intent."""
    with system_scope(db):
        reservations = db.scalars(
            select(StockReservation).where(StockReservation.payment_intent_id == intent.id, StockReservation.status == "active")
        ).all()
        for reservation in reservations:
            db.execute(
                update(StockItem)
                .where(StockItem.id == reservation.stock_item_id)
                .values(reserved=StockItem.reserved - reservation.qty, updated_at=utcnow())
            )
            reservation.status = "released"
        if intent.coupon_code:
            coupons.give_back_use(db, intent.coupon_code)
        intent.status = status
        intent.failure_reason = reason


def start_checkout(ctx: Ctx, ship_name: str, ship_address: str) -> dict:
    db = ctx.db
    cart = carts.get_or_create(db, ctx.user_id)
    if not cart.lines:
        raise Conflict("Your cart is empty", code="cart_empty")
    quote, problems, messages, _vendors = carts.build(db, cart, ctx.user_id)
    if problems:
        raise Conflict("Some items need attention before checkout: " + "; ".join(messages), code="cart_problems", details={"problems": messages})
    if cart.coupon_code and quote.coupon is None:
        raise Conflict(f"Coupon {cart.coupon_code} no longer applies: {quote.coupon_message}. Remove it to continue.", code="coupon_rejected")
    if quote.total_cents <= 0:
        raise Conflict("The order total must be more than $0.00", code="zero_total")

    now = utcnow()
    expires_at = now + timedelta(minutes=settings.reservation_minutes)
    intent = PaymentIntent(
        id=new_id("PI", 10),
        user_id=ctx.user_id,
        status="requires_payment",
        amount_cents=quote.total_cents,
        coupon_code=quote.coupon.code if quote.coupon else None,
        ship_name=ship_name.strip(),
        ship_address=ship_address.strip(),
        quote=quote.to_json(),
        created_at=now,
        expires_at=expires_at,
    )
    db.add(intent)
    db.flush()
    if intent.coupon_code and not coupons.take_use(db, intent.coupon_code):
        raise Conflict(f"{intent.coupon_code} has just been fully used. Remove it to continue.", code="coupon_rejected")
    _reserve(db, intent, quote, expires_at)
    ctx.audit(
        "order",
        "checkout",
        "payment_intent",
        intent.id,
        after={
            "amount_cents": intent.amount_cents,
            "coupon": intent.coupon_code,
            "shops": [g.vendor_id for g in quote.groups],
            "reserved_until": expires_at,
        },
    )
    ctx.commit()
    return intent_out(intent)


def get_intent(ctx: Ctx, intent_id: str) -> PaymentIntent:
    intent = ctx.db.get(PaymentIntent, intent_id)
    if intent is None or intent.user_id != ctx.user_id:
        raise NotFound("Payment", intent_id)
    return intent


def next_order_id(db: Session) -> str:
    with system_scope(db):
        number = db.execute(text("SELECT nextval('order_number_seq')")).scalar_one()
    return f"O-{number}"


def confirm(ctx: Ctx, intent_id: str, card_number: str) -> str:
    """Returns the order id. Safe to call twice: the second call returns the same order."""
    db = ctx.db
    intent = db.get(PaymentIntent, intent_id, with_for_update=True, populate_existing=True)
    if intent is None or intent.user_id != ctx.user_id:
        raise NotFound("Payment", intent_id)
    if intent.status == "succeeded":
        ctx.audit(
            "order",
            "create",
            "order",
            intent.order_id,
            after={"payment_intent": intent.id, "repeat": True},
            reason="Payment was already confirmed; returned the existing order",
        )
        ctx.commit()
        return intent.order_id
    if intent.status == "failed":
        raise Conflict(f"This payment was declined ({intent.failure_reason}). Go back to the cart and check out again.", code="payment_failed")
    if intent.status == "expired" or intent.expires_at <= utcnow():
        if intent.status != "expired":
            release(db, intent, "expired", "Checkout window expired")
            ctx.audit("order", "payment_expired", "payment_intent", intent.id, outcome="failed", reason="Checkout window expired")
            ctx.commit()
            ctx.request.state.failure_audited = True
        raise Conflict("This checkout expired and the items were released. Check out again.", code="payment_expired")

    digits = "".join(ch for ch in card_number if ch.isdigit())
    if not 12 <= len(digits) <= 19 or not luhn_ok(digits):
        raise Unprocessable("That card number is not valid. Try 4242 4242 4242 4242.", code="card_invalid")

    if digits in DECLINES:
        reason = DECLINES[digits]
        release(db, intent, "failed", reason)
        ctx.audit("order", "payment_declined", "payment_intent", intent.id, outcome="failed", reason=reason, after={"card_last4": digits[-4:]})
        ctx.commit()
        ctx.request.state.failure_audited = True
        raise PaymentDeclined(f"{reason}. Nothing was charged and your items were released.", details={"payment_intent": intent.id})

    quote = Quote.from_json(intent.quote)
    now = utcnow()
    product_ids = {line.product_id for g in quote.groups for line in g.lines}
    products = {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(product_ids))).all()}
    before_available = {pid: sum(v.available for v in p.variants if v.active) for pid, p in products.items()}

    with system_scope(db):
        reservations = db.scalars(
            select(StockReservation).where(StockReservation.payment_intent_id == intent.id, StockReservation.status == "active")
        ).all()
        for reservation in reservations:
            db.execute(
                update(StockItem)
                .where(StockItem.id == reservation.stock_item_id)
                .values(
                    on_hand=StockItem.on_hand - reservation.qty,
                    reserved=StockItem.reserved - reservation.qty,
                    updated_at=now,
                )
            )
            reservation.status = "committed"
        order_id = next_order_id(db)
        order = place_order(
            db,
            order_id=order_id,
            buyer_id=ctx.user_id,
            quote=quote,
            placed_at=now,
            source=ctx.user.source if quote.coupon is None else "coupon",
            ship_name=intent.ship_name,
            ship_address=intent.ship_address,
            card_last4=digits[-4:],
            payment_intent_id=intent.id,
        )
        intent.status = "succeeded"
        intent.order_id = order_id
        intent.confirmed_at = now
        intent.card_last4 = digits[-4:]

    cart = db.scalar(select(Cart).where(Cart.user_id == ctx.user_id))
    if cart is not None:
        purchased = {line.variant_id for g in quote.groups for line in g.lines}
        for line in list(cart.lines):
            if line.variant_id in purchased:
                db.delete(line)
        if cart.coupon_code == intent.coupon_code:
            cart.coupon_code = None

    notices = [Notice(ctx.user_id, f"Order {order_id} is confirmed: {money(order.total_cents)}", f"/account/orders/{order_id}")]
    for sub in order.sub_orders:
        for uid in vendor_staff_ids(db, sub.vendor_id):
            notices.append(Notice(uid, f"New order {sub.id} to accept ({money(sub.charged_cents)})", "/seller/orders"))
    emit(db, "order.placed", {"order_id": order_id, "sub_orders": [s.id for s in order.sub_orders]}, notices)
    db.flush()
    db.expire_all()
    for pid in products:
        notify_low_stock(db, db.get(Product, pid), before_available[pid])

    ctx.audit(
        "order",
        "create",
        "order",
        order_id,
        after={
            "total_cents": order.total_cents,
            "payment_intent": intent.id,
            "card_last4": intent.card_last4,
            "coupon": order.coupon_code,
            "sub_orders": {s.id: s.charged_cents for s in order.sub_orders},
        },
    )
    ctx.commit()
    return order_id
