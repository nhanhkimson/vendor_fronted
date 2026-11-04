"""Route introspection for docs and coverage tests."""

from __future__ import annotations

import inspect
from typing import Any

from app.flaskapi.params import Depends
from app.routers import ROUTERS


def iter_routes():
    for router in ROUTERS:
        prefix = router.prefix
        for route in router.routes:
            yield prefix, route


def dependency_meta(endpoint) -> list[Any]:
    found = []
    sig = inspect.signature(endpoint)
    for param in sig.parameters.values():
        default = param.default
        if not isinstance(default, Depends):
            continue
        dep = default.dependency
        if dep is None:
            continue
        if getattr(dep, "permission", None) is not None:
            found.append(dep)
    return found
