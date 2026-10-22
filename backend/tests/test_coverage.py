"""CI check: every API route declares a permission, and every mutation declares an audit action."""

from fastapi.routing import APIRoute

from app.main import app

MUTATING = {"POST", "PUT", "PATCH", "DELETE"}


def _routes():
    found = []
    for included in app.routes:
        router = getattr(included, "original_router", None)
        if router is None:
            continue
        for route in router.routes:
            if isinstance(route, APIRoute):
                found.append(route)
    return found


def test_section10_every_route_has_a_permission_and_mutating_routes_audit():
    routes = _routes()
    assert len(routes) > 100
    missing_permission = []
    missing_audit = []
    for route in routes:
        methods = set(route.methods or ()) - {"HEAD", "OPTIONS"}
        permissions = []
        for dependency in route.dependant.dependencies:
            permission = getattr(dependency.call, "permission", None)
            if permission:
                permissions.append(permission)
        if not permissions:
            missing_permission.append(f"{sorted(methods)} {route.path}")
        audit = (route.openapi_extra or {}).get("x-audit") or {}
        if methods & MUTATING and not (audit.get("module") and audit.get("action")):
            missing_audit.append(f"{sorted(methods & MUTATING)} {route.path}")
        assert route.path.startswith("/api")
    assert missing_permission == []
    assert missing_audit == []
