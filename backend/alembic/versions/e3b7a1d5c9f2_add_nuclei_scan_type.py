"""add nuclei scan type

Revision ID: e3b7a1d5c9f2
Revises: d8f1a7c2e9b4
Create Date: 2026-06-08

"""
from alembic import op


revision = "e3b7a1d5c9f2"
down_revision = "d8f1a7c2e9b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE scantype ADD VALUE IF NOT EXISTS 'nuclei_scan'")


def downgrade() -> None:
    # PostgreSQL nao suporta remocao simples de valores de enum sem recriar o tipo.
    pass
