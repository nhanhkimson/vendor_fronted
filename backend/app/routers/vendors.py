from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile

from app.core.deps import Ctx, audit_meta, authenticated, principal_for, require
from app.routers.auth import me_out, set_session_cookie
from app.schemas.catalogue import (
    DocumentReviewIn,
    ShopUpdate,
    TierIn,
    TierOut,
    VendorCreate,
    VendorOut,
    VendorUpdate,
)
from app.schemas.common import Message, ReasonIn
from app.schemas.identity import MeOut
from app.services import vendors

router = APIRouter(tags=["M3 Vendors"])


# Staff ----------------------------------------------------------------------------


@router.get("/api/vendors", response_model=list[VendorOut], summary="All vendors with status, documents and history")
def list_vendors(
    status: str | None = Query(default=None, description="draft, under_review, active, suspended, rejected"),
    q: str | None = Query(default=None, description="Name, city or id"),
    tier: str | None = None,
    include_deleted: bool = False,
    ctx: Ctx = Depends(require("vendor:read")),
):
    return vendors.list_vendors(ctx.db, status, q, tier, include_deleted)


@router.get("/api/vendors/tiers", response_model=list[TierOut], summary="Commission tiers and their current rates")
def tiers(ctx: Ctx = Depends(require("vendor:read"))):
    return vendors.tiers(ctx.db)


@router.get("/api/vendors/{vendor_id}", response_model=VendorOut, summary="One vendor")
def get_vendor(vendor_id: str, ctx: Ctx = Depends(require("vendor:read"))):
    return vendors.vendor_out(ctx.db, vendors.get_vendor(ctx.db, vendor_id), staff_view=True)


@router.post(
    "/api/vendors",
    response_model=VendorOut,
    status_code=201,
    summary="Create a vendor on someone's behalf (starts as draft)",
    openapi_extra=audit_meta("vendor", "create"),
)
def create_vendor(body: VendorCreate, ctx: Ctx = Depends(require("vendor:create"))):
    return vendors.create_vendor(ctx, body)


@router.patch(
    "/api/vendors/{vendor_id}",
    response_model=VendorOut,
    summary="Edit a vendor's profile, shipping fee, warehouse or internal notes",
    openapi_extra=audit_meta("vendor", "update"),
)
def update_vendor(vendor_id: str, body: VendorUpdate, ctx: Ctx = Depends(require("vendor:update"))):
    return vendors.update_vendor(ctx, vendor_id, body)


@router.post(
    "/api/vendors/{vendor_id}/verify",
    response_model=VendorOut,
    summary="Verify a vendor (under review to active)",
    description="Every document must be approved first. The shop goes live on the storefront.",
    openapi_extra=audit_meta("vendor", "verify"),
)
def verify(vendor_id: str, ctx: Ctx = Depends(require("vendor:verify"))):
    return vendors.verify(ctx, vendor_id)


@router.post(
    "/api/vendors/{vendor_id}/reject",
    response_model=VendorOut,
    summary="Reject an application (reason required)",
    openapi_extra=audit_meta("vendor", "reject"),
)
def reject(vendor_id: str, body: ReasonIn, ctx: Ctx = Depends(require("vendor:verify"))):
    return vendors.reject(ctx, vendor_id, body.reason)


@router.post(
    "/api/vendors/{vendor_id}/suspend",
    response_model=VendorOut,
    summary="Suspend a vendor (reason required); their products disappear from the store",
    openapi_extra=audit_meta("vendor", "suspend"),
)
def suspend(vendor_id: str, body: ReasonIn, ctx: Ctx = Depends(require("vendor:suspend"))):
    return vendors.suspend(ctx, vendor_id, body.reason)


@router.post(
    "/api/vendors/{vendor_id}/reinstate",
    response_model=VendorOut,
    summary="Reinstate a suspended vendor (reason required)",
    openapi_extra=audit_meta("vendor", "reinstate"),
)
def reinstate(vendor_id: str, body: ReasonIn, ctx: Ctx = Depends(require("vendor:suspend"))):
    return vendors.reinstate(ctx, vendor_id, body.reason)


@router.put(
    "/api/vendors/{vendor_id}/tier",
    response_model=VendorOut,
    summary="Move a vendor to another commission tier",
    description="Applies to orders placed from now on. Past orders keep their frozen commission.",
    openapi_extra=audit_meta("vendor", "assign_tier"),
)
def assign_tier(vendor_id: str, body: TierIn, ctx: Ctx = Depends(require("vendor:assign_tier"))):
    return vendors.assign_tier(ctx, vendor_id, body.tier_id, body.reason)


