"""Error envelopes and audit rows for denied or failed requests (Flask)."""

from __future__ import annotations

import logging
from typing import Any

from flask import Response, jsonify

from app.core.errors import ApiError
from app.core.middleware import MUTATING
from app.core.permissions import MODULES
from app.flaskapi.encoding import jsonable_encoder
from app.flaskapi.request import Request
from app.flaskapi.routing import ValidationFailed

log = logging.getLogger("bazaar")
TAG_TO_MODULE = {m.tag: m.id for m in MODULES} | {"Notifications & Messages": "order", "Auth": "identity"}


def route_audit_meta(request: Request) -> tuple[str, str]:
    route = request.scope.get("route")
    extra = getattr(route, "openapi_extra", None) or {}
    meta = extra.get("x-audit") if isinstance(extra, dict) else None
    if meta:
        return meta["module"], meta["action"]
    tags = getattr(route, "tags", None) or []
    module = next((TAG_TO_MODULE[t] for t in tags if t in TAG_TO_MODULE), "system")
    return module, "read" if request.method not in MUTATING else request.method.lower()


def _principal(request: Request):
    return getattr(request.state, "principal", None)


def _token_actor_name(request: Request) -> str:
    from app.core.config import settings
    from app.core.security import decode_access_token

    token = request.cookies.get(settings.cookie_name)
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        token = header[7:]
    payload = decode_access_token(token) if token else None
    return payload.get("name", "Anonymous") if payload else "Anonymous"


def _record_failure(request: Request, status: int, message: str) -> None:
    if getattr(request.state, "failure_audited", False):
        return
    path = getattr(request._req, "path", "")
    if not str(path).startswith("/api/"):
        return
    if status == 403:
        outcome = "denied"
    elif request.method in MUTATING and status not in (401,):
        outcome = "failed"
    else:
        return
    from app.services.audit import record_standalone

    module, action = route_audit_meta(request)
    path_params = request.path_params or {}
    resource_id = next(iter(path_params.values()), None)
    principal = _principal(request)
    try:
        record_standalone(
            request,
            module=module,
            action=action,
            resource_type=module,
            resource_id=resource_id,
            outcome=outcome,
            reason=f"{status}: {message}",
            principal=principal,
            actor_name=_token_actor_name(request) if principal is None else "Anonymous",
        )
    except Exception:
        log.exception("could not write failure audit row")


def _body(code: str, message: str, details: Any = None, fields: dict[str, str] | None = None):
    body: dict[str, Any] = {"detail": message, "code": code}
    if details is not None:
        body["details"] = jsonable_encoder(details)
    if fields:
        body["fields"] = fields
    return body


def handle_exception(request: Request, exc: Exception) -> Response:
    if isinstance(exc, ValidationFailed):
        _record_failure(request, 422, exc.message)
        return jsonify(_body("validation_error", "Some fields are not valid", fields=exc.fields)), 422
    if isinstance(exc, ApiError):
        _record_failure(request, exc.status_code, exc.message)
        return jsonify(_body(exc.code, exc.message, exc.details)), exc.status_code

    log.exception("unhandled error on %s %s", request.method, getattr(request._req, "path", ""))
    _record_failure(request, 500, f"{type(exc).__name__}")
    request_id = getattr(request.state, "request_id", "")
    return jsonify(_body("server_error", f"Unexpected server error (request {request_id})")), 500
