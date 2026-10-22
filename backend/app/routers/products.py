from fastapi import APIRouter, Depends, File, Query, Response, UploadFile

from app.core.deps import Ctx, audit_meta, require
from app.schemas.catalogue import (
    ImportResult,
    InventoryRow,
    ModerateProductIn,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    StockAdjustIn,
    VariantIn,
    VariantUpdate,
)
from app.schemas.common import Message
from app.services import catalogue

router = APIRouter(tags=["M4 Products & Inventory"])

STATUS = Query(default=None, description="active, inactive, low or archived")


# Vendor (own shop only) --------------------------------------------------------------


@router.get("/api/seller/products", response_model=list[ProductOut], summary="My products with variants and stock")
def my_products(
    q: str | None = None,
    status: str | None = STATUS,
    category: str | None = None,
    ctx: Ctx = Depends(require("product:read", "vendor")),
):
    return catalogue.list_products(ctx.db, vendor_id=ctx.vendor_id, q=q, status=status, category=category)


@router.get("/api/seller/products/export", summary="Download my catalogue as CSV", response_class=Response)
def export_products(ctx: Ctx = Depends(require("product:read", "vendor"))):
    body = catalogue.export_csv(ctx, ctx.vendor_id)
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="bazaar-products.csv"'},
    )


@router.post(
    "/api/seller/products/import",
    response_model=ImportResult,
    summary="Create or update products from CSV (matched by SKU)",
    description="Columns: product_id, title, description, price, category (slug), tags (a|b), sku, size, color, "
    "stock, active. With `dry_run=true` nothing is saved. Any invalid row cancels the whole import.",
    openapi_extra=audit_meta("product", "import"),
)
def import_products(
    file: UploadFile = File(...),
    dry_run: bool = Query(default=False),
    ctx: Ctx = Depends(require("product:import", "vendor")),
):
    result = catalogue.import_csv(ctx, file, dry_run)
    if result["errors"] or dry_run:
        ctx.audit("product", "import", "product", None, outcome="failed" if result["errors"] else "success", after={"dry_run": dry_run, "errors": len(result["errors"])})
        ctx.commit()
    return result


@router.post(
    "/api/seller/products",
    response_model=ProductOut,
    status_code=201,
    summary="List a new product",
    openapi_extra=audit_meta("product", "create"),
)
def create_product(body: ProductCreate, ctx: Ctx = Depends(require("product:create", "vendor"))):
    return catalogue.create_product(ctx, body)


@router.get("/api/seller/products/{product_id}", response_model=ProductOut, summary="One of my products")
def my_product(product_id: str, ctx: Ctx = Depends(require("product:read", "vendor"))):
    return catalogue.one(ctx.db, catalogue.get_product(ctx, product_id))


@router.patch(
    "/api/seller/products/{product_id}",
    response_model=ProductOut,
    summary="Edit title, price, category, threshold or visibility",
    openapi_extra=audit_meta("product", "update"),
)
def update_product(product_id: str, body: ProductUpdate, ctx: Ctx = Depends(require("product:update", "vendor"))):
    return catalogue.update_product(ctx, product_id, body)


@router.delete(
    "/api/seller/products/{product_id}",
    response_model=Message,
    summary="Archive a product (kept for order history)",
    openapi_extra=audit_meta("product", "delete"),
)
def archive_product(product_id: str, ctx: Ctx = Depends(require("product:delete", "vendor"))):
    catalogue.archive_product(ctx, product_id)
    return Message(detail=f"Product {product_id} archived")


@router.post(
    "/api/seller/products/{product_id}/restore",
    response_model=ProductOut,
    summary="Restore an archived product",
    openapi_extra=audit_meta("product", "restore"),
)
def restore_product(product_id: str, ctx: Ctx = Depends(require("product:update", "vendor"))):
    return catalogue.restore_product(ctx, product_id)


@router.post(
    "/api/seller/products/{product_id}/variants",
    response_model=ProductOut,
    status_code=201,
    summary="Add a size or colour variant with starting stock",
    openapi_extra=audit_meta("product", "add_variant"),
)
def add_variant(product_id: str, body: VariantIn, ctx: Ctx = Depends(require("product:update", "vendor"))):
    return catalogue.add_variant(ctx, product_id, body)


@router.patch(
    "/api/seller/variants/{variant_id}",
    response_model=ProductOut,
    summary="Edit a variant's SKU, size, colour or availability",
    openapi_extra=audit_meta("product", "update_variant"),
)
def update_variant(variant_id: str, body: VariantUpdate, ctx: Ctx = Depends(require("product:update", "vendor"))):
    return catalogue.update_variant(ctx, variant_id, body)


@router.post(
    "/api/seller/products/{product_id}/image",
    response_model=ProductOut,
    summary="Upload a product photo (JPEG, PNG or WebP, up to 5 MB)",
    openapi_extra=audit_meta("product", "upload_image"),
)
def upload_image(product_id: str, file: UploadFile = File(...), ctx: Ctx = Depends(require("product:update", "vendor"))):
    return catalogue.upload_image(ctx, product_id, file)


@router.get("/api/seller/inventory", response_model=list[InventoryRow], summary="My stock per variant and warehouse")
def my_inventory(low: bool = False, ctx: Ctx = Depends(require("stock:read", "vendor"))):
    return catalogue.inventory(ctx.db, ctx.vendor_id, low)


@router.post(
    "/api/seller/inventory/{variant_id}/adjust",
    response_model=InventoryRow,
    summary="Restock or correct stock (reason required)",
    description="Send `delta` (for example 10 or -2) or `set_to`. On-hand can never drop below "
    "units reserved by open checkouts. Crossing the low-stock threshold notifies the shop.",
    openapi_extra=audit_meta("product", "adjust_stock"),
)
def adjust_stock(variant_id: str, body: StockAdjustIn, ctx: Ctx = Depends(require("stock:adjust", "vendor"))):
    return catalogue.adjust_stock(ctx, variant_id, body.delta, body.set_to, body.reason)


# Staff (every shop) ------------------------------------------------------------------


@router.get("/api/products", response_model=list[ProductOut], summary="All products across shops")
def all_products(
    vendor_id: str | None = None,
    q: str | None = None,
    status: str | None = STATUS,
    category: str | None = None,
    ctx: Ctx = Depends(require("product:read")),
):
    return catalogue.list_products(ctx.db, vendor_id=vendor_id, q=q, status=status, category=category)


@router.post(
    "/api/products/{product_id}/moderate",
    response_model=ProductOut,
    summary="Hide or re-list a product, or fix its category (reason required)",
    openapi_extra=audit_meta("product", "moderate"),
)
def moderate(product_id: str, body: ModerateProductIn, ctx: Ctx = Depends(require("product:update"))):
    return catalogue.moderate_product(ctx, product_id, body.active, body.reason, body.category_id)


@router.get("/api/inventory", response_model=list[InventoryRow], summary="Stock across shops")
def all_inventory(vendor_id: str | None = None, low: bool = False, ctx: Ctx = Depends(require("stock:read"))):
    return catalogue.inventory(ctx.db, vendor_id, low)
