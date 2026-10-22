"""Explicit transition tables. Anything not listed is refused with 409.

`scripts/gen_docs.py` draws the state diagrams in docs/ from these tables.
"""

from dataclasses import dataclass

from app.core.errors import Conflict


@dataclass(frozen=True)
class Machine:
    name: str
    initial: str
    transitions: dict[str, dict[str, str]]  # from -> {to: label}

    @property
    def states(self) -> list[str]:
        seen: list[str] = []
        for source, targets in self.transitions.items():
            for state in (source, *targets):
                if state not in seen:
                    seen.append(state)
        return seen

    @property
    def terminal(self) -> list[str]:
        return [s for s in self.states if not self.transitions.get(s)]

    def allowed(self, current: str) -> list[str]:
        return list(self.transitions.get(current, {}))

    def check(self, current: str, target: str, label: str | None = None) -> None:
        if target not in self.transitions.get(current, {}):
            allowed = ", ".join(self.allowed(current)) or "none (final state)"
            raise Conflict(
                f"{label or self.name.capitalize()} cannot move from {_human(current)} to {_human(target)}. "
                f"Allowed next: {allowed}.",
                code="invalid_transition",
                details={"machine": self.name, "from": current, "to": target, "allowed": self.allowed(current)},
            )


def _human(state: str) -> str:
    return state.replace("_", " ")


VENDOR = Machine(
    "vendor",
    "draft",
    {
        "draft": {"under_review": "submit application"},
        "under_review": {"active": "verify", "rejected": "reject (reason)"},
        "rejected": {"under_review": "resubmit documents"},
        "active": {"suspended": "suspend (reason)"},
        "suspended": {"active": "reinstate (reason)"},
    },
)

SUB_ORDER = Machine(
    "sub-order",
    "pending_acceptance",
    {
        "pending_acceptance": {"accepted": "vendor accepts", "cancelled": "cancel before shipping"},
        "accepted": {"packing": "vendor packs", "cancelled": "cancel before shipping"},
        "packing": {"shipped": "ship with tracking number", "cancelled": "cancel before shipping"},
        "shipped": {"delivered": "delivered", "refunded": "dispute resolved with refund"},
        "delivered": {"refunded": "dispute resolved with refund"},
        "cancelled": {},
        "refunded": {},
    },
)

# The parent order is derived from its sub-orders (see derive_order_status).
ORDER = Machine(
    "order",
    "paid",
    {
        "paid": {
            "partially_fulfilled": "some shops shipped",
            "fulfilled": "every shop shipped",
            "partially_refunded": "a shop cancelled",
            "cancelled": "every shop cancelled",
        },
        "partially_fulfilled": {
            "fulfilled": "every shop shipped",
            "partially_refunded": "a shop cancelled or refunded",
        },
        "fulfilled": {
            "completed": "all delivered and holdback passed",
            "partially_refunded": "a shop refunded",
            "refunded": "every shop refunded",
        },
        "partially_refunded": {
            "completed": "the rest delivered and holdback passed",
            "refunded": "the rest refunded",
            "cancelled": "the rest cancelled",
        },
        "completed": {},
        "cancelled": {},
        "refunded": {},
    },
)

PAYOUT = Machine(
    "payout",
    "eligible",
    {
        "eligible": {"requested": "vendor requests", "held_for_dispute": "dispute opened"},
        "requested": {"pending_second_approval": "first approver signs", "held_for_dispute": "dispute opened"},
        "pending_second_approval": {"approved": "second, different approver signs", "held_for_dispute": "dispute opened"},
        "approved": {"paid": "bank transfer sent", "held_for_dispute": "dispute opened"},
        "held_for_dispute": {
            "eligible": "dispute closed",
            "requested": "dispute closed",
            "pending_second_approval": "dispute closed",
            "approved": "dispute closed",
        },
        "paid": {},
    },
)

REVIEW = Machine(
    "review",
    "published",
    {
        "published": {"flagged": "flag for moderation", "removed": "remove (reason)"},
        "flagged": {"published": "restore", "removed": "remove (reason)"},
        "removed": {"published": "restore"},
    },
)

DISPUTE = Machine(
    "dispute",
    "open",
    {
        "open": {"resolved_refund": "refund the buyer", "resolved_rejected": "reject with reason"},
        "resolved_refund": {},
        "resolved_rejected": {},
    },
)

MACHINES = [VENDOR, ORDER, SUB_ORDER, PAYOUT, REVIEW, DISPUTE]

CLOSED_SUB_ORDER = {"delivered", "cancelled", "refunded"}
CANCELLABLE_SUB_ORDER = {"pending_acceptance", "accepted", "packing"}


def derive_order_status(sub_statuses: list[str], holdback_passed: bool) -> str:
    """Parent status from its sub-orders.

    Research gap: `completed` had no trigger. Here it is reached when every
    sub-order is closed and the holdback period has passed.
    """
    live = [s for s in sub_statuses if s not in ("cancelled", "refunded")]
    if not live:
        return "refunded" if "refunded" in sub_statuses else "cancelled"
    if holdback_passed and all(s == "delivered" for s in live):
        return "completed"
    if len(live) < len(sub_statuses):
        return "partially_refunded"
    if all(s in ("shipped", "delivered") for s in live):
        return "fulfilled"
    if any(s in ("shipped", "delivered") for s in live):
        return "partially_fulfilled"
    return "paid"
