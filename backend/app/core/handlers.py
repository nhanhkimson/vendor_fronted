"""Error envelopes and audit rows for denied or failed requests."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import ApiError
from app.core.middleware import MUTATING
from app.core.permissions import MODULES

log = logging.getLogger("bazaar")
TAG_TO_MODULE = {m.tag: m.id for m in MODULES}


def _route_audit_meta(request: Request) -> tuple[str, str]:
    route = request.scope.get("route")
    extra = getattr(route, "openapi_extra", None) or {}
    meta = extra.get("x-audit")
    if meta:
        return meta["module"], meta["action"]
    tags = getattr(route, "tags", None) or []
    module = next((TAG_TO_MODULE[t] for t in tags if t in TAG_TO_MODULE), "system")
    return module, "read" if request.method not in MUTATING else request.method.lower()


def _principal(request: Request):
    principal = getattr(request.state, "principal", None)
    if principal is not None:
        return principal
    return None


def _token_actor_name(request: Request) -> str:
    from app.core.config import settings
    from app.core.security import decode_access_token

    token = request.cookies.get(settings.cookie_name)
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        token = header[7:]
    payload = decode_access_token(token) if token else None
    return payload.get("name", "Anonymous") if payload else "Anonymous"


async def _record_failure(request: Request, status: int, message: str) -> None:
    if getattr(request.state, "failure_audited", False):
        return
    if not request.url.path.startswith("/api/"):
        return
    if status == 403:
        outcome = "denied"
    elif request.method in MUTATING and status not in (401,):
        outcome = "failed"
    else:
        return
    from app.services.audit import record_standalone

    module, action = _route_audit_meta(request)
    path_params = request.path_params or {}
    resource_id = next(iter(path_params.values()), None)
    principal = _principal(request)
    try:
        await run_in_threadpool(
            lambda: record_standalone(
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
        )
    except Exception:  # an audit failure must never hide the original error
        log.exception("could not write failure audit row")


def _body(code: str, message: str, details: Any = None, fields: dict[str, str] | None = None):
    body: dict[str, Any] = {"detail": message, "code": code}
    if details is not None:
        body["details"] = jsonable_encoder(details)
    if fields:
        body["fields"] = fields
    return body


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError):
        await _record_failure(request, exc.status_code, exc.message)
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        fields: dict[str, str] = {}
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", []) if p not in ("body", "query", "path"))
            fields[loc or "request"] = err.get("msg", "Invalid value")
        summary = "; ".join(f"{k}: {v}" for k, v in list(fields.items())[:3])
        await _record_failure(request, 422, f"Validation failed ({summary})")
        return JSONResponse(
            status_code=422,
            content=_body("validation_error", "Some fields are not valid", fields=fields),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        await _record_failure(request, exc.status_code, message)
        return JSONResponse(
            status_code=exc.status_code,
            content=_body("http_error", message),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception):
        log.exception("unhandled error on %s %s", request.method, request.url.path)
        await _record_failure(request, 500, f"{type(exc).__name__}")
        request_id = getattr(request.state, "request_id", "")
        return JSONResponse(
            status_code=500,
            content=_body("server_error", f"Unexpected server error (request {request_id})"),
        )
