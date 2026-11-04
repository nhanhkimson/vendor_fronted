"""Parameter markers that mirror FastAPI's Query / File / Form / Depends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class Depends:
    def __init__(self, dependency: Any = None):
        self.dependency = dependency


@dataclass
class Param:
    default: Any = None
    alias: str | None = None
    description: str | None = None
    ge: float | None = None
    le: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    required: bool = False
    kind: str = "query"


def Query(default: Any = None, *, alias: str | None = None, description: str | None = None, ge=None, le=None, min_length=None, max_length=None, pattern=None) -> Any:
    required = default is ...
    return Param(
        default=None if required else default,
        alias=alias,
        description=description,
        ge=ge,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        required=required,
        kind="query",
    )


def File(default: Any = ..., *, description: str | None = None) -> Any:
    required = default is ...
    return Param(default=None if required else default, description=description, required=required, kind="file")


def Form(default: Any = ..., *, description: str | None = None, min_length=None, max_length=None) -> Any:
    required = default is ...
    return Param(
        default=None if required else default,
        description=description,
        min_length=min_length,
        max_length=max_length,
        required=required,
        kind="form",
    )


@dataclass
class RouteOptions:
    response_model: Any = None
    status_code: int = 200
    summary: str | None = None
    description: str | None = None
    openapi_extra: dict[str, Any] | None = None
    tags: list[str] = field(default_factory=list)
    response_class: Any = None
