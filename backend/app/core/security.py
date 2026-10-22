from datetime import datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.db import utcnow

_hasher = PasswordHash.recommended()


def hash_password(raw: str) -> str:
    return _hasher.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return _hasher.verify(raw, hashed)
    except Exception:
        return False


def create_access_token(
    user_id: str, name: str, role_ids: list[str], vendor_id: str | None
) -> tuple[str, datetime]:
    now = utcnow()
    expires = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "name": name,
        "roles": role_ids,
        "vendor_id": vendor_id,
        "iat": int(now.timestamp()),
        "exp": expires,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), expires


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
