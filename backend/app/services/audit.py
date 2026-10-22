"""M2 Activity Log writer.

Successful mutations write their audit row in the same transaction as the
change (`record`). Denied and failed requests are written by the error
handlers in a separate transaction (`record_standalone`), because the request
transaction is rolled back.
"""

from typing import TYPE_CHECKING, Any

from fastapi import Request

from app.core.db import SessionLocal, utcnow
from app.core.util import to_json
from app.models.system import AuditLog

if TYPE_CHECKING:
    from app.core.deps import Ctx, Principal


def _actor(principal: "Principal | None", fallback_name: str = "Anonymous") -> dict[str, Any]:
    if principal is None:
        return {
            "actor_id": None,
            "actor_name": fallback_name,
            "actor_roles": [],
            "actor_vendor_id": None,
        }
    return {
        "actor_id": principal.id,
        "actor_name": principal.name,
        "actor_roles": principal.role_ids,
        "actor_vendor_id": principal.vendor_id,
    }


def record(
    ctx: "Ctx",
    module: str,
    action: str,
    resource_type: str,
    resource_id: Any = None,
    *,
    before: Any = None,
    after: Any = None,
    outcome: str = "success",
    reason: str | None = None,
    principal: "Principal | None" = None,
) -> AuditLog:
    entry = AuditLog(
        at=utcnow(),
        **_actor(principal or ctx.principal),
        ip=ctx.ip,
        user_agent=ctx.user_agent,
        module=module,
        action=action,
        resource_type=resource_type,
        resource_id=None if resource_id is None else str(resource_id),
        before=to_json(before),
        after=to_json(after),
        request_id=ctx.request_id,
        outcome=outcome,
        reason=reason,
    )
    ctx.db.add(entry)
    ctx.request.state.audited = True
    return entry


def record_standalone(
    request: Request,
    *,
    module: str,
    action: str,
    resource_type: str,
    resource_id: Any = None,
    outcome: str,
    reason: str | None = None,
    principal: "Principal | None" = None,
    actor_name: str = "Anonymous",
    before: Any = None,
    after: Any = None,
) -> None:
    from app.core.deps import client_ip

    with SessionLocal() as db:
        db.add(
            AuditLog(
                at=utcnow(),
                **_actor(principal, actor_name),
                ip=client_ip(request),
                user_agent=(request.headers.get("user-agent") or "")[:255],
                module=module,
                action=action,
                resource_type=resource_type,
                resource_id=None if resource_id is None else str(resource_id)[:80],
                before=to_json(before),
                after=to_json(after),
                request_id=getattr(request.state, "request_id", None),
                outcome=outcome,
                reason=(reason or "")[:255] or None,
            )
        )
        db.commit()
    request.state.failure_audited = True
