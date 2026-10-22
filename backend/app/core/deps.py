"""Request context and the permission dependency used by every route.

`require("product:update", scope="vendor")` returns a FastAPI dependency that
resolves the caller, checks the permission (403 if missing), checks tenancy,
sets the row-level security scope for the request and returns a `Ctx`. The
permission and scope are attached to the dependency so tests and the docs
generator can list which permission guards each route.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db, set_scope
from app.core.errors import Forbidden, Unauthorized
from app.core.permissions import BANNED_STRIPPED
from app.core.security import decode_access_token
from app.models.identity import Role, User

PUBLIC = "public"
AUTHENTICATED = "authenticated"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CLIENT_HEADER = "x-bazaar-client"

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/token",
    auto_error=False,
    scheme_name="Bazaar login",
    description="Use a demo account email as the username and `demo` as the password.",
)


def effective_permissions(roles: list[Role]) -> dict[str, str]:
    """Map each effective permission key to the role it comes from (direct or inherited)."""
    result: dict[str, str] = {}
    for role in roles:
        seen: set[str] = set()
        current: Role | None = role
        while current is not None and current.id not in seen:
            seen.add(current.id)
            for perm in current.permissions:
                result.setdefault(perm.key, current.id)
            current = current.parent
    return result


ROLE_KIND_ORDER = {"platform": 0, "vendor": 1, "customer": 2}


@dataclass
class Principal:
    user: User
    permissions: frozenset[str]
    via: str

    @property
    def id(self) -> str:
        return self.user.id

    @property
    def name(self) -> str:
        return self.user.name

    @property
    def role_ids(self) -> list[str]:
        return [r.id for r in self.user.roles]

    @property
    def vendor_id(self) -> str | None:
        return self.user.vendor_id

    @property
    def kind(self) -> str:
        kinds = sorted((r.kind for r in self.user.roles), key=lambda k: ROLE_KIND_ORDER.get(k, 9))
        return kinds[0] if kinds else "customer"

    def can(self, key: str) -> bool:
        return key in self.permissions


def principal_for(user: User, via: str) -> Principal:
    perms = set(effective_permissions(user.roles))
    if user.is_banned:
        perms -= BANNED_STRIPPED
    return Principal(user=user, permissions=frozenset(perms), via=via)


def _token_from(request: Request, bearer: str | None) -> tuple[str | None, str]:
    if bearer:
        return bearer, "bearer"
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip(), "bearer"
    cookie = request.cookies.get(settings.cookie_name)
    if cookie:
        return cookie, "cookie"
    return None, "none"


def resolve_principal(request: Request, db: Session, bearer: str | None = None) -> Principal | None:
    token, via = _token_from(request, bearer)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    user = db.get(User, payload["sub"])
    if user is None or not user.is_active:
        return None
    principal = principal_for(user, via)
    request.state.principal = principal
    return principal


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return request.client.host if request.client else "unknown"


@dataclass
class Ctx:
    db: Session
    request: Request
    principal: Principal | None
    scope: str
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def request_id(self) -> str:
        return getattr(self.request.state, "request_id", "")

    @property
    def ip(self) -> str:
        return client_ip(self.request)

    @property
    def user_agent(self) -> str:
        return (self.request.headers.get("user-agent") or "")[:255]

    @property
    def user(self) -> User:
        if self.principal is None:
            raise Unauthorized("Sign in required")
        return self.principal.user

    @property
    def user_id(self) -> str | None:
        return self.principal.id if self.principal else None

    @property
    def vendor_id(self) -> str:
        vendor_id = self.principal.vendor_id if self.principal else None
        if not vendor_id:
            raise Forbidden("This action needs a vendor account")
        return vendor_id

    def can(self, key: str) -> bool:
        return bool(self.principal and self.principal.can(key))

    def audit(self, module: str, action: str, resource_type: str, resource_id: Any = None, **kwargs):
        from app.services import audit

        return audit.record(self, module, action, resource_type, resource_id, **kwargs)

    def commit(self) -> None:
        self.db.commit()


def _csrf_check(request: Request, principal: Principal | None) -> None:
    if (
        principal is not None
        and principal.via == "cookie"
        and request.method not in SAFE_METHODS
        and not request.headers.get(CLIENT_HEADER)
    ):
        raise Forbidden(
            "Cookie sessions must send the X-Bazaar-Client header. In Swagger, use Authorize instead.",
            code="csrf_failed",
        )


def require(permission: str, scope: str = "platform") -> Callable[..., Ctx]:
    """Dependency factory: authenticated caller with `permission`, running in `scope`."""

    def dependency(
        request: Request,
        db: Session = Depends(get_db),
        bearer: str | None = Depends(oauth2_scheme),
    ) -> Ctx:
        principal = resolve_principal(request, db, bearer)
        if principal is None:
            raise Unauthorized("Sign in required")
        _csrf_check(request, principal)
        if permission != AUTHENTICATED and not principal.can(permission):
            raise Forbidden(
                f"Your role does not include the permission {permission}",
                code="permission_denied",
                details={"permission": permission},
            )
        if scope == "platform" and principal.vendor_id:
            raise Forbidden("Vendor accounts cannot use platform endpoints", code="tenancy")
        if scope == "vendor" and not principal.vendor_id:
            raise Forbidden("This endpoint needs a vendor account", code="tenancy")
        set_scope(
            db,
            scope,
            user_id=principal.id,
            vendor_id=principal.vendor_id if scope == "vendor" else None,
        )
        return Ctx(db=db, request=request, principal=principal, scope=scope)

    dependency.permission = permission  # type: ignore[attr-defined]
    dependency.scope = scope  # type: ignore[attr-defined]
    dependency.__name__ = f"require_{permission.replace(':', '_')}_{scope}"
    return dependency


def public_ctx(request: Request, db: Session = Depends(get_db)) -> Ctx:
    """Anonymous-friendly context for the storefront and the login endpoints."""
    principal = resolve_principal(request, db)
    _csrf_check(request, principal)
    set_scope(db, "public", user_id=principal.id if principal else None)
    return Ctx(db=db, request=request, principal=principal, scope="public")


public_ctx.permission = PUBLIC  # type: ignore[attr-defined]
public_ctx.scope = "public"  # type: ignore[attr-defined]


def authenticated(scope: str = "customer") -> Callable[..., Ctx]:
    return require(AUTHENTICATED, scope)


def audit_meta(module: str, action: str) -> dict[str, Any]:
    """openapi_extra for mutating routes; read by the audit coverage check and failure logging."""
    return {"x-audit": {"module": module, "action": action}}
