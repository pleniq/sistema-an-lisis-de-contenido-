"""indices de hardening

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-15

Postgres no indexa automáticamente las columnas FK ni las de ORDER BY.
Agregamos índices en reels.account_id (filtrado/labels por cuenta) y
reels.published_at (el ORDER BY del listado). El índice de snapshots por reel
ya lo cubre el UNIQUE(reel_id, snapshot_date).
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_reels_account_id", "reels", ["account_id"])
    op.create_index("ix_reels_published_at", "reels", ["published_at"])


def downgrade() -> None:
    op.drop_index("ix_reels_published_at", table_name="reels")
    op.drop_index("ix_reels_account_id", table_name="reels")
