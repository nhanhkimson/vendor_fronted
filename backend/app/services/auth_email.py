"""Register with email OTP and related helpers."""

from __future__ import annotations

import json
import secrets
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import utcnow
from app.core.deps import Ctx, Principal, principal_for
from app.core.errors import Conflict, Forbidden, Unauthorized, Unprocessable
from app.core.security import hash_password, verify_password
from app.core.util import new_id
from app.models.identity import EmailChallenge, User, UserRole
from app.services.mail import send_mail


def _otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _issue_challenge(db: Session, *, email: str, purpose: str, payload: dict | None = None) -> tuple[EmailChallenge, str]:
    email = email.strip().lower()
    # Invalidate older open challenges for the same email+purpose.
    open_rows = db.scalars(
        select(EmailChallenge).where(
            func.lower(EmailChallenge.email) == email,
            EmailChallenge.purpose == purpose,
            EmailChallenge.consumed_at.is_(None),
        )
    ).all()
    now = utcnow()
    for row in open_rows:
        row.consumed_at = now

    code = _otp_code()
    challenge = EmailChallenge(
        id=new_id("OTP"),
        email=email,
        purpose=purpose,
        code_hash=hash_password(code),
        attempts=0,
        max_attempts=5,
        expires_at=now + timedelta(minutes=settings.otp_ttl_minutes),
        created_at=now,
        payload_json=json.dumps(payload) if payload else None,
    )
    db.add(challenge)
    db.flush()
    return challenge, code


def _send_otp_mail(email: str, code: str, name: str | None = None) -> None:
    greeting = f"Hi {name}," if name else "Hi,"
    text = (
        f"{greeting}\n\n"
        f"Your Bazaar verification code is {code}.\n"
        f"It expires in {settings.otp_ttl_minutes} minutes.\n\n"
        "If you did not create an account, ignore this email.\n"
    )
    html = f"""
    <div style="font-family:Georgia,serif;max-width:480px;margin:0 auto;color:#171411">
      <p style="font-size:28px;margin:0 0 8px">Bazaar</p>
      <p>{greeting}</p>
      <p>Your verification code is</p>
      <p style="font-size:36px;letter-spacing:0.2em;font-weight:700;margin:16px 0">{code}</p>
      <p style="color:#6b6258">Expires in {settings.otp_ttl_minutes} minutes.</p>
    </div>
    """
    send_mail(to=email, subject=f"Your Bazaar code is {code}", text=text, html=html)


def start_register(ctx: Ctx, *, name: str, email: str, password: str, city: str | None) -> dict:
    db = ctx.db
    email = email.strip().lower()
    existing = db.scalar(select(User).where(func.lower(User.email) == email))
    if existing and existing.email_verified_at:
        raise Conflict("An account with that email already exists. Sign in instead.", code="email_taken")

    if existing and not existing.email_verified_at:
        existing.password_hash = hash_password(password)
        existing.name = name.strip()
        if city:
            existing.city = city
        user_id = existing.id
    else:
        user = User(
            id=new_id("U"),
            email=email,
            password_hash=hash_password(password),
            name=name.strip(),
            city=city,
            source="organic",
            blurb="Registered on the storefront",
            email_verified_at=None,
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role_id="customer"))
        user_id = user.id

    challenge, code = _issue_challenge(
        db,
        email=email,
        purpose="register",
        payload={"user_id": user_id, "name": name.strip()},
    )
    _send_otp_mail(email, code, name.strip())
    ctx.audit(
        "identity",
        "register_start",
        "user",
        user_id,
        after={"email": email, "challenge_id": challenge.id},
    )
    ctx.commit()
    out = {
        "email": email,
        "detail": "We sent a 6-digit code to your email. Enter it to finish creating your account.",
        "expires_in_seconds": settings.otp_ttl_minutes * 60,
        "challenge_id": challenge.id,
    }
    if settings.expose_otp_in_api:
        out["dev_code"] = code
    return out


def resend_otp(ctx: Ctx, email: str) -> dict:
    db = ctx.db
    email = email.strip().lower()
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if user is None:
        raise Unprocessable("No pending account for that email.", code="unknown_email")
    if user.email_verified_at:
        raise Conflict("That email is already verified. Sign in.", code="already_verified")
    challenge, code = _issue_challenge(db, email=email, purpose="register", payload={"user_id": user.id, "name": user.name})
    _send_otp_mail(email, code, user.name)
    ctx.audit("identity", "otp_resend", "user", user.id, after={"challenge_id": challenge.id})
    ctx.commit()
    out = {
        "email": email,
        "detail": "A new code was sent.",
        "expires_in_seconds": settings.otp_ttl_minutes * 60,
        "challenge_id": challenge.id,
    }
    if settings.expose_otp_in_api:
        out["dev_code"] = code
    return out


def verify_email(ctx: Ctx, *, email: str, code: str) -> Principal:
    db = ctx.db
    email = email.strip().lower()
    code = code.strip()
    if len(code) < 4:
        raise Unprocessable("Enter the 6-digit code from your email.", code="bad_code")

    challenge = db.scalar(
        select(EmailChallenge)
        .where(
            func.lower(EmailChallenge.email) == email,
            EmailChallenge.purpose == "register",
            EmailChallenge.consumed_at.is_(None),
        )
        .order_by(EmailChallenge.created_at.desc())
    )
    if challenge is None:
        raise Unprocessable("No open verification for that email. Register again.", code="no_challenge")
    if challenge.expires_at <= utcnow():
        challenge.consumed_at = utcnow()
        ctx.commit()
        raise Unprocessable("That code expired. Request a new one.", code="otp_expired")
    if challenge.attempts >= challenge.max_attempts:
        raise Forbidden("Too many attempts. Request a new code.", code="otp_locked")

    challenge.attempts += 1
    if not verify_password(code, challenge.code_hash):
        ctx.commit()
        raise Unauthorized("That code is not correct.", code="otp_invalid")

    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if user is None:
        raise Unprocessable("Account missing. Register again.", code="unknown_email")

    challenge.consumed_at = utcnow()
    user.email_verified_at = utcnow()
    user.last_login_at = utcnow()
    principal = principal_for(user, "cookie")
    ctx.audit(
        "identity",
        "verify_email",
        "user",
        user.id,
        after={"email": user.email, "roles": principal.role_ids},
        principal=principal,
    )
    ctx.commit()
    return principal


def require_verified(user: User) -> None:
    if not user.email_verified_at:
        raise Forbidden(
            "Verify your email before continuing. Check your inbox for the code, or register again to resend it.",
            code="email_unverified",
        )
