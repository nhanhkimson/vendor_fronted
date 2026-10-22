from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.core.db import utcnow
from app.core.deps import Ctx, audit_meta, require
from app.schemas.reports import OverviewOut, SummaryOut
from app.services import reports

router = APIRouter(tags=["M10 Reports & Analytics"])

ReportName = Literal["sales", "revenue", "products", "sources", "commission"]


def _dates(date_from: date | None = None, date_to: date | None = Query(default=None, description="Inclusive end date")) -> tuple[date | None, date | None]:
    return date_from, date_to


def _csv(ctx: Ctx, report: str, vendor_id: str | None, dates: tuple[date | None, date | None]) -> Response:
    body = reports.export_csv(ctx.db, report, vendor_id, *dates)
    ctx.audit("report", "export", "report", report, after={"vendor_id": vendor_id, "from": dates[0], "to": dates[1]})
    ctx.commit()
    stamp = utcnow().strftime("%Y%m%d")
    return Response(content=body, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="bazaar-{report}-{stamp}.csv"'})


@router.get("/api/reports/overview", response_model=OverviewOut, summary="Sales, revenue, top products, sources and commission")
def overview(
    vendor_id: str | None = None,
    dates: tuple = Depends(_dates),
    ctx: Ctx = Depends(require("report:read")),
):
    return reports.overview(ctx.db, vendor_id, *dates)


@router.get(
    "/api/reports/{report}/export",
    summary="Download one report as CSV",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
    openapi_extra=audit_meta("report", "export"),
)
def export_report(
    report: ReportName,
    vendor_id: str | None = None,
    dates: tuple = Depends(_dates),
    ctx: Ctx = Depends(require("report:export")),
):
    return _csv(ctx, report, vendor_id, dates)


@router.get("/api/seller/reports/overview", response_model=OverviewOut, summary="My shop's reports")
def seller_overview(dates: tuple = Depends(_dates), ctx: Ctx = Depends(require("report:read", "vendor"))):
    return reports.overview(ctx.db, ctx.vendor_id, *dates)


@router.get(
    "/api/seller/reports/{report}/export",
    summary="Download one of my shop's reports as CSV",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
    openapi_extra=audit_meta("report", "export"),
)
def seller_export(report: ReportName, dates: tuple = Depends(_dates), ctx: Ctx = Depends(require("report:export", "vendor"))):
    return _csv(ctx, report, ctx.vendor_id, dates)


@router.get("/api/account/summary", response_model=SummaryOut, summary="Counts for the customer menu")
def account_summary(ctx: Ctx = Depends(require("order:read", "customer"))):
    return reports.summary(ctx)


@router.get("/api/seller/summary", response_model=SummaryOut, summary="Counts for the seller menu")
def seller_summary(ctx: Ctx = Depends(require("report:read", "vendor"))):
    return reports.summary(ctx)


@router.get("/api/admin/summary", response_model=SummaryOut, summary="Counts for the admin menu")
def admin_summary(ctx: Ctx = Depends(require("report:read"))):
    return reports.summary(ctx)
