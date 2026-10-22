from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.core.deps import Ctx, audit_meta, public_ctx, require
from app.schemas.common import Message, Schema
from app.services.audit import record_standalone

router = APIRouter(prefix="/api", tags=["System"])


class Health(Schema):
    status: str
    database: str
    version: str


@router.get("/health", response_model=Health, summary="Liveness and database check")
def health(ctx: Ctx = Depends(public_ctx)):
    ctx.db.execute(text("SELECT 1"))
    return Health(status="ok", database="ok", version="1.0.0")


@router.post(
    "/system/reset",
    response_model=Message,
    summary="Reset all data to the demo seed",
    description="Truncates every table and loads the seed again using the owner role. "
    "Super Admin only (`system:reset`). The reset itself is the first row of the new activity log.",
    openapi_extra=audit_meta("system", "reset"),
)
def reset(ctx: Ctx = Depends(require("system:reset"))):
    from app.seed.run import reset_database

    principal = ctx.principal
    ctx.db.close()
    counts = reset_database()
    record_standalone(
        ctx.request,
        module="system",
        action="reset",
        resource_type="database",
        outcome="success",
        principal=principal,
        after=counts,
    )
    ctx.request.state.audited = True
    return Message(detail="Demo data restored to the seed")
