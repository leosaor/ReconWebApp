"""add new scan types

Revision ID: 6d3e1f8b2c47
Revises: 4b79fc586a84
Create Date: 2026-06-08

"""
from alembic import op

revision = "6d3e1f8b2c47"
down_revision = "4b79fc586a84"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE scantype ADD VALUE IF NOT EXISTS 'header_check'")
    op.execute("ALTER TYPE scantype ADD VALUE IF NOT EXISTS 'clickjacking'")
    op.execute("ALTER TYPE scantype ADD VALUE IF NOT EXISTS 'domain_spoofing'")


def downgrade() -> None:
    # PostgreSQL não suporta remoção de valores de enum sem recriar o tipo.
    pass
