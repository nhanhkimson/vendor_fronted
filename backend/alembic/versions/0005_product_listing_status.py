"""product listing maker-checker status

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("products", sa.Column("listing_status", sa.String(length=20), nullable=False, server_default="published"))
    op.add_column("products", sa.Column("listing_reason", sa.String(length=255), nullable=True))
    op.create_index("ix_products_listing_status", "products", ["listing_status"])
    op.execute(
        """
        UPDATE products
        SET listing_status = CASE
            WHEN archived_at IS NOT NULL THEN 'archived'
            WHEN active IS FALSE THEN 'draft'
            ELSE 'published'
        END
        """
    )
    op.alter_column("products", "listing_status", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_products_listing_status", table_name="products")
    op.drop_column("products", "listing_reason")
    op.drop_column("products", "listing_status")
