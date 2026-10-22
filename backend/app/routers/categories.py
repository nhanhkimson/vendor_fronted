from fastapi import APIRouter, Depends

from app.core.deps import Ctx, audit_meta, require
from app.schemas.catalogue import CategoryCreate, CategoryOut, CategoryUpdate, ProductOut, TagCreate, TagOut, TagsIn
from app.schemas.common import Message
from app.services import catalogue

router = APIRouter(tags=["M5 Categories & Tags"])


@router.get("/api/categories", response_model=list[CategoryOut], summary="Category tree with product counts (all products)")
def categories(ctx: Ctx = Depends(require("category:read"))):
    return catalogue.category_tree(ctx.db, active_only=False)


@router.post(
    "/api/categories",
    response_model=CategoryOut,
    status_code=201,
    summary="Create a category (unique slug)",
    openapi_extra=audit_meta("category", "create"),
)
def create_category(body: CategoryCreate, ctx: Ctx = Depends(require("category:create"))):
    return catalogue.create_category(ctx, body)


@router.patch(
    "/api/categories/{category_id}",
    response_model=CategoryOut,
    summary="Rename, re-slug or move a category",
    description="Moving a category under one of its own sub-categories is refused with 409 (cycle check).",
    openapi_extra=audit_meta("category", "update"),
)
def update_category(category_id: str, body: CategoryUpdate, ctx: Ctx = Depends(require("category:update"))):
    return catalogue.update_category(ctx, category_id, body)


@router.delete(
    "/api/categories/{category_id}",
    response_model=Message,
    summary="Delete an empty category",
    description="Refused while it has sub-categories or products.",
    openapi_extra=audit_meta("category", "delete"),
)
def delete_category(category_id: str, ctx: Ctx = Depends(require("category:delete"))):
    catalogue.delete_category(ctx, category_id)
    return Message(detail=f"Category {category_id} deleted")


@router.get("/api/tags", response_model=list[TagOut], summary="Tags with usage counts")
def tags(ctx: Ctx = Depends(require("category:read"))):
    return catalogue.list_tags(ctx.db)


@router.post(
    "/api/tags",
    response_model=TagOut,
    status_code=201,
    summary="Create a tag",
    openapi_extra=audit_meta("category", "create_tag"),
)
def create_tag(body: TagCreate, ctx: Ctx = Depends(require("tag:create"))):
    return catalogue.create_tag(ctx, body.name)


@router.delete(
    "/api/tags/{tag_id}",
    response_model=Message,
    summary="Delete a tag and remove it from products",
    openapi_extra=audit_meta("category", "delete_tag"),
)
def delete_tag(tag_id: str, ctx: Ctx = Depends(require("tag:delete"))):
    catalogue.delete_tag(ctx, tag_id)
    return Message(detail=f"Tag {tag_id} deleted")


@router.put(
    "/api/products/{product_id}/tags",
    response_model=ProductOut,
    summary="Set a product's tags (staff)",
    openapi_extra=audit_meta("category", "assign_tags"),
)
def set_tags(product_id: str, body: TagsIn, ctx: Ctx = Depends(require("tag:assign"))):
    return catalogue.set_tags(ctx, product_id, body.tag_ids)


@router.put(
    "/api/seller/products/{product_id}/tags",
    response_model=ProductOut,
    summary="Set my product's tags",
    openapi_extra=audit_meta("category", "assign_tags"),
)
def set_my_tags(product_id: str, body: TagsIn, ctx: Ctx = Depends(require("tag:assign", "vendor"))):
    return catalogue.set_tags(ctx, product_id, body.tag_ids)
