from datetime import date, datetime

from pydantic import Field

from app.schemas.common import Cents, Schema

# Vendors -----------------------------------------------------------------------


class TierOut(Schema):
    id: str
    name: str
    name_kh: str | None
    min_sales: int
    max_sales: int | None
    rate_bps: int | None = None


class DocumentOut(Schema):
    id: str
    kind: str
    name: str
    status: str
    original_filename: str | None
    uploaded_at: datetime | None
    reviewed_by: str | None
    reviewed_at: datetime | None
    has_file: bool


class VendorEventOut(Schema):
    from_status: str | None
    to_status: str
    actor_id: str | None
    reason: str | None
    at: datetime


class ShopCard(Schema):
    """Public shop summary."""

    id: str
    name: str
    slug: str
    country: str
    city: str
    headline: str
    image_url: str | None
    hue: int
    rating: float | None
    rating_flag: str
    review_count: int
    lifetime_sales: int
    since: date | None
    response_hours: int
    tier_id: str
    tier_name: str
    product_count: int = 0
    shipping_fee_cents: int
    processing_days: int


class ShopDetail(ShopCard):
    about: str
    catalog_size: str


class VendorOut(ShopDetail):
    """Full vendor record for staff and for the vendor's own Seller Central."""

    status: str
    status_reason: str | None
    verified_at: datetime | None
    warehouse_id: str | None
    warehouse_name: str | None
    payout_account: str | None
    internal_notes: str | None = None
    is_outlier: bool
    response_flag: str
    deleted_at: datetime | None
    created_at: datetime
    open_sub_orders: int = 0
    staff: list[dict] = []
    documents: list[DocumentOut] = []
    history: list[VendorEventOut] = []
    allowed_actions: list[str] = []


class VendorCreate(Schema):
    name: str = Field(min_length=2, max_length=120)
    country: str = Field(default="US", min_length=2, max_length=2)
    city: str = Field(default="", max_length=120)
    headline: str = Field(default="", max_length=160)
    about: str = Field(default="", max_length=4000)
    shipping_fee_cents: Cents = 500
    owner_user_id: str | None = Field(default=None, description="Existing user who will run the shop")


class VendorUpdate(Schema):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    headline: str | None = Field(default=None, max_length=160)
    about: str | None = Field(default=None, max_length=4000)
    shipping_fee_cents: Cents | None = None
    processing_days: int | None = Field(default=None, ge=1, le=30)
    warehouse_id: str | None = None
    internal_notes: str | None = Field(default=None, max_length=4000)


class ShopUpdate(Schema):
    headline: str | None = Field(default=None, max_length=160)
    about: str | None = Field(default=None, max_length=4000)
    city: str | None = Field(default=None, max_length=120)
    shipping_fee_cents: Cents | None = None
    processing_days: int | None = Field(default=None, ge=1, le=30)
    payout_account: str | None = Field(default=None, max_length=60)


class TierIn(Schema):
    tier_id: str
    reason: str = Field(min_length=3, max_length=255)


class DocumentReviewIn(Schema):
    decision: str = Field(pattern="^(verified|rejected)$")
    reason: str | None = Field(default=None, max_length=255)


# Catalogue ---------------------------------------------------------------------


class CategoryOut(Schema):
    id: str
    name: str
    name_kh: str | None
    slug: str
    parent_id: str | None
    sort: int
    product_count: int = 0
    path: list[str] = []


class CategoryCreate(Schema):
    name: str = Field(min_length=2, max_length=80)
    name_kh: str | None = Field(default=None, max_length=120)
    slug: str | None = Field(default=None, max_length=80)
    parent_id: str | None = None
    sort: int = 0


class CategoryUpdate(Schema):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    name_kh: str | None = Field(default=None, max_length=120)
    slug: str | None = Field(default=None, max_length=80)
    parent_id: str | None = None
    clear_parent: bool = False
    sort: int | None = None


class TagOut(Schema):
    id: str
    name: str
    slug: str
    product_count: int = 0


class TagCreate(Schema):
    name: str = Field(min_length=2, max_length=40)


class TagsIn(Schema):
    tag_ids: list[str] = Field(default_factory=list, max_length=12)


class VariantOut(Schema):
    id: str
    sku: str
    size: str
    color: str
    active: bool
    on_hand: int
    reserved: int
    available: int


