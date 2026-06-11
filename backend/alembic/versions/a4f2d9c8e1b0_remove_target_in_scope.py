"""remove target in_scope

Revision ID: a4f2d9c8e1b0
Revises: 6d3e1f8b2c47
Create Date: 2026-06-08

"""
from alembic import op
import sqlalchemy as sa


revision = "a4f2d9c8e1b0"
down_revision = "6d3e1f8b2c47"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("targets", "in_scope")


def downgrade() -> None:
    op.add_column(
        "targets",
        sa.Column("in_scope", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("targets", "in_scope", server_default=None)
