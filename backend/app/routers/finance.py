from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.deps import Ctx, audit_meta, require
from app.domain import ledger
from app.models import Vendor
from app.schemas.common import OptionalNoteIn, ReasonIn
from app.schemas.finance import (
    CommissionLineOut,
    EarningsOut,
    LedgerEntryOut,
    PayIn,
    PayoutOut,
    RuleIn,
    RuleOut,
    RuleReviseIn,
    TrialBalanceOut,
)
from app.services import commissions, payouts

router = APIRouter(tags=["M7 Commission & Payouts"])


def _dates(date_from: date | None = None, date_to: date | None = None) -> tuple[date | None, date | None]:
    return date_from, date_to


# Rules and frozen lines --------------------------------------------------------------


@router.get("/api/commission-rules", response_model=list[RuleOut], summary="Commission rules, current and previous versions")
def list_rules(include_ended: bool = False, ctx: Ctx = Depends(require("commission:read"))):
    return commissions.list_rules(ctx.db, include_ended)


@router.post(
    "/api/commission-rules",
    response_model=RuleOut,
    status_code=201,
    summary="Add a rule for a tier, category or vendor",
    description="The platform default already exists. Change it with revise, which keeps every past order on the old rate.",
    openapi_extra=audit_meta("commission", "create_rule"),
)
def create_rule(body: RuleIn, ctx: Ctx = Depends(require("commission:manage_rule"))):
    return commissions.create_rule(ctx, body)


@router.post(
    "/api/commission-rules/{rule_id}/revise",
    response_model=RuleOut,
    summary="Change a rate: close this version and open the next one",
    description="Orders already placed keep their frozen commission line. Only new orders use the new rate.",
    openapi_extra=audit_meta("commission", "revise_rule"),
)
def revise_rule(rule_id: str, body: RuleReviseIn, ctx: Ctx = Depends(require("commission:manage_rule"))):
    return commissions.revise_rule(ctx, rule_id, body)


@router.post(
    "/api/commission-rules/{rule_id}/end",
    response_model=RuleOut,
    summary="Stop a rule applying to new orders (the platform default cannot be removed)",
    openapi_extra=audit_meta("commission", "end_rule"),
)
def end_rule(rule_id: str, body: ReasonIn, ctx: Ctx = Depends(require("commission:manage_rule"))):
    return commissions.end_rule(ctx, rule_id, body.reason)


@router.get("/api/commission-lines", response_model=list[CommissionLineOut], summary="Frozen commission, one row per order line")
def staff_lines(
    vendor_id: str | None = None,
    dates: tuple = Depends(_dates),
    ctx: Ctx = Depends(require("commission:read")),
):
    return commissions.list_lines(ctx.db, vendor_id, *dates)


@router.get("/api/seller/commission-rules", response_model=list[RuleOut], summary="Rates that can apply to my shop")
def seller_rules(ctx: Ctx = Depends(require("commission:read", "vendor"))):
    vendor = ctx.db.get(Vendor, ctx.vendor_id)
    tier = vendor.tier_id if vendor else None
    return [
        rule
        for rule in commissions.list_rules(ctx.db, include_ended=False)
        if rule["target_type"] in ("platform", "category")
        or (rule["target_type"] == "tier" and rule["target_id"] == tier)
        or (rule["target_type"] == "vendor" and rule["target_id"] == ctx.vendor_id)
    ]


@router.get("/api/seller/commission-lines", response_model=list[CommissionLineOut], summary="Frozen commission on my orders")
def seller_lines(dates: tuple = Depends(_dates), ctx: Ctx = Depends(require("commission:read", "vendor"))):
    return commissions.list_lines(ctx.db, ctx.vendor_id, *dates)


# Ledger ------------------------------------------------------------------------------


@router.get("/api/ledger", response_model=list[LedgerEntryOut], summary="Double-entry ledger")
def staff_ledger(
    vendor_id: str | None = None,
    account: str | None = Query(default=None, description="cash, vendor_payable, platform_revenue, platform_promotions"),
    dates: tuple = Depends(_dates),
    ctx: Ctx = Depends(require("commission:read")),
):
    return commissions.list_ledger(ctx.db, vendor_id, account, *dates)


