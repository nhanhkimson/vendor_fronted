"""CI check: every API route declares a permission, and every mutation declares an audit action."""

from app.flaskapi.introspect import dependency_meta, iter_routes

MUTATING = {"POST", "PUT", "PATCH", "DELETE"}


def test_section10_every_route_has_a_permission_and_mutating_routes_audit():
    routes = list(iter_routes())
    assert len(routes) > 100
    missing_permission = []
    missing_audit = []
    for prefix, route in routes:
        methods = set(route.methods or ()) - {"HEAD", "OPTIONS"}
        path = f"{prefix}{route.path}"
        permissions = [dep.permission for dep in dependency_meta(route.endpoint)]
        if not permissions:
            missing_permission.append(f"{sorted(methods)} {path}")
        audit = (route.openapi_extra or {}).get("x-audit") or {}
        if methods & MUTATING and not (audit.get("module") and audit.get("action")):
            missing_audit.append(f"{sorted(methods & MUTATING)} {path}")
        assert path.startswith("/api")
    assert missing_permission == [], missing_permission
    assert missing_audit == [], missing_audit
