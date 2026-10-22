from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, utcnow


class CommissionTier(Base):
    __tablename__ = "commission_tiers"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    name_kh: Mapped[str | None] = mapped_column(String(120))
    min_sales: Mapped[int] = mapped_column(BigInteger, default=0)
    max_sales: Mapped[int | None] = mapped_column(BigInteger)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(120))


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    country: Mapped[str] = mapped_column(String(2), default="US")
    city: Mapped[str] = mapped_column(String(120), default="")
    # draft, under_review, active, suspended, rejected (see app.domain.states.VENDOR)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    status_reason: Mapped[str | None] = mapped_column(String(255))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tier_id: Mapped[str] = mapped_column(ForeignKey("commission_tiers.id"), default="starter")
    warehouse_id: Mapped[str | None] = mapped_column(ForeignKey("warehouses.id"))
    headline: Mapped[str] = mapped_column(String(160), default="")
    about: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(String(255))
    hue: Mapped[int] = mapped_column(Integer, default=24)
    # Flat fee per sub-order. Passed through to the vendor, never commissionable.
    shipping_fee_cents: Mapped[int] = mapped_column(Integer, default=500)
    processing_days: Mapped[int] = mapped_column(Integer, default=3)
    # Public-sample metrics carried over from the research dataset.
    lifetime_sales: Mapped[int] = mapped_column(BigInteger, default=0)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2))
    rating_flag: Mapped[str] = mapped_column(String(20), default="observed")
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    since: Mapped[date | None] = mapped_column(Date)
    response_hours: Mapped[int] = mapped_column(Integer, default=24)
    response_flag: Mapped[str] = mapped_column(String(20), default="estimated")
    catalog_size: Mapped[str] = mapped_column(String(20), default="Small")
    is_outlier: Mapped[bool] = mapped_column(Boolean, default=False)
    payout_account: Mapped[str | None] = mapped_column(String(60))
    internal_notes: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    tier: Mapped[CommissionTier] = relationship(lazy="joined")
    warehouse: Mapped[Warehouse | None] = relationship(lazy="joined")
    documents: Mapped[list["VendorDocument"]] = relationship(
        back_populates="vendor", lazy="selectin", order_by="VendorDocument.id"
    )


class VendorDocument(Base):
    __tablename__ = "vendor_documents"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    # government_id, address_proof, payout_account
    kind: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(120))
    # missing, submitted, verified, rejected
    status: Mapped[str] = mapped_column(String(20), default="missing")
    file_path: Mapped[str | None] = mapped_column(String(255))
    original_filename: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(80))
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[str | None] = mapped_column(String(40))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    vendor: Mapped[Vendor] = relationship(back_populates="documents")


class VendorStatusEvent(Base):
    __tablename__ = "vendor_status_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str | None] = mapped_column(String(40))
    reason: Mapped[str | None] = mapped_column(String(255))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
