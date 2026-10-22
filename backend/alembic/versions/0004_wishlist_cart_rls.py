"""row-level security for wishlists and carts

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

from alembic import op

from app.core.config import settings

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP = '"' + settings.app_db_role.replace('"', "") + '"'
OWN = "app_scope() = 'platform' OR user_id = app_user_id()"
LINE = (
    "app_scope() = 'platform' OR EXISTS (SELECT 1 FROM carts c"
    " WHERE c.id = cart_lines.cart_id AND c.user_id = app_user_id())"
)
LINE_CHECK = (
    "app_scope() = 'platform' OR EXISTS (SELECT 1 FROM carts c"
    " WHERE c.id = cart_id AND c.user_id = app_user_id())"
)

POLICIES = [
    ("wishlist_items", "wishlist_own", OWN, OWN),
    ("carts", "carts_own", OWN, OWN),
    ("cart_lines", "cart_lines_own", LINE, LINE_CHECK),
]


def upgrade() -> None:
    for table, name, using, check in POLICIES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {name} ON {table} FOR ALL TO {APP} USING ({using}) WITH CHECK ({check})"
        )


def downgrade() -> None:
    for table, name, *_ in POLICIES:
        op.execute(f"DROP POLICY IF EXISTS {name} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
