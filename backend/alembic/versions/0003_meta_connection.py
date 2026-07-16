"""tabla meta_connection (token de Meta gestionado desde la app)

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meta_connection",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("ig_user_id", sa.String(length=64), nullable=True),
        sa.Column("account_name", sa.String(length=255), nullable=False, server_default="Instagram"),
        sa.Column("app_id", sa.String(length=64), nullable=True),
        sa.Column("app_secret", sa.String(length=255), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_ok", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("meta_connection")
