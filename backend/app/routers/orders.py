from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.core.deps import Ctx, audit_meta, require
from app.schemas.orders import (
    CancelIn,
    CartItemIn,
    CartMergeIn,
    CartOut,
    CartQtyIn,
    CheckoutIn,
    ConfirmIn,
    CouponIn,
    DisputeIn,
    DisputeOut,
    OrderOut,
    PaymentIntentOut,
    ResolveIn,
    ShipIn,
    StaffStatusIn,
    SubOrderOut,
)
from app.services import cart, checkout, disputes, fulfilment

router = APIRouter(tags=["M6 Orders & Fulfilment"])


# Cart ---------------------------------------------------------------------------------


@router.get("/api/cart", response_model=CartOut, summary="My cart, grouped by shop, with live prices and stock")
def view_cart(ctx: Ctx = Depends(require("order:create", "customer"))):
    return cart.view(ctx)


@router.post(
    "/api/cart/items",
    response_model=CartOut,
    summary="Add an item (or more of it) to my cart",
    openapi_extra=audit_meta("order", "cart_add"),
)
def add_to_cart(body: CartItemIn, ctx: Ctx = Depends(require("order:create", "customer"))):
    return cart.add(ctx, body.variant_id, body.qty)


@router.patch(
    "/api/cart/items/{line_id}",
    response_model=CartOut,
    summary="Change the quantity of a cart line (0 removes it)",
    openapi_extra=audit_meta("order", "cart_update"),
)
def update_cart_line(line_id: int, body: CartQtyIn, ctx: Ctx = Depends(require("order:create", "customer"))):
    return cart.set_qty(ctx, line_id, body.qty)


@router.delete(
    "/api/cart/items/{line_id}",
    response_model=CartOut,
    summary="Remove a cart line",
    openapi_extra=audit_meta("order", "cart_remove"),
)
def remove_cart_line(line_id: int, ctx: Ctx = Depends(require("order:create", "customer"))):
    return cart.remove(ctx, line_id)


@router.post(
    "/api/cart/merge",
    response_model=CartOut,
    summary="Merge the guest cart from this browser after signing in",
    description="Quantities are capped by stock and the 10-per-item limit; `notes` explains anything that changed.",
    openapi_extra=audit_meta("order", "cart_merge"),
)
def merge_cart(body: CartMergeIn, ctx: Ctx = Depends(require("order:create", "customer"))):
    return cart.merge(ctx, body.items)


@router.post(
    "/api/cart/coupon",
    response_model=CartOut,
    tags=["M9 Coupons & Promotions"],
    summary="Apply a coupon code to my cart",
    description="Try `WELCOME10` (platform-funded) or `ANNE5` (Anne's Jewelry only). Errors explain exactly why a code does not apply.",
    openapi_extra=audit_meta("coupon", "apply"),
)
def apply_coupon(body: CouponIn, ctx: Ctx = Depends(require("coupon:apply", "customer"))):
    return cart.apply_coupon(ctx, body.code)


@router.delete(
    "/api/cart/coupon",
    response_model=CartOut,
    tags=["M9 Coupons & Promotions"],
    summary="Remove the coupon from my cart",
    openapi_extra=audit_meta("coupon", "remove"),
)
def remove_coupon(ctx: Ctx = Depends(require("coupon:apply", "customer"))):
    return cart.remove_coupon(ctx)


# Checkout and payment -----------------------------------------------------------------


@router.post(
    "/api/checkout",
    response_model=PaymentIntentOut,
    status_code=201,
    summary="Start checkout: freeze prices and reserve stock for 15 minutes",
    openapi_extra=audit_meta("order", "checkout"),
)
def start_checkout(body: CheckoutIn, ctx: Ctx = Depends(require("order:create", "customer"))):
    return checkout.start_checkout(ctx, body.ship_name, body.ship_address)


@router.get("/api/payments/{intent_id}", response_model=PaymentIntentOut, summary="A checkout payment and its status")
def get_payment(intent_id: str, ctx: Ctx = Depends(require("order:create", "customer"))):
    return checkout.intent_out(checkout.get_intent(ctx, intent_id))


@router.post(
    "/api/payments/{intent_id}/confirm",
    response_model=OrderOut,
    summary="Pay with a test card and place the order",
    description=(
        "Simulated card payment. `4242 4242 4242 4242` succeeds, `4000 0000 0000 0002` is declined (402) and "
        "releases the stock. Confirming twice returns the same order. One order is split into one sub-order per shop."
    ),
    openapi_extra=audit_meta("order", "create"),
)
def confirm_payment(intent_id: str, body: ConfirmIn, ctx: Ctx = Depends(require("order:create", "customer"))):
    order_id = checkout.confirm(ctx, intent_id, body.card_number)
    return fulfilment.my_order(ctx, order_id)


