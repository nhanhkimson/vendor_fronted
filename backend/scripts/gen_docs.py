"""Write docs/generated from the models, state machines, routes, roles, and pytest."""

# Imports follow a sys.path insert so `app` resolves when this file is run as a script.
# ruff: noqa: E402

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.routing import APIRoute

from app.core.permissions import CATALOGUE, SYSTEM_ROLES
from app.domain.states import MACHINES
from app.main import app
from app.models import Base

OUT = ROOT / "docs" / "generated"
OUT.mkdir(parents=True, exist_ok=True)


def write(name: str, body: str) -> None:
    (OUT / name).write_text(body.rstrip() + "\n", encoding="utf-8")
    print(f"wrote {name}")


def erd() -> str:
    lines = [
        "# Entity diagram",
        "",
        "Generated from the SQLAlchemy models. Regenerate with `uv run python scripts/gen_docs.py`.",
        "",
        "```mermaid",
        "erDiagram",
    ]
    for table in Base.metadata.sorted_tables:
        lines.append(f"  {table.name} {{")
        for column in table.columns:
            kind = str(column.type).split("(")[0].replace(" ", "_")
            marker = " PK" if column.primary_key else ""
            lines.append(f"    {kind} {column.name}{marker}")
        lines.append("  }")
    seen = set()
    for table in Base.metadata.sorted_tables:
        for fk in table.foreign_keys:
            edge = (fk.column.table.name, table.name, fk.parent.name)
            if edge in seen:
                continue
            seen.add(edge)
            lines.append(f"  {fk.column.table.name} ||--o{{ {table.name} : {fk.parent.name}")
    lines.append("```")
    lines.append("")
    lines.append("## Tables")
    lines.append("")
    for table in Base.metadata.sorted_tables:
        cols = ", ".join(column.name for column in table.columns)
        lines.append(f"- `{table.name}`: {cols}")
    return "\n".join(lines)


def states() -> str:
    lines = [
        "# State machines",
        "",
        "Generated from `app/domain/states.py`. A transition that is not listed returns 409.",
        "",
    ]
    for machine in MACHINES:
        lines += ["```mermaid", "stateDiagram-v2"]
        for source, targets in machine.transitions.items():
            if not targets:
                lines.append(f"  {source}")
            for target, label in targets.items():
                lines.append(f"  {source} --> {target}: {label}")
        lines += ["```", "", f"Terminal: {', '.join(machine.terminal) or 'none'}.", ""]
    return "\n".join(lines)


def api_map() -> str:
    lines = [
        "# API map",
        "",
        "Every route declares a permission. Every mutating route declares the audit action written with the change.",
        "",
        "| Method | Path | Permission | Scope | Audit |",
        "| --- | --- | --- | --- | --- |",
    ]
    rows = []
    for included in app.routes:
        router = getattr(included, "original_router", None)
        if router is None:
            continue
        for route in router.routes:
            if not isinstance(route, APIRoute):
                continue
            methods = sorted(set(route.methods or ()) - {"HEAD", "OPTIONS"})
            permission = scope = ""
            for dependency in route.dependant.dependencies:
                if getattr(dependency.call, "permission", None):
                    permission = dependency.call.permission
                    scope = getattr(dependency.call, "scope", "")
            audit = (route.openapi_extra or {}).get("x-audit") or {}
            audit_label = f"{audit.get('module', '')}.{audit.get('action', '')}" if audit else ""
            for method in methods:
                rows.append((method, route.path, permission, scope, audit_label))
    for method, path, permission, scope, audit_label in sorted(rows, key=lambda row: (row[1], row[0])):
        lines.append(f"| {method} | `{path}` | `{permission}` | {scope} | {audit_label} |")
    return "\n".join(lines)


def rbac() -> str:
    grants = {role[0]: set(role[6]) for role in SYSTEM_ROLES}
    # Super Admin inherits Admin in the running app. Show the direct grants here
    # and say so; the effective set is parent plus direct.
    lines = [
        "# Permission matrix",
        "",
        "Direct grants. Super Admin's parent is Admin, so the effective set is both columns.",
        "",
        "| Permission | " + " | ".join(role[1] for role in SYSTEM_ROLES) + " |",
        "| --- | " + " | ".join("---" for _ in SYSTEM_ROLES) + " |",
    ]
    for key, _module, _action, _description in CATALOGUE:
        marks = ["yes" if key in grants[role[0]] else "" for role in SYSTEM_ROLES]
        lines.append("| `" + key + "` | " + " | ".join(marks) + " |")
    return "\n".join(lines)


def tests() -> tuple[str, int]:
    print("running pytest for the evidence file…")
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--tb=line"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
    )
    output = (completed.stdout + "\n" + completed.stderr).strip()
    mapping = """
| Evidence | Test |
| --- | --- |
| Section 10 permission matrix | `test_section10_every_route_has_a_permission_and_mutating_routes_audit` |
| Section 10 isolation | `test_g2_and_section10_vendor_isolation_is_404_and_rls` |
| Section 10 split order | `test_g3_one_payment_two_suborders_and_two_tracking_numbers` |
| Section 10 temporal commission | `test_g4_changing_the_rate_does_not_rewrite_history` |
| Section 10 audit and SQL denial | `test_section10_audit_records_role_at_the_time_and_sql_cannot_change_the_log` |
| Section 10 separation of duties | `test_section10_payout_needs_two_people_and_an_open_dispute_blocks_it` |
| Gate G1 | `test_g1_support_cannot_change_rules_and_admin_action_is_audited` |
| Gate G2 | `test_g2_and_section10_vendor_isolation_is_404_and_rls` |
| Gate G3 | `test_g3_one_payment_two_suborders_and_two_tracking_numbers` |
| Gate G4 | `test_g4_changing_the_rate_does_not_rewrite_history` |
| Gate G5 | `test_g5_seeded_demo_ledger_and_sub_orders_balance` |
| Corrected Appendix B | `test_appendix_b_customer_pays_90_and_commission_base_stays_full` |
| Platform coupon keeps the commission base | `test_platform_coupon_does_not_shrink_the_frozen_commission_base` |
| Last Super Admin and support | `test_last_super_admin_and_support_cannot_promote_themselves` |
| Permission revoke is immediate | `test_revoke_permission_takes_effect_on_the_next_request` |
| Vendor CSV is only their shop | `test_low_stock_notification_and_vendor_csv_is_only_their_shop` |
""".strip()
    body = "\n".join(
        [
            "# Test evidence",
            "",
            mapping,
            "",
            f"Pytest exit code: {completed.returncode}",
            "",
            "```",
            output,
            "```",
        ]
    )
    return body, completed.returncode


def main() -> None:
    write("erd.md", erd())
    write("states.md", states())
    write("api-map.md", api_map())
    write("rbac.md", rbac())
    evidence, code = tests()
    write("tests.md", evidence)
    if code != 0:
        sys.exit(code)


if __name__ == "__main__":
    main()