class VariantIn(Schema):
    sku: str = Field(min_length=2, max_length=60, pattern=r"^[A-Za-z0-9._-]+$")
    size: str = Field(default="One size", max_length=40)
    color: str = Field(default="Natural", max_length=40)
    stock: int = Field(default=0, ge=0, le=100000)


class VariantUpdate(Schema):
    sku: str | None = Field(default=None, min_length=2, max_length=60, pattern=r"^[A-Za-z0-9._-]+$")
    size: str | None = Field(default=None, max_length=40)
    color: str | None = Field(default=None, max_length=40)
    active: bool | None = None


class ProductOut(Schema):
    id: str
    vendor_id: str
    vendor_name: str
    vendor_slug: str
    category_id: str | None
    category_name: str | None
    title: str
    description: str
    price_cents: int
    low_stock_threshold: int
    image_url: str | None
    active: bool
    archived_at: datetime | None
    tags: list[TagOut]
    variants: list[VariantOut]
    available: int
    low_stock: bool
    rating: float | None = None
    review_count: int = 0
    units_sold: int = 0
    created_at: datetime
    updated_at: datetime


class ProductCreate(Schema):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(default="", max_length=4000)
    price_cents: int = Field(gt=0, le=10_000_000, description="Price in cents")
    category_id: str | None = None
    low_stock_threshold: int = Field(default=3, ge=0, le=10000)
    tag_ids: list[str] = Field(default_factory=list, max_length=12)
    variants: list[VariantIn] = Field(default_factory=list, max_length=50)
    active: bool = True


class ProductUpdate(Schema):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    price_cents: int | None = Field(default=None, gt=0, le=10_000_000)
    category_id: str | None = None
    low_stock_threshold: int | None = Field(default=None, ge=0, le=10000)
    active: bool | None = None


class ModerateProductIn(Schema):
    active: bool
    reason: str = Field(min_length=3, max_length=255)
    category_id: str | None = None


class StockAdjustIn(Schema):
    delta: int | None = Field(default=None, ge=-100000, le=100000, description="Add or remove units")
    set_to: int | None = Field(default=None, ge=0, le=100000, description="Set the on-hand count")
    reason: str = Field(min_length=3, max_length=255)


class InventoryRow(Schema):
    variant_id: str
    product_id: str
    title: str
    sku: str
    size: str
    color: str
    image_url: str | None
    warehouse_id: str
    on_hand: int
    reserved: int
    available: int
    low_stock_threshold: int
    low: bool
    active: bool


class ImportRowError(Schema):
    row: int
    message: str


class ImportResult(Schema):
    dry_run: bool
    created_products: int
    updated_products: int
    created_variants: int
    updated_variants: int
    errors: list[ImportRowError]


# Storefront ----------------------------------------------------------------------


class ProductCard(Schema):
    id: str
    title: str
    price_cents: int
    image_url: str | None
    vendor_id: str
    vendor_name: str
    vendor_slug: str
    vendor_country: str
    category_id: str | None
    category_name: str | None
    tags: list[str]
    rating: float | None
    review_count: int
    available: int
    units_sold: int = 0


class StoreVariant(Schema):
    id: str
    sku: str
    size: str
    color: str
    available: int


class ReviewCard(Schema):
    id: str
    product_id: str
    product_title: str
    vendor_id: str
    vendor_name: str
    buyer_name: str
    rating: float | None
    body: str
    sentiment: str | None
    theme: str | None
    source: str
    verified_purchase: bool
    vendor_response: str | None
    vendor_responded_at: datetime | None
    created_at: datetime


class ProductDetail(ProductCard):
    description: str
    low_stock: bool
    variants: list[StoreVariant]
    shop: ShopCard
    category_path: list[CategoryOut]
    reviews: list[ReviewCard]
    related: list[ProductCard]


class ProductPage(Schema):
    items: list[ProductCard]
    total: int
    page: int
    page_size: int


class Promotion(Schema):
    code: str
    funded_by: str
    vendor_id: str | None
    vendor_name: str | None
    discount_type: str
    percent_off: int | None
    amount_off_cents: int | None
    min_subtotal_cents: int
    ends_at: datetime
    is_flash: bool
    note: str


class HomeOut(Schema):
    featured: list[ProductCard]
    new_arrivals: list[ProductCard]
    shops: list[ShopCard]
    categories: list[CategoryOut]
    promotions: list[Promotion]
    reviews: list[ReviewCard]
    stats: dict[str, int]


class ShopPage(Schema):
    shop: ShopDetail
    products: list[ProductCard]
    reviews: list[ReviewCard]
    promotions: list[Promotion]
