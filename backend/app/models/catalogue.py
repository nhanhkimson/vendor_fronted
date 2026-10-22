from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, utcnow


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    name_kh: Mapped[str | None] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"))
    sort: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True)


class ProductTag(Base):
    __tablename__ = "product_tags"

    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    price_cents: Mapped[int] = mapped_column(Integer)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=3)
    image_url: Mapped[str | None] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    variants: Mapped[list["Variant"]] = relationship(
        back_populates="product", lazy="selectin", order_by="Variant.id"
    )
    tags: Mapped[list[Tag]] = relationship(secondary="product_tags", lazy="selectin", order_by=Tag.name)

    __table_args__ = (CheckConstraint("price_cents > 0", name="price_positive"),)


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    sku: Mapped[str] = mapped_column(String(60))
    size: Mapped[str] = mapped_column(String(40), default="One size")
    color: Mapped[str] = mapped_column(String(40), default="Natural")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    product: Mapped[Product] = relationship(back_populates="variants")
    stock_items: Mapped[list["StockItem"]] = relationship(
        back_populates="variant", lazy="selectin", order_by="StockItem.id"
    )

    __table_args__ = (UniqueConstraint("vendor_id", "sku", name="uq_variant_vendor_sku"),)

    @property
    def available(self) -> int:
        return sum(s.on_hand - s.reserved for s in self.stock_items)

    @property
    def on_hand(self) -> int:
        return sum(s.on_hand for s in self.stock_items)

    @property
    def reserved(self) -> int:
        return sum(s.reserved for s in self.stock_items)


class StockItem(Base):
    """Stock of one variant in one warehouse. `reserved` holds units in open checkouts."""

    __tablename__ = "stock_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    variant_id: Mapped[str] = mapped_column(ForeignKey("variants.id", ondelete="CASCADE"), index=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    warehouse_id: Mapped[str] = mapped_column(ForeignKey("warehouses.id"))
    on_hand: Mapped[int] = mapped_column(Integer, default=0)
    reserved: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    variant: Mapped[Variant] = relationship(back_populates="stock_items")

    __table_args__ = (
        UniqueConstraint("variant_id", "warehouse_id", name="uq_stock_variant_warehouse"),
        CheckConstraint("on_hand >= 0", name="on_hand_non_negative"),
        CheckConstraint("reserved >= 0 AND reserved <= on_hand", name="reserved_within_on_hand"),
    )


class StockReservation(Base):
    __tablename__ = "stock_reservations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    payment_intent_id: Mapped[str] = mapped_column(ForeignKey("payment_intents.id"), index=True)
    stock_item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id"))
    variant_id: Mapped[str] = mapped_column(String(40))
    qty: Mapped[int] = mapped_column(Integer)
    # active, committed, released
    status: Mapped[str] = mapped_column(String(20), default="active")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
