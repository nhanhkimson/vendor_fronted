"""JSON encoding for pydantic / datetime / decimal values."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel


def jsonable_encoder(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, BaseModel):
        return jsonable_encoder(obj.model_dump(mode="json"))
    if isinstance(obj, dict):
        return {str(k): jsonable_encoder(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [jsonable_encoder(v) for v in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (UUID, Path)):
        return str(obj)
    if hasattr(obj, "model_dump"):
        return jsonable_encoder(obj.model_dump(mode="json"))
    return str(obj)
