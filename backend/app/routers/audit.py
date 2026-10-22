from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.core.db import utcnow
from app.core.deps import Ctx, audit_meta, require
from app.schemas.common import Schema
from app.schemas.identity import ArchiveResult, AuditArchivePage, AuditPage
from app.services import audit_log

router = APIRouter(prefix="/api/audit-logs", tags=["M2 Activity Log"])


class ActorRef(Schema):
    id: str
    name: str


class AuditFacets(Schema):
    modules: list[str]
    actions: list[str]
    actors: list[ActorRef]
    outcomes: list[str]


def _filters(
    actor: str | None = Query(default=None, description="Actor user id, e.g. daniel"),
    role: str | None = Query(default=None, description="Role held at the time, e.g. vendor"),
    module: str | None = Query(default=None, description="roles, audit, vendor, product, ..."),
    action: str | None = Query(default=None, description="create, update, grant, login, ..."),
    outcome: Literal["success", "denied", "failed"] | None = None,
    resource: str | None = Query(default=None, description="Exact resource id, e.g. O-1001"),
    q: str | None = Query(default=None, description="Free text over actor, resource, action and diff"),
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict:
    return {
        "actor": actor,
        "role": role,
        "module": module,
        "action": action,
        "outcome": outcome,
        "resource": resource,
        "q": q,
        "date_from": date_from,
        "date_to": date_to,
    }


@router.get("", response_model=AuditPage, summary="Search the activity log")
def search(
    filters: dict = Depends(_filters),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    ctx: Ctx = Depends(require("audit:read")),
):
    return audit_log.search(ctx.db, page=page, page_size=page_size, **filters)


@router.get("/facets", response_model=AuditFacets, summary="Values for the filter dropdowns")
def facets(ctx: Ctx = Depends(require("audit:read"))):
    return audit_log.facets(ctx.db)


@router.get(
    "/export",
    summary="Export filtered rows as CSV or JSON",
    description="The export itself is written to the activity log.",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}, "application/json": {}}}},
)
def export(
    format: Literal["csv", "json"] = "csv",
    filters: dict = Depends(_filters),
    ctx: Ctx = Depends(require("audit:export")),
):
    body, media_type = audit_log.export(ctx.db, format, **filters)
    ctx.audit(
        "audit",
        "export",
        "audit_log",
        None,
        after={"format": format, "filters": {k: v for k, v in filters.items() if v}},
    )
    ctx.commit()
    stamp = utcnow().strftime("%Y%m%d-%H%M")
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="bazaar-audit-{stamp}.{format}"'},
    )


@router.get("/archive", response_model=AuditArchivePage, summary="Search archived rows")
def search_archive(
    filters: dict = Depends(_filters),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    ctx: Ctx = Depends(require("audit:read")),
):
    return audit_log.search(ctx.db, archive=True, page=page, page_size=page_size, **filters)


@router.post(
    "/archive",
    response_model=ArchiveResult,
    summary="Archive and clear the hot log",
    description="Runs the archive_audit_logs() SECURITY DEFINER function: rows move to "
    "audit_logs_archive in one statement. The runtime role itself cannot delete audit rows.",
    openapi_extra=audit_meta("audit", "archive"),
)
def archive(ctx: Ctx = Depends(require("audit:archive"))):
    moved = audit_log.archive_all(ctx.db)
    ctx.audit("audit", "archive", "audit_log", None, after={"archived_rows": moved})
    ctx.commit()
    return ArchiveResult(archived=moved, detail=f"Moved {moved} rows to the archive")
