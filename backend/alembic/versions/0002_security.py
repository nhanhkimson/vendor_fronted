"""security: grants, append-only tables, row-level security, audit archive function

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

from alembic import op

from app.core.config import settings

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP = '"' + settings.app_db_role.replace('"', "") + '"'

# Tables the runtime role may read and insert but never change or delete.
APPEND_ONLY = (
    "audit_logs",
    "commission_lines",
    "ledger_entries",
    "sub_order_events",
    "vendor_status_events",
    "review_events",
    "payout_events",
    "payout_approvals",
    "outbox_events",
)

AUDIT_COLUMNS = (
    "id, at, actor_id, actor_name, actor_roles, actor_vendor_id, ip, user_agent, module, action,"
    " resource_type, resource_id, before, after, request_id, outcome, reason"
)

HELPERS = """
CREATE OR REPLACE FUNCTION app_scope() RETURNS text LANGUAGE sql STABLE AS
$$ SELECT coalesce(nullif(current_setting('app.scope', true), ''), 'none') $$;
CREATE OR REPLACE FUNCTION app_user_id() RETURNS text LANGUAGE sql STABLE AS
$$ SELECT nullif(current_setting('app.user_id', true), '') $$;
CREATE OR REPLACE FUNCTION app_vendor_id() RETURNS text LANGUAGE sql STABLE AS
$$ SELECT nullif(current_setting('app.vendor_id', true), '') $$;
"""

ARCHIVE_FUNCTION = f"""
CREATE OR REPLACE FUNCTION archive_audit_logs() RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE moved_count integer;
BEGIN
  -- One statement, so rows committed concurrently are either moved or kept, never lost.
  WITH moved AS (DELETE FROM audit_logs RETURNING {AUDIT_COLUMNS})
  INSERT INTO audit_logs_archive ({AUDIT_COLUMNS}, archived_at)
  SELECT {AUDIT_COLUMNS}, now() FROM moved;
  GET DIAGNOSTICS moved_count = ROW_COUNT;
  RETURN moved_count;
