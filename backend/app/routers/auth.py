from app.flaskapi import APIRouter, Depends, Response
from app.flaskapi import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import utcnow
from app.core.deps import Ctx, Principal, audit_meta, authenticated, client_ip, principal_for, public_ctx
from app.core.errors import Forbidden, TooManyRequests, Unauthorized
from app.core.ratelimit import FailureLimiter
from app.core.security import create_access_token, verify_password
from app.models.identity import Role, User
from app.models.vendor import Vendor
from app.schemas.common import Message
from app.schemas.identity import (
    DemoAccount,
    LoginIn,
    MeOut,
    RegisterIn,
    RegisterStartedOut,
    ResendOtpIn,
    TokenOut,
    VerifyEmailIn,
)
from app.services import auth_email
from app.services.audit import record_standalone

router = APIRouter(prefix="/api/auth", tags=["Auth"])
login_limiter = FailureLimiter(settings.login_rate_limit, settings.login_rate_window_seconds)


def me_out(db: Session, principal: Principal) -> MeOut:
    user = principal.user
    vendor = db.get(Vendor, user.vendor_id) if user.vendor_id else None
    has_vendor_role = any(r.kind == "vendor" for r in user.roles)
    kind = principal.kind
    home = "/admin" if kind == "platform" else "/seller" if has_vendor_role else "/"
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
        email_verified=bool(user.email_verified_at),
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
    if not user.email_verified_at:
        login_limiter.reset(ip)
        raise Forbidden(
            "Verify your email first. Enter the code we sent, or register again to get a new one.",
            code="email_unverified",
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
    response_model=RegisterStartedOut,
    status_code=201,
    summary="Start customer registration — sends an email OTP",
    openapi_extra=audit_meta("identity", "register_start"),
)
def register(body: RegisterIn, ctx: Ctx = Depends(public_ctx)) -> RegisterStartedOut:
    return auth_email.start_register(
        ctx,
        name=body.name,
        email=body.email,
        password=body.password,
        city=body.city,
    )


@router.post(
    "/verify-email",
    response_model=MeOut,
    summary="Confirm the email OTP and sign in",
    openapi_extra=audit_meta("identity", "verify_email"),
)
def verify_email(body: VerifyEmailIn, response: Response, ctx: Ctx = Depends(public_ctx)) -> MeOut:
    principal = auth_email.verify_email(ctx, email=body.email, code=body.code)
    set_session_cookie(response, principal)
    return me_out(ctx.db, principal)


@router.post(
    "/resend-otp",
    response_model=RegisterStartedOut,
    summary="Resend the registration verification code",
    openapi_extra=audit_meta("identity", "otp_resend"),
)
def resend_otp(body: ResendOtpIn, ctx: Ctx = Depends(public_ctx)) -> RegisterStartedOut:
    return auth_email.resend_otp(ctx, body.email)


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
