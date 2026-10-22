from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from app.schemas.common import Email, Schema


class LoginIn(Schema):
    email: Email = Field(examples=["maya@bazaar.local"])
    password: str = Field(min_length=1, max_length=200, examples=["demo"])


class RegisterIn(Schema):
    name: str = Field(min_length=2, max_length=120, examples=["Sok Dara"])
    email: Email = Field(examples=["dara@example.com"])
    password: str = Field(min_length=8, max_length=200)
    city: str | None = Field(default=None, max_length=120, examples=["Phnom Penh"])


class TokenOut(Schema):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class RoleRef(Schema):
    id: str
    name: str
    kind: str


class VendorRef(Schema):
    id: str
    name: str
    slug: str
    status: str
    tier_id: str


class MeOut(Schema):
    id: str
    email: str
    name: str
    city: str | None
    blurb: str | None
    avatar_url: str | None
    source: str
    banned: bool
    ban_reason: str | None
    kind: Literal["platform", "vendor", "customer"]
    home: str
    roles: list[RoleRef]
    permissions: list[str]
    vendor: VendorRef | None


class DemoAccount(Schema):
    email: str
    password: str
    name: str
    role: str
    role_id: str
    home: str
    try_this: str
    blurb_kh: str | None


class EffectivePermission(Schema):
    key: str
    source_role_id: str
    inherited: bool


class RoleOut(Schema):
    id: str
    name: str
    description: str
    kind: str
    is_system: bool
    is_locked: bool
    parent_id: str | None
    parent_name: str | None
    user_count: int
    direct: list[str]
    effective: list[EffectivePermission]


class ModuleOut(Schema):
    id: str
    code: str
    name: str


class PermissionOut(Schema):
    key: str
    module: str
    action: str
    description: str


class MatrixOut(Schema):
    modules: list[ModuleOut]
    permissions: list[PermissionOut]
    roles: list[RoleOut]


class RoleCreate(Schema):
    name: str = Field(min_length=3, max_length=80, examples=["Finance Clerk"])
    description: str = Field(default="", max_length=255)
    kind: Literal["platform", "vendor", "customer"] = "platform"
    parent_id: str | None = None
    permissions: list[str] = Field(default_factory=list, examples=[["payout:read", "report:read"]])


class RoleUpdate(Schema):
    name: str | None = Field(default=None, min_length=3, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    parent_id: str | None = None
    clear_parent: bool = False


class RolePermissionsIn(Schema):
    permissions: list[str]


class UserRolesIn(Schema):
    role_ids: list[str] = Field(min_length=1, examples=[["support"]])


class UserOut(Schema):
    id: str
    name: str
    email: str
    vendor_id: str | None
    is_active: bool
    banned: bool
    roles: list[RoleRef]
    permissions: list[str]


class AuditOut(Schema):
    id: int
    at: datetime
    actor_id: str | None
    actor_name: str
    actor_roles: list[str]
    actor_vendor_id: str | None
    ip: str | None
    user_agent: str | None
    module: str
    action: str
    resource_type: str
    resource_id: str | None
    before: Any
    after: Any
    request_id: str | None
    outcome: str
    reason: str | None


class AuditArchiveOut(AuditOut):
    archived_at: datetime


class AuditPage(Schema):
    items: list[AuditOut]
    total: int
    page: int
    page_size: int


class AuditArchivePage(Schema):
    items: list[AuditArchiveOut]
    total: int
    page: int
    page_size: int


class ArchiveResult(Schema):
    archived: int
    detail: str


class NotificationOut(Schema):
    id: str
    kind: str
    title: str
    body: str | None
    link: str | None
    read_at: datetime | None
    created_at: datetime


class NotificationList(Schema):
    items: list[NotificationOut]
    unread: int