@router.get("/api/ledger/trial-balance", response_model=TrialBalanceOut, summary="Debits and credits per account")
def trial_balance(ctx: Ctx = Depends(require("commission:read"))):
    rows = ledger.trial_balance(ctx.db)
    balanced = sum(r["debit_cents"] for r in rows) == sum(r["credit_cents"] for r in rows)
    return {"rows": rows, "balanced": balanced}


@router.get("/api/seller/ledger", response_model=list[LedgerEntryOut], summary="My shop's ledger entries")
def seller_ledger(dates: tuple = Depends(_dates), ctx: Ctx = Depends(require("commission:read", "vendor"))):
    return commissions.list_ledger(ctx.db, ctx.vendor_id, None, *dates)


# Earnings and payouts ----------------------------------------------------------------


@router.get("/api/payouts", response_model=list[PayoutOut], summary="All payouts")
def staff_payouts(
    status: str | None = Query(default=None, description="eligible, requested, pending_second_approval, approved, paid, held_for_dispute"),
    vendor_id: str | None = None,
    ctx: Ctx = Depends(require("payout:read")),
):
    return payouts.list_payouts(ctx, status, vendor_id)


@router.get("/api/payouts/{payout_id}", response_model=PayoutOut, summary="One payout, with signatures and history")
def staff_payout(payout_id: str, ctx: Ctx = Depends(require("payout:read"))):
    return payouts.get_payout(ctx, payout_id)


@router.post(
    "/api/payouts/{payout_id}/approve",
    response_model=PayoutOut,
    summary="Sign a payout (two different people, neither of them the requester)",
    openapi_extra=audit_meta("commission", "approve_payout"),
)
def approve_payout(payout_id: str, body: OptionalNoteIn, ctx: Ctx = Depends(require("payout:approve"))):
    return payouts.approve(ctx, payout_id, body.note)


@router.post(
    "/api/payouts/{payout_id}/pay",
    response_model=PayoutOut,
    summary="Mark an approved payout paid and post the bank transfer",
    openapi_extra=audit_meta("commission", "pay_payout"),
)
def pay_payout(payout_id: str, body: PayIn, ctx: Ctx = Depends(require("payout:approve"))):
    return payouts.pay(ctx, payout_id, body.reference, body.note)


@router.get("/api/vendors/{vendor_id}/earnings", response_model=EarningsOut, summary="A shop's balance, holdback and statement")
def staff_earnings(vendor_id: str, dates: tuple = Depends(_dates), ctx: Ctx = Depends(require("commission:read"))):
    return payouts.earnings(ctx, vendor_id, *dates)


@router.get("/api/seller/earnings", response_model=EarningsOut, summary="My balance, what I can request, and my statement")
def seller_earnings(dates: tuple = Depends(_dates), ctx: Ctx = Depends(require("commission:read", "vendor"))):
    return payouts.earnings(ctx, ctx.vendor_id, *dates)


@router.get("/api/seller/payouts", response_model=list[PayoutOut], summary="My payouts")
def seller_payouts(status: str | None = None, ctx: Ctx = Depends(require("payout:read", "vendor"))):
    return payouts.list_payouts(ctx, status, None)


@router.get("/api/seller/payouts/{payout_id}", response_model=PayoutOut, summary="One of my payouts")
def seller_payout(payout_id: str, ctx: Ctx = Depends(require("payout:read", "vendor"))):
    return payouts.get_payout(ctx, payout_id)


@router.post(
    "/api/seller/payouts",
    response_model=PayoutOut,
    status_code=201,
    summary="Request a payout of every delivered order past the holdback",
    openapi_extra=audit_meta("commission", "request_payout"),
)
def request_matured(ctx: Ctx = Depends(require("payout:request", "vendor"))):
    return payouts.request_matured(ctx)


@router.post(
    "/api/seller/payouts/{payout_id}/request",
    response_model=PayoutOut,
    summary="Request a payout that is ready (status eligible)",
    openapi_extra=audit_meta("commission", "request_payout"),
)
def request_payout(payout_id: str, ctx: Ctx = Depends(require("payout:request", "vendor"))):
    return payouts.request_payout(ctx, payout_id)
