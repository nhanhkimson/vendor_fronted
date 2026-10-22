import logging
import uuid

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings

MUTATING = {"POST", "PUT", "PATCH", "DELETE"}
log = logging.getLogger("bazaar.audit")

# Filled when strict_audit is on: successful mutating requests that wrote no audit row.
AUDIT_VIOLATIONS: list[str] = []


class RequestContextMiddleware:
    """Adds a request id (echoed as X-Request-ID) and enforces audit coverage in strict mode."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        request_id = (headers.get("x-request-id") or uuid.uuid4().hex[:16])[:40]
        state = scope.setdefault("state", {})
        state["request_id"] = request_id
        status = {"code": 500}

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
                message.setdefault("headers", [])
                message["headers"].append((b"x-request-id", request_id.encode()))
            await send(message)

        await self.app(scope, receive, send_with_id)

        method = scope.get("method", "GET")
        path = scope.get("path", "")
        if (
            method in MUTATING
            and path.startswith("/api/")
            and 200 <= status["code"] < 300
            and not state.get("audited")
        ):
            message = f"{method} {path} returned {status['code']} without an audit row"
            log.warning(message)
            if settings.strict_audit:
                AUDIT_VIOLATIONS.append(message)
