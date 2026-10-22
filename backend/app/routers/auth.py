from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import utcnow
from app.core.deps import Ctx, Principal, audit_meta, authenticated, client_ip, principal_for, public_ctx
from app.core.errors import Conflict, TooManyRequests, Unauthorized
from app.core.ratelimit import FailureLimiter
from app.core.security import create_access_token, hash_password, verify_password
from app.core.util import new_id
from app.models.identity import Role, User, UserRole
from app.models.vendor import Vendor
from app.schemas.common import Message
from app.schemas.identity import DemoAccount, LoginIn, MeOut, RegisterIn, TokenOut
from app.services.audit import record_standalone

router = APIRouter(prefix="/api/auth", tags=["Auth"])
login_limiter = FailureLimiter(settings.login_rate_limit, settings.login_rate_window_seconds)


def me_out(db: Session, principal: Principal) -> MeOut:
    user = principal.user
    vendor = db.get(Vendor, user.vendor_id) if user.vendor_id else None
    has_vendor_role = any(r.kind == "vendor" for r in user.roles)
    kind = principal.kind
    home = "/admin" if kind == "platform" else "/seller" if has_vendor_role else "/account"
    return MeOut(
        id=user.id,
        email=user.email,
        name=user.name,
        city=user.city,
        blurb=user.blurb,
        avatar_url=user.avatar_url,
        source=user.source,
        banned=user.is_banned,
        ban_reason=user.ban_reason,
        kind=kind if kind in ("platform", "vendor", "customer") else "customer",
        home=home,
        roles=[{"id": r.id, "name": r.name, "kind": r.kind} for r in user.roles],
        permissions=sorted(principal.permissions),
        vendor=(
            {
                "id": vendor.id,
                "name": vendor.name,
                "slug": vendor.slug,
                "status": vendor.status,
                "tier_id": vendor.tier_id,
            }
            if vendor
            else None
        ),
    )


def _authenticate(ctx: Ctx, email: str, password: str) -> Principal:
    ip = client_ip(ctx.request)
    if login_limiter.blocked(ip):
        record_standalone(
            ctx.request,
            module="identity",
            action="login",
            resource_type="user",
            resource_id=email,
            outcome="failed",
            reason="Too many failed sign-in attempts",
            actor_name=email,
        )
        raise TooManyRequests("Too many failed sign-in attempts. Wait a few minutes and try again.")
    user = ctx.db.scalar(select(User).where(func.lower(User.email) == email.lower()))
    if user is None or not verify_password(password, user.password_hash) or not user.is_active:
        login_limiter.fail(ip)
        reason = "Account is deactivated" if user is not None and not user.is_active else "Wrong email or password"
        record_standalone(
            ctx.request,
            module="identity",
            action="login",
            resource_type="user",
            resource_id=email,
            outcome="failed",
            reason=reason,
            actor_name=email,
        )
        raise Unauthorized(
            "That email and password do not match. Every demo account uses the password demo."
            if reason == "Wrong email or password"
            else "This account has been deactivated."
        )
    login_limiter.reset(ip)
    user.last_login_at = utcnow()
    principal = principal_for(user, "cookie")
    ctx.audit("identity", "login", "user", user.id, after={"roles": principal.role_ids}, principal=principal)
    ctx.commit()
    return principal


def set_session_cookie(response: Response, principal: Principal) -> None:
    token, expires = create_access_token(
        principal.id, principal.name, principal.role_ids, principal.vendor_id
    )
    response.set_cookie(
        settings.cookie_name,
        token,
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


@router.post(
    "/login",
    response_model=MeOut,
    summary="Sign in (browser)",
    description="Checks the email and password and sets an httpOnly session cookie. "
    "Swagger users should use **Authorize** instead, which calls `/api/auth/token`.",
    openapi_extra=audit_meta("identity", "login"),
)
def login(body: LoginIn, response: Response, ctx: Ctx = Depends(public_ctx)) -> MeOut:
    principal = _authenticate(ctx, body.email, body.password)
    set_session_cookie(response, principal)
    return me_out(ctx.db, principal)


@router.post(
    "/token",
    response_model=TokenOut,
    summary="Get a bearer token (Swagger Authorize)",
    description="OAuth2 password flow. Username is the account email.",
    openapi_extra=audit_meta("identity", "login"),
)
def token(form: OAuth2PasswordRequestForm = Depends(), ctx: Ctx = Depends(public_ctx)) -> TokenOut:
    principal = _authenticate(ctx, form.username.strip().lower(), form.password)
    access_token, expires = create_access_token(
        principal.id, principal.name, principal.role_ids, principal.vendor_id
    )
    return TokenOut(access_token=access_token, expires_at=expires)


@router.post(
    "/logout",
    response_model=Message,
    summary="Sign out",
    openapi_extra=audit_meta("identity", "logout"),
)
def logout(response: Response, ctx: Ctx = Depends(authenticated())) -> Message:
    ctx.audit("identity", "logout", "user", ctx.user_id)
    ctx.commit()
    response.delete_cookie(settings.cookie_name, path="/")
    return Message(detail="Signed out")


@router.get("/me", response_model=MeOut, summary="Who am I: roles and effective permissions")
def me(ctx: Ctx = Depends(authenticated())) -> MeOut:
    return me_out(ctx.db, ctx.principal)


@router.post(
    "/register",
    response_model=MeOut,
    status_code=201,
    summary="Create a customer account",
    openapi_extra=audit_meta("identity", "register"),
)
def register(body: RegisterIn, response: Response, ctx: Ctx = Depends(public_ctx)) -> MeOut:
    db = ctx.db
    if db.scalar(select(User).where(func.lower(User.email) == body.email)):
        raise Conflict("An account with that email already exists. Sign in instead.", code="email_taken")
    user = User(
        id=new_id("U"),
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name.strip(),
        city=body.city,
        source="organic",
        blurb="Registered on the storefront",
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id="customer"))
    db.flush()
    db.refresh(user)
    principal = principal_for(user, "cookie")
    ctx.audit(
        "identity",
        "register",
        "user",
        user.id,
        after={"email": user.email, "roles": ["customer"]},
        principal=principal,
    )
    ctx.commit()
    set_session_cookie(response, principal)
    return me_out(db, principal)


@router.get(
    "/demo-accounts",
    response_model=list[DemoAccount],
    summary="Demo accounts shown under the login form",
)
def demo_accounts(ctx: Ctx = Depends(public_ctx)) -> list[DemoAccount]:
    from app.seed.data import DEMO_ACCOUNTS

    roles = {r.id: r.name for r in ctx.db.scalars(select(Role)).all()}
    return [
        DemoAccount(
            email=a["email"],
            password="demo",
            name=a["name"],
            role=roles.get(a["role"], a["role"]),
            role_id=a["role"],
            home=a["home"],
            try_this=a["try_this"],
            blurb_kh=a.get("blurb_kh"),
        )
        for a in DEMO_ACCOUNTS
    ]
