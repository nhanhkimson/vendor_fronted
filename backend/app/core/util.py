import re
import secrets
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def new_id(prefix: str, length: int = 8) -> str:
    return f"{prefix}-{secrets.token_hex(length // 2 + 1)[:length].upper()}"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def money(cents: int | None) -> str:
    cents = cents or 0
    sign = "-" if cents < 0 else ""
    return f"{sign}${abs(cents) / 100:,.2f}"


def to_json(value: Any) -> Any:
    """Make a value safe for a JSONB column (audit before/after snapshots)."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): to_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_json(v) for v in value]
    return str(value)


def snapshot(obj: Any, fields: list[str]) -> dict[str, Any]:
    return {f: to_json(getattr(obj, f, None)) for f in fields}
