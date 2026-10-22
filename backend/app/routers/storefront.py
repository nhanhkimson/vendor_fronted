from fastapi import APIRouter, Depends, Query

from app.core.deps import Ctx, public_ctx
from app.schemas.catalogue import (
    CategoryOut,
    HomeOut,
    ProductDetail,
    ProductPage,
    Promotion,
    ReviewCard,
    ShopCard,
    ShopPage,
    TagOut,
)
from app.schemas.common import Page
from app.services import storefront

router = APIRouter(prefix="/api/store", tags=["Storefront"])


@router.get("/home", response_model=HomeOut, summary="Home page: featured items, shops, promotions")
def home(ctx: Ctx = Depends(public_ctx)):
    return storefront.home(ctx.db)


@router.get("/products", response_model=ProductPage, summary="Search and browse products")
def products(
    q: str | None = Query(default=None, description="Words in the title, description, shop or tags"),
    category: str | None = Query(default=None, description="Category slug; includes sub-categories"),
    tag: str | None = Query(default=None, description="Tag slug"),
    shop: str | None = Query(default=None, description="Shop slug"),
    min_price: int | None = Query(default=None, ge=0, description="Cents"),
    max_price: int | None = Query(default=None, ge=0, description="Cents"),
    in_stock: bool = False,
    sort: str = Query(default="relevance", pattern="^(relevance|popular|rating|price_asc|price_desc|newest)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    ctx: Ctx = Depends(public_ctx),
):
    return storefront.search(
        ctx.db,
        q=q,
        category=category,
        tag=tag,
        shop=shop,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/products/{product_id}", response_model=ProductDetail, summary="Product page with variants and reviews")
def product(product_id: str, ctx: Ctx = Depends(public_ctx)):
    return storefront.product_detail(ctx.db, product_id)


@router.get("/shops", response_model=list[ShopCard], summary="Verified shops")
def shops(ctx: Ctx = Depends(public_ctx)):
    return storefront.shops(ctx.db)


@router.get("/shops/{slug}", response_model=ShopPage, summary="A shop's storefront")
def shop(slug: str, ctx: Ctx = Depends(public_ctx)):
    return storefront.shop_page(ctx.db, slug)


@router.get("/categories", response_model=list[CategoryOut], summary="Category tree with live product counts")
def categories(ctx: Ctx = Depends(public_ctx)):
    from app.services.catalogue import category_tree

    return category_tree(ctx.db)


@router.get("/tags", response_model=list[TagOut], summary="Tags")
def tags(ctx: Ctx = Depends(public_ctx)):
    return storefront.tags(ctx.db)


@router.get("/promotions", response_model=list[Promotion], summary="Coupon codes that are live right now")
def promotions(ctx: Ctx = Depends(public_ctx)):
    return storefront.promotions(ctx.db)


@router.get("/reviews", summary="Published reviews", response_model=Page[ReviewCard])
def reviews(
    shop: str | None = Query(default=None, description="Shop slug or id"),
    min_rating: float | None = Query(default=None, ge=0, le=5),
    theme: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    ctx: Ctx = Depends(public_ctx),
):
    return storefront.review_feed(ctx.db, vendor=shop, min_rating=min_rating, theme=theme, page=page, page_size=page_size)