@router.delete(
    "/api/vendors/{vendor_id}",
    response_model=Message,
    summary="Delete a vendor",
    description="Refused (409) while the vendor has open orders or payouts in progress. "
    "Products are hidden and staff lose Seller Central access; history is kept.",
    openapi_extra=audit_meta("vendor", "delete"),
)
def delete_vendor(vendor_id: str, ctx: Ctx = Depends(require("vendor:delete"))):
    vendors.delete_vendor(ctx, vendor_id)
    return Message(detail=f"Vendor {vendor_id} deleted")


@router.post(
    "/api/vendors/{vendor_id}/documents/{doc_id}/review",
    response_model=VendorOut,
    summary="Approve or reject one identity document",
    openapi_extra=audit_meta("vendor", "review_document"),
)
def review_document(vendor_id: str, doc_id: str, body: DocumentReviewIn, ctx: Ctx = Depends(require("vendor:verify"))):
    return vendors.review_document(ctx, vendor_id, doc_id, body.decision, body.reason)


@router.get(
    "/api/vendors/{vendor_id}/documents/{doc_id}/file",
    summary="Open an identity document (staff with vendor:verify; every view is logged)",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}, "image/png": {}, "image/jpeg": {}}}},
)
def document_file(vendor_id: str, doc_id: str, ctx: Ctx = Depends(require("vendor:verify"))):
    return vendors.document_file(ctx, vendor_id, doc_id)


# Vendor self-service ---------------------------------------------------------------


@router.get("/api/seller/shop", response_model=VendorOut, summary="My shop: status, tier, documents")
def my_shop(ctx: Ctx = Depends(require("vendor:read", "vendor"))):
    return vendors.my_shop(ctx)


@router.patch(
    "/api/seller/shop",
    response_model=VendorOut,
    summary="Edit my storefront and shipping settings",
    openapi_extra=audit_meta("vendor", "update_shop"),
)
def update_shop(body: ShopUpdate, ctx: Ctx = Depends(require("vendor:update", "vendor"))):
    return vendors.update_shop(ctx, body)


@router.post(
    "/api/seller/shop/image",
    response_model=VendorOut,
    summary="Upload my storefront banner (JPEG, PNG or WebP, up to 5 MB)",
    openapi_extra=audit_meta("vendor", "upload_image"),
)
def upload_shop_image(file: UploadFile = File(...), ctx: Ctx = Depends(require("vendor:update", "vendor"))):
    return vendors.upload_shop_image(ctx, file)


@router.post(
    "/api/seller/documents/{doc_id}",
    response_model=VendorOut,
    summary="Upload or replace one of my identity documents (PDF, JPEG or PNG)",
    openapi_extra=audit_meta("vendor", "upload_document"),
)
def upload_document(doc_id: str, file: UploadFile = File(...), ctx: Ctx = Depends(require("vendor:update", "vendor"))):
    return vendors.upload_document(ctx, doc_id, file)


@router.get(
    "/api/seller/documents/{doc_id}/file",
    summary="Open one of my documents",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}, "image/png": {}, "image/jpeg": {}}}},
)
def my_document_file(doc_id: str, ctx: Ctx = Depends(require("vendor:read", "vendor"))):
    return vendors.my_document_file(ctx, doc_id)


@router.post(
    "/api/seller/shop/submit",
    response_model=VendorOut,
    summary="Send my shop for verification (draft or rejected to under review)",
    openapi_extra=audit_meta("vendor", "submit_application"),
)
def submit_for_review(ctx: Ctx = Depends(require("vendor:update", "vendor"))):
    return vendors.submit_for_review(ctx)


@router.post(
    "/api/vendor-applications",
    response_model=MeOut,
    status_code=201,
    summary="Sell on Bazaar: open a shop with your documents",
    description="Any signed-in customer can apply. With all three documents attached the shop goes "
    "straight to review; otherwise it stays a draft until they are uploaded in Seller Central. "
    "The session cookie is refreshed so Seller Central opens immediately.",
    openapi_extra=audit_meta("vendor", "submit_application"),
)
def apply(
    response: Response,
    name: str = Form(min_length=2, max_length=120),
    country: str = Form(default="US", min_length=2, max_length=2),
    city: str = Form(default="", max_length=120),
    headline: str = Form(default="", max_length=160),
    about: str = Form(default="", max_length=4000),
    government_id: UploadFile | None = File(default=None),
    address_proof: UploadFile | None = File(default=None),
    payout_account: UploadFile | None = File(default=None),
    ctx: Ctx = Depends(authenticated("customer")),
):
    vendors.apply(
        ctx,
        name=name,
        country=country,
        city=city,
        headline=headline,
        about=about,
        uploads={"government_id": government_id, "address_proof": address_proof, "payout_account": payout_account},
    )
    ctx.db.refresh(ctx.user)
    principal = principal_for(ctx.user, ctx.principal.via)
    if ctx.principal.via == "cookie":
        set_session_cookie(response, principal)
    return me_out(ctx.db, principal)