END $$;
REVOKE ALL ON FUNCTION archive_audit_logs() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION archive_audit_logs() TO {APP};
"""

PLATFORM = "app_scope() = 'platform'"
VENDOR_OWN = "(app_scope() = 'vendor' AND vendor_id = app_vendor_id())"
CUSTOMER_OWN = "(app_scope() = 'customer' AND buyer_id = app_user_id())"
CATALOGUE_READERS = "app_scope() IN ('platform', 'public', 'customer')"

# (table, policy name, command, USING, WITH CHECK)
POLICIES: list[tuple[str, str, str, str | None, str | None]] = [
    ("vendors", "vendors_read", "SELECT", "true", None),
    ("vendors", "vendors_platform", "ALL", PLATFORM, PLATFORM),
    (
        "vendors",
        "vendors_self_update",
        "UPDATE",
        "(app_scope() = 'vendor' AND id = app_vendor_id())",
        "(app_scope() = 'vendor' AND id = app_vendor_id())",
    ),
    ("vendor_documents", "vendor_documents_access", "ALL", f"{PLATFORM} OR {VENDOR_OWN}", f"{PLATFORM} OR {VENDOR_OWN}"),
    *[
        row
        for table in ("products", "variants", "stock_items")
        for row in (
            (table, f"{table}_read", "SELECT", f"{CATALOGUE_READERS} OR {VENDOR_OWN}", None),
            (table, f"{table}_write", "ALL", f"{PLATFORM} OR {VENDOR_OWN}", f"{PLATFORM} OR {VENDOR_OWN}"),
        )
    ],
    ("stock_reservations", "stock_reservations_platform", "ALL", PLATFORM, PLATFORM),
    (
        "payment_intents",
        "payment_intents_access",
        "ALL",
        f"{PLATFORM} OR (app_scope() = 'customer' AND user_id = app_user_id())",
        f"{PLATFORM} OR (app_scope() = 'customer' AND user_id = app_user_id())",
    ),
    (
        "orders",
        "orders_read",
        "SELECT",
        f"{PLATFORM} OR {CUSTOMER_OWN} OR (app_scope() = 'vendor' AND EXISTS ("
        "SELECT 1 FROM sub_orders s WHERE s.order_id = orders.id AND s.vendor_id = app_vendor_id()))",
        None,
    ),
    ("orders", "orders_platform", "ALL", PLATFORM, PLATFORM),
    ("sub_orders", "sub_orders_read", "SELECT", f"{PLATFORM} OR {VENDOR_OWN} OR {CUSTOMER_OWN}", None),
    ("sub_orders", "sub_orders_platform", "ALL", PLATFORM, PLATFORM),
    ("sub_orders", "sub_orders_vendor_update", "UPDATE", VENDOR_OWN, VENDOR_OWN),
    ("order_lines", "order_lines_read", "SELECT", f"{PLATFORM} OR {VENDOR_OWN} OR {CUSTOMER_OWN}", None),
    ("order_lines", "order_lines_platform", "ALL", PLATFORM, PLATFORM),
    (
        "sub_order_events",
        "sub_order_events_read",
        "SELECT",
        "EXISTS (SELECT 1 FROM sub_orders s WHERE s.id = sub_order_events.sub_order_id)",
        None,
    ),
    ("sub_order_events", "sub_order_events_platform", "ALL", PLATFORM, PLATFORM),
    (
        "sub_order_events",
        "sub_order_events_vendor_insert",
        "INSERT",
        None,
        "app_scope() = 'vendor' AND EXISTS (SELECT 1 FROM sub_orders s"
        " WHERE s.id = sub_order_id AND s.vendor_id = app_vendor_id())",
    ),
    ("commission_lines", "commission_lines_read", "SELECT", f"{PLATFORM} OR {VENDOR_OWN}", None),
    ("commission_lines", "commission_lines_platform", "ALL", PLATFORM, PLATFORM),
    ("ledger_entries", "ledger_entries_read", "SELECT", f"{PLATFORM} OR {VENDOR_OWN}", None),
    ("ledger_entries", "ledger_entries_platform", "ALL", PLATFORM, PLATFORM),
    *[
        row
        for table in ("payouts", "payout_items")
        for row in (
            (table, f"{table}_platform", "ALL", PLATFORM, PLATFORM),
            (table, f"{table}_vendor", "ALL", VENDOR_OWN, VENDOR_OWN),
        )
    ],
    *[
        row
        for table in ("payout_approvals", "payout_events")
        for row in (
            (
                table,
                f"{table}_read",
                "SELECT",
                f"EXISTS (SELECT 1 FROM payouts p WHERE p.id = {table}.payout_id)",
                None,
            ),
            (table, f"{table}_platform", "ALL", PLATFORM, PLATFORM),
        )
    ],
    (
        "payout_events",
        "payout_events_vendor_insert",
        "INSERT",
        None,
        "app_scope() = 'vendor' AND EXISTS (SELECT 1 FROM payouts p"
        " WHERE p.id = payout_id AND p.vendor_id = app_vendor_id())",
    ),
    (
        "coupons",
        "coupons_read",
        "SELECT",
        f"{CATALOGUE_READERS} OR (app_scope() = 'vendor'"
        " AND (vendor_id IS NULL OR vendor_id = app_vendor_id()))",
        None,
    ),
    ("coupons", "coupons_platform", "ALL", PLATFORM, PLATFORM),
    (
        "coupons",
        "coupons_vendor",
        "ALL",
        f"{VENDOR_OWN} AND funded_by = 'vendor'",
        f"{VENDOR_OWN} AND funded_by = 'vendor'",
    ),
    (
        "coupon_redemptions",
        "coupon_redemptions_read",
        "SELECT",
        f"{PLATFORM} OR (app_scope() = 'customer' AND customer_id = app_user_id())",
        None,
    ),
    ("coupon_redemptions", "coupon_redemptions_platform", "ALL", PLATFORM, PLATFORM),
    *[
        (
            table,
            f"{table}_access",
            "ALL",
            f"{PLATFORM} OR {VENDOR_OWN} OR {CUSTOMER_OWN}",
            f"{PLATFORM} OR {VENDOR_OWN} OR {CUSTOMER_OWN}",
        )
        for table in ("conversations", "conversation_messages")
    ],
    ("disputes", "disputes_read", "SELECT", f"{PLATFORM} OR {VENDOR_OWN} OR {CUSTOMER_OWN}", None),
    ("disputes", "disputes_platform", "ALL", PLATFORM, PLATFORM),
    ("disputes", "disputes_customer_insert", "INSERT", None, CUSTOMER_OWN),
    ("reviews", "reviews_read", "SELECT", "true", None),
    ("reviews", "reviews_platform", "ALL", PLATFORM, PLATFORM),
    ("reviews", "reviews_customer", "INSERT", None, CUSTOMER_OWN),
    ("reviews", "reviews_vendor_update", "UPDATE", VENDOR_OWN, VENDOR_OWN),
    (
        "notifications",
        "notifications_own",
        "ALL",
        f"{PLATFORM} OR user_id = app_user_id()",
        f"{PLATFORM} OR user_id = app_user_id()",
    ),
    ("notifications", "notifications_insert", "INSERT", None, "true"),
]


def _policy_sql(table: str, name: str, command: str, using: str | None, check: str | None) -> str:
    sql = f"CREATE POLICY {name} ON {table} FOR {command} TO {APP}"
    if using is not None:
        sql += f" USING ({using})"
    if check is not None:
        sql += f" WITH CHECK ({check})"
    return sql


def rls_tables() -> list[str]:
    return sorted({p[0] for p in POLICIES})


def upgrade() -> None:
    op.execute(HELPERS)
    op.execute(ARCHIVE_FUNCTION)

    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP}")
    op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {APP}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {APP}"
    )
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {APP}")
    op.execute(f"REVOKE UPDATE, DELETE, TRUNCATE ON {', '.join(APPEND_ONLY)} FROM {APP}")
    op.execute(f"REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON audit_logs_archive FROM {APP}")
    op.execute(f"REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON alembic_version FROM {APP}")

    for table in rls_tables():
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    for policy in POLICIES:
        op.execute(_policy_sql(*policy))


def downgrade() -> None:
    for table, name, *_ in POLICIES:
        op.execute(f"DROP POLICY IF EXISTS {name} ON {table}")
    for table in rls_tables():
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute("DROP FUNCTION IF EXISTS archive_audit_logs()")
    op.execute("DROP FUNCTION IF EXISTS app_scope()")
    op.execute("DROP FUNCTION IF EXISTS app_user_id()")
    op.execute("DROP FUNCTION IF EXISTS app_vendor_id()")
    op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {APP}")
    op.execute(f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM {APP}")
