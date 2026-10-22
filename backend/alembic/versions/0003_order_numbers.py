"""order number sequence (O-1007, O-1008, ...)

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

from alembic import op

from app.core.config import settings

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP = '"' + settings.app_db_role.replace('"', "") + '"'


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS order_number_seq START WITH 1007")
    op.execute(f"GRANT USAGE, SELECT ON SEQUENCE order_number_seq TO {APP}")


def downgrade() -> None:
    op.execute("DROP SEQUENCE IF EXISTS order_number_seq")
