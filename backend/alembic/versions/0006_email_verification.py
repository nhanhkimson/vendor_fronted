"""email verification challenges and verified_at

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP = "bazaar_app"


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE users SET email_verified_at = created_at WHERE email_verified_at IS NULL")

    op.create_table(
        "email_challenges",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", sa.String(length=2000), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_challenges")),
    )
    op.create_index("ix_email_challenges_email", "email_challenges", ["email"])
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON email_challenges TO {APP}")


def downgrade() -> None:
    op.drop_index("ix_email_challenges_email", table_name="email_challenges")
    op.drop_table("email_challenges")
    op.drop_column("users", "email_verified_at")
