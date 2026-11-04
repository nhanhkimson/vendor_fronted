"""Request-id header and strict audit coverage checks."""

from __future__ import annotations

import logging
import uuid
from types import SimpleNamespace

from flask import Flask, g, request

from app.core.config import settings
from app.core.middleware import AUDIT_VIOLATIONS, MUTATING

log = logging.getLogger("bazaar.audit")


def install_middleware(app: Flask) -> None:
    @app.before_request
    def _before():
        request_id = (request.headers.get("x-request-id") or uuid.uuid4().hex[:16])[:40]
        g._bazaar_state = SimpleNamespace(request_id=request_id, audited=False, failure_audited=False)
        g.request_id = request_id

    @app.after_request
    def _after(response):
        state = getattr(g, "_bazaar_state", None)
        request_id = getattr(state, "request_id", "") if state else ""
        if request_id:
            response.headers["X-Request-ID"] = request_id
        method = request.method
        path = request.path
        status = response.status_code
        audited = bool(getattr(state, "audited", False)) if state else False
        if method in MUTATING and path.startswith("/api/") and 200 <= status < 300 and not audited:
            message = f"{method} {path} returned {status} without an audit row"
            log.warning(message)
            if settings.strict_audit:
                AUDIT_VIOLATIONS.append(message)
        return response
