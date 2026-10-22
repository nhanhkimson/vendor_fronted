from fastapi import APIRouter, Depends

from app.core.deps import Ctx, audit_meta, require
from app.schemas.finance import CouponIn, CouponOut, CouponUpdate
from app.services import coupons

router = APIRouter(tags=["M9 Coupons & Promotions"])


@router.get("/api/coupons", response_model=list[CouponOut], summary="All coupons")
def list_coupons(
    vendor_id: str | None = None,
    active_only: bool = False,
    ctx: Ctx = Depends(require("coupon:read")),
):
    return coupons.list_coupons(ctx, vendor_id, active_only)


@router.post(
    "/api/coupons",
    response_model=CouponOut,
    status_code=201,
    summary="Create a platform or vendor coupon",
    description="A platform coupon does not reduce the shop's commission. A vendor coupon is funded by that shop, and commission is charged on the discounted amount.",
    openapi_extra=audit_meta("coupon", "create"),
)
def create_coupon(body: CouponIn, ctx: Ctx = Depends(require("coupon:create"))):
    return coupons.create_coupon(ctx, body)


@router.patch(
    "/api/coupons/{code}",
    response_model=CouponOut,
    summary="Edit a coupon's value, window, limits or pause it",
    openapi_extra=audit_meta("coupon", "update"),
)
def update_coupon(code: str, body: CouponUpdate, ctx: Ctx = Depends(require("coupon:update"))):
    return coupons.update_coupon(ctx, code, body)


@router.delete(
    "/api/coupons/{code}",
    status_code=204,
    summary="Delete a coupon that has never been used",
    openapi_extra=audit_meta("coupon", "delete"),
)
def delete_coupon(code: str, ctx: Ctx = Depends(require("coupon:delete"))):
    coupons.delete_coupon(ctx, code)


@router.get("/api/seller/coupons", response_model=list[CouponOut], summary="Coupons funded by my shop")
def seller_coupons(ctx: Ctx = Depends(require("coupon:read", "vendor"))):
    return coupons.list_coupons(ctx, None, False)


@router.post(
    "/api/seller/coupons",
    response_model=CouponOut,
    status_code=201,
    summary="Create a coupon funded by my shop",
    openapi_extra=audit_meta("coupon", "create"),
)
def seller_create(body: CouponIn, ctx: Ctx = Depends(require("coupon:create", "vendor"))):
    return coupons.create_coupon(ctx, body)


@router.patch(
    "/api/seller/coupons/{code}",
    response_model=CouponOut,
    summary="Edit one of my coupons",
    openapi_extra=audit_meta("coupon", "update"),
)
def seller_update(code: str, body: CouponUpdate, ctx: Ctx = Depends(require("coupon:update", "vendor"))):
    return coupons.update_coupon(ctx, code, body)


@router.delete(
    "/api/seller/coupons/{code}",
    status_code=204,
    summary="Delete one of my coupons if it has never been used",
    openapi_extra=audit_meta("coupon", "delete"),
)
def seller_delete(code: str, ctx: Ctx = Depends(require("coupon:delete", "vendor"))):
    coupons.delete_coupon(ctx, code)
