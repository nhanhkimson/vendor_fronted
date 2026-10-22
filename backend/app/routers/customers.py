from fastapi import APIRouter, Depends, Query

from app.core.deps import Ctx, audit_meta, authenticated, require
from app.schemas.common import ReasonIn
from app.schemas.trust import (
    CustomerCreate,
    CustomerDetail,
    CustomerOut,
    CustomerUpdate,
    ReviewIn,
    ReviewOut,
    ReviewReplyIn,
    WishlistIn,
    WishlistItemOut,
)
from app.services import customers, reviews, wishlist

router = APIRouter(tags=["M8 Customers & Reviews"])


@router.get("/api/customers", response_model=list[CustomerOut], summary="Customers, with order count and spend")
def list_customers(
    q: str | None = Query(default=None, description="Name, email or city"),
    source: str | None = Query(default=None, description="organic, coupon, social, referral"),
    banned: bool | None = None,
    include_inactive: bool = False,
    ctx: Ctx = Depends(require("customer:read")),
):
    return customers.list_customers(ctx.db, q, source, banned, include_inactive)


@router.post(
    "/api/customers",
    response_model=CustomerOut,
    status_code=201,
    summary="Create a customer account",
    openapi_extra=audit_meta("customer", "create"),
)
def create_customer(body: CustomerCreate, ctx: Ctx = Depends(require("customer:create"))):
    return customers.create_customer(ctx, body)


@router.get("/api/customers/{user_id}", response_model=CustomerDetail, summary="One customer, with recent orders")
def get_customer(user_id: str, ctx: Ctx = Depends(require("customer:read"))):
    return customers.detail(ctx.db, user_id)


@router.patch(
    "/api/customers/{user_id}",
    response_model=CustomerOut,
    summary="Edit a customer's name, email, city or acquisition source",
    openapi_extra=audit_meta("customer", "update"),
)
def update_customer(user_id: str, body: CustomerUpdate, ctx: Ctx = Depends(require("customer:update"))):
    return customers.update_customer(ctx, user_id, body)


@router.post(
    "/api/customers/{user_id}/ban",
    response_model=CustomerOut,
    summary="Ban a customer (reason required). They can sign in but cannot buy, review or message.",
    openapi_extra=audit_meta("customer", "ban"),
)
def ban_customer(user_id: str, body: ReasonIn, ctx: Ctx = Depends(require("customer:ban"))):
    return customers.ban(ctx, user_id, body.reason, lift=False)


@router.post(
    "/api/customers/{user_id}/unban",
    response_model=CustomerOut,
    summary="Lift a ban (reason required)",
    openapi_extra=audit_meta("customer", "unban"),
)
def unban_customer(user_id: str, body: ReasonIn, ctx: Ctx = Depends(require("customer:ban"))):
    return customers.ban(ctx, user_id, body.reason, lift=True)


@router.post(
    "/api/customers/{user_id}/deactivate",
    response_model=CustomerOut,
    summary="Deactivate a customer so they can no longer sign in",
    openapi_extra=audit_meta("customer", "deactivate"),
)
def deactivate_customer(user_id: str, body: ReasonIn, ctx: Ctx = Depends(require("customer:delete"))):
    return customers.deactivate(ctx, user_id, body.reason)


# Reviews ---------------------------------------------------------------------------


@router.get("/api/reviews", response_model=list[ReviewOut], summary="All reviews, including flagged and removed")
def staff_reviews(
    status: str | None = Query(default=None, description="published, flagged, removed"),
    vendor_id: str | None = None,
    product_id: str | None = None,
    ctx: Ctx = Depends(require("review:read")),
):
    return reviews.list_reviews(ctx, status, vendor_id, product_id)


@router.post(
    "/api/reviews/{review_id}/flag",
    response_model=ReviewOut,
    summary="Flag a review for a second look",
    openapi_extra=audit_meta("customer", "flag"),
)
def flag_review(review_id: str, body: ReasonIn, ctx: Ctx = Depends(require("review:moderate"))):
    return reviews.flag_review(ctx, review_id, body.reason)


@router.post(
    "/api/reviews/{review_id}/remove",
    response_model=ReviewOut,
    summary="Remove a review from the store (reason required)",
    openapi_extra=audit_meta("customer", "remove"),
)
def remove_review(review_id: str, body: ReasonIn, ctx: Ctx = Depends(require("review:moderate"))):
    return reviews.remove_review(ctx, review_id, body.reason)


@router.post(
    "/api/reviews/{review_id}/restore",
    response_model=ReviewOut,
    summary="Put a review back on the store",
    openapi_extra=audit_meta("customer", "restore"),
)
def restore_review(review_id: str, body: ReasonIn, ctx: Ctx = Depends(require("review:moderate"))):
    return reviews.restore_review(ctx, review_id, body.reason)


@router.get("/api/account/reviews", response_model=list[ReviewOut], summary="Reviews I have written")
def my_reviews(ctx: Ctx = Depends(require("review:read", "customer"))):
    return reviews.list_reviews(ctx, None, None, None)


@router.post(
    "/api/account/reviews",
    response_model=ReviewOut,
    status_code=201,
    summary="Review an item from a delivered order",
    description="The order must be delivered, and each item can be reviewed once. The review is marked as a verified purchase.",
    openapi_extra=audit_meta("customer", "create_review"),
)
def create_review(body: ReviewIn, ctx: Ctx = Depends(require("review:create", "customer"))):
    return reviews.create_review(ctx, body)


@router.get("/api/seller/reviews", response_model=list[ReviewOut], summary="Reviews of my products")
def seller_reviews(status: str | None = None, ctx: Ctx = Depends(require("review:read", "vendor"))):
    return reviews.list_reviews(ctx, status, None, None)


@router.post(
    "/api/seller/reviews/{review_id}/reply",
    response_model=ReviewOut,
    summary="Reply to a review. The stars stay as the buyer left them.",
    openapi_extra=audit_meta("customer", "respond"),
)
def reply_review(review_id: str, body: ReviewReplyIn, ctx: Ctx = Depends(require("review:respond", "vendor"))):
    return reviews.respond(ctx, review_id, body.response)


# Wishlist -------------------------------------------------------------------------


@router.get("/api/account/wishlist", response_model=list[WishlistItemOut], summary="Products I saved")
def my_wishlist(ctx: Ctx = Depends(authenticated("customer"))):
    return wishlist.list_saved(ctx)


@router.post(
    "/api/account/wishlist",
    response_model=list[WishlistItemOut],
    summary="Save a product",
    openapi_extra=audit_meta("customer", "wishlist_add"),
)
def save_product(body: WishlistIn, ctx: Ctx = Depends(authenticated("customer"))):
    return wishlist.add(ctx, body.product_id)


@router.delete(
    "/api/account/wishlist/{product_id}",
    response_model=list[WishlistItemOut],
    summary="Remove a saved product",
    openapi_extra=audit_meta("customer", "wishlist_remove"),
)
def unsave_product(product_id: str, ctx: Ctx = Depends(authenticated("customer"))):
    return wishlist.remove(ctx, product_id)