# Customer: my orders ------------------------------------------------------------------


@router.get("/api/account/orders", response_model=list[OrderOut], summary="My orders, newest first")
def my_orders(ctx: Ctx = Depends(require("order:read", "customer"))):
    return fulfilment.my_orders(ctx)


@router.get("/api/account/orders/{order_id}", response_model=OrderOut, summary="One of my orders with tracking per shop")
def my_order(order_id: str, ctx: Ctx = Depends(require("order:read", "customer"))):
    return fulfilment.my_order(ctx, order_id)


@router.post(
    "/api/account/sub-orders/{sub_id}/cancel",
    response_model=OrderOut,
    summary="Cancel my order from one shop (before it is packed); refunds automatically",
    openapi_extra=audit_meta("order", "cancel"),
)
def customer_cancel(sub_id: str, body: CancelIn, ctx: Ctx = Depends(require("order:cancel", "customer"))):
    sub = fulfilment.customer_sub_order(ctx, sub_id)
    fulfilment.cancel(ctx, sub, body.reason, "customer")
    return fulfilment.my_order(ctx, sub.order_id)


@router.post(
    "/api/account/sub-orders/{sub_id}/confirm-delivery",
    response_model=OrderOut,
    summary="Confirm that a shipment arrived",
    openapi_extra=audit_meta("order", "confirm_delivery"),
)
def confirm_delivery(sub_id: str, ctx: Ctx = Depends(require("order:confirm_delivery", "customer"))):
    sub = fulfilment.customer_sub_order(ctx, sub_id)
    fulfilment.confirm_delivery(ctx, sub)
    return fulfilment.my_order(ctx, sub.order_id)


@router.post(
    "/api/account/sub-orders/{sub_id}/dispute",
    response_model=DisputeOut,
    status_code=201,
    summary="Open a dispute on one shop's part of my order",
    description="Allowed once shipped and up to 7 days after delivery. The shop's unpaid payouts are frozen until support resolves it.",
    openapi_extra=audit_meta("order", "open_dispute"),
)
def open_dispute(sub_id: str, body: DisputeIn, ctx: Ctx = Depends(require("dispute:create", "customer"))):
    sub = fulfilment.customer_sub_order(ctx, sub_id)
    return disputes.open_dispute(ctx, sub, body.reason, body.note)


# Vendor: my shop's orders -------------------------------------------------------------


@router.get("/api/seller/orders", response_model=list[SubOrderOut], summary="Orders for my shop")
def seller_orders(
    status: str | None = Query(default=None, description="open, pending_acceptance, accepted, packing, shipped, delivered, cancelled, refunded"),
    q: str | None = Query(default=None, description="Order id or tracking number"),
    ctx: Ctx = Depends(require("order:read", "vendor")),
):
    return fulfilment.vendor_orders(ctx, status, q)


@router.get("/api/seller/orders/{sub_id}", response_model=SubOrderOut, summary="One order for my shop")
def seller_order(sub_id: str, ctx: Ctx = Depends(require("order:read", "vendor"))):
    return fulfilment.sub_order_out(ctx.db, fulfilment.vendor_sub_order(ctx, sub_id), "vendor")


def _vendor_move(ctx: Ctx, sub_id: str, target: str, action: str, **kwargs) -> dict:
    sub = fulfilment.vendor_sub_order(ctx, sub_id)
    fulfilment.move(ctx, sub, target, role="vendor", action=action, **kwargs)
    return fulfilment.sub_order_out(ctx.db, sub, "vendor")


@router.post(
    "/api/seller/orders/{sub_id}/accept",
    response_model=SubOrderOut,
    summary="Accept a new order",
    openapi_extra=audit_meta("order", "accept"),
)
def seller_accept(sub_id: str, ctx: Ctx = Depends(require("order:update_status", "vendor"))):
    return _vendor_move(ctx, sub_id, "accepted", "accept")


@router.post(
    "/api/seller/orders/{sub_id}/pack",
    response_model=SubOrderOut,
    summary="Start packing",
    openapi_extra=audit_meta("order", "pack"),
)
def seller_pack(sub_id: str, ctx: Ctx = Depends(require("order:update_status", "vendor"))):
    return _vendor_move(ctx, sub_id, "packing", "pack")


@router.post(
    "/api/seller/orders/{sub_id}/ship",
    response_model=SubOrderOut,
    summary="Mark shipped with a tracking number (required)",
    openapi_extra=audit_meta("order", "ship"),
)
def seller_ship(sub_id: str, body: ShipIn, ctx: Ctx = Depends(require("order:add_tracking", "vendor"))):
    return _vendor_move(ctx, sub_id, "shipped", "ship", tracking=body.tracking_number, carrier=body.carrier)


