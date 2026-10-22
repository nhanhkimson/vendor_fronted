"""Gate G2: another tenant's record looks exactly like a missing one (404).

Row-level security already hides the row. When it existed for someone else,
the attempt is written to the activity log as `denied`, so support can see
probing without the caller learning that the record exists.
"""

from typing import Any

from sqlalchemy import exists, select

from app.core.db import system_scope
from app.core.deps import Ctx
from app.core.errors import NotFound
from app.services.audit import record_standalone


def not_found(ctx: Ctx, model: Any, resource_id: str, label: str, module: str, resource_type: str) -> NotFound:
    if ctx.scope in ("vendor", "customer"):
        with system_scope(ctx.db):
            hidden = ctx.db.scalar(select(exists().where(model.id == resource_id)))
        if hidden:
            from app.core.handlers import route_audit_meta

            who = "vendor" if ctx.scope == "vendor" else "customer"
            record_standalone(
                ctx.request,
                module=module,
                action=route_audit_meta(ctx.request)[1],
                resource_type=resource_type,
                resource_id=resource_id,
                outcome="denied",
                reason=f"Not visible to this {who} (tenant isolation)",
                principal=ctx.principal,
            )
    return NotFound(label, resource_id)


def owned(ctx: Ctx, model: Any, resource_id: str, label: str, module: str, resource_type: str, field: str = "vendor_id"):
    """Load a row the caller may see in its scope, or raise 404."""
    obj = ctx.db.get(model, resource_id)
    if obj is not None and ctx.scope == "vendor" and getattr(obj, field) != ctx.vendor_id:
        obj = None
    if obj is not None and ctx.scope == "customer" and getattr(obj, field) != ctx.user_id:
        obj = None
    if obj is None:
        raise not_found(ctx, model, resource_id, label, module, resource_type)
    return obj
