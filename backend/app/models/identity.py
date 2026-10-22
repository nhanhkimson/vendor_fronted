from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, utcnow


class Permission(Base):
    """One row per permission key, e.g. `product:update` (Appendix A catalogue)."""

    __tablename__ = "permissions"

    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    module: Mapped[str] = mapped_column(String(20), index=True)
    action: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(255), default="")
    sort: Mapped[int] = mapped_column(default=0)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_key: Mapped[str] = mapped_column(
        ForeignKey("permissions.key", ondelete="CASCADE"), primary_key=True
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    granted_by: Mapped[str | None] = mapped_column(String(40))


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    # Which part of the product the role is for: platform staff, vendor tenant or customer.
    kind: Mapped[str] = mapped_column(String(20), default="platform")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    # Locked roles cannot have their matrix edited (protects Super Admin from lock-out).
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    parent: Mapped["Role | None"] = relationship(remote_side=[id], lazy="joined", join_depth=3)
    permissions: Mapped[list[Permission]] = relationship(
        secondary="role_permissions", lazy="selectin", order_by=Permission.sort
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    assigned_by: Mapped[str | None] = mapped_column(String(40))


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))
    blurb: Mapped[str | None] = mapped_column(String(255))
    blurb_kh: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(120))
    # Acquisition channel used by M10 reports: organic, coupon, social, referral.
    source: Mapped[str] = mapped_column(String(30), default="organic")
    avatar_url: Mapped[str | None] = mapped_column(String(255))
    # Tenancy: set for vendor staff (and for applicants while their shop is reviewed).
    vendor_id: Mapped[str | None] = mapped_column(ForeignKey("vendors.id"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    banned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ban_reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    roles: Mapped[list[Role]] = relationship(
        secondary="user_roles", lazy="selectin", order_by=Role.name
    )

    @property
    def is_banned(self) -> bool:
        return self.banned_at is not None