@router.post(
    "/api/seller/orders/{sub_id}/deliver",
    response_model=SubOrderOut,
    summary="Mark delivered (carrier confirmed)",
    openapi_extra=audit_meta("order", "deliver"),
)
def seller_deliver(sub_id: str, ctx: Ctx = Depends(require("order:update_status", "vendor"))):
    return _vendor_move(ctx, sub_id, "delivered", "deliver")


@router.post(
    "/api/seller/orders/{sub_id}/cancel",
    response_model=SubOrderOut,
    summary="Cancel before shipping (reason required); the buyer is refunded and stock returns",
    openapi_extra=audit_meta("order", "cancel"),
)
def seller_cancel(sub_id: str, body: CancelIn, ctx: Ctx = Depends(require("order:cancel", "vendor"))):
    sub = fulfilment.vendor_sub_order(ctx, sub_id)
    fulfilment.cancel(ctx, sub, body.reason, "vendor")
    return fulfilment.sub_order_out(ctx.db, sub, "vendor")


@router.get("/api/seller/disputes", response_model=list[DisputeOut], summary="Disputes on my shop's orders")
def seller_disputes(status: str | None = None, ctx: Ctx = Depends(require("dispute:read", "vendor"))):
    return disputes.list_disputes(ctx, status)


# Staff ---------------------------------------------------------------------------------


@router.get("/api/orders", response_model=list[OrderOut], summary="All orders (newest 200), with commission per line")
def staff_orders(
    status: str | None = Query(default=None, description="paid, partially_fulfilled, fulfilled, completed, partially_refunded, refunded, cancelled"),
    vendor_id: str | None = None,
    q: str | None = Query(default=None, description="Order id, buyer name or email"),
    since: datetime | None = None,
    ctx: Ctx = Depends(require("order:read")),
):
    return fulfilment.staff_orders(ctx, status, vendor_id, q, since)


@router.get("/api/orders/{order_id}", response_model=OrderOut, summary="One order with every shop's part")
def staff_order(order_id: str, ctx: Ctx = Depends(require("order:read"))):
    return fulfilment.staff_order(ctx, order_id)


@router.post(
    "/api/orders/sub-orders/{sub_id}/status",
    response_model=OrderOut,
    summary="Move a sub-order on the shop's behalf (note required)",
    description="Follows the same state machine as the shop. Shipping still needs a tracking number.",
    openapi_extra=audit_meta("order", "update_status"),
)
def staff_status(sub_id: str, body: StaffStatusIn, ctx: Ctx = Depends(require("order:update_status"))):
    sub = fulfilment.staff_sub_order(ctx, sub_id)
    fulfilment.move(ctx, sub, body.status, role="staff", note=body.note, tracking=body.tracking_number, carrier=body.carrier)
    return fulfilment.staff_order(ctx, sub.order_id)


@router.post(
    "/api/orders/sub-orders/{sub_id}/cancel",
    response_model=OrderOut,
    summary="Cancel a sub-order before shipping (reason required); refunds automatically",
    openapi_extra=audit_meta("order", "cancel"),
)
def staff_cancel(sub_id: str, body: CancelIn, ctx: Ctx = Depends(require("order:cancel"))):
    sub = fulfilment.staff_sub_order(ctx, sub_id)
    fulfilment.cancel(ctx, sub, body.reason, "staff")
    return fulfilment.staff_order(ctx, sub.order_id)


@router.get("/api/disputes", response_model=list[DisputeOut], summary="All disputes")
def staff_disputes(
    status: str | None = Query(default=None, description="open, resolved_refund, resolved_rejected"),
    ctx: Ctx = Depends(require("dispute:read")),
):
    return disputes.list_disputes(ctx, status)


@router.get("/api/disputes/{dispute_id}", response_model=DisputeOut, summary="One dispute")
def staff_dispute(dispute_id: str, ctx: Ctx = Depends(require("dispute:read"))):
    return fulfilment.dispute_out(ctx.db, disputes.get(ctx.db, dispute_id))


@router.post(
    "/api/disputes/{dispute_id}/resolve",
    response_model=DisputeOut,
    summary="Resolve a dispute: refund the buyer or reject (note required)",
    description="Either way the shop's frozen payouts are released once no other dispute is open.",
    openapi_extra=audit_meta("order", "resolve_dispute"),
)
def resolve_dispute(dispute_id: str, body: ResolveIn, ctx: Ctx = Depends(require("dispute:resolve"))):
    return disputes.resolve(ctx, dispute_id, body.outcome, body.note)
