"""add tls scan type

Revision ID: b7e9a2d4f6c1
Revises: a4f2d9c8e1b0
Create Date: 2026-06-08

"""
from alembic import op


revision = "b7e9a2d4f6c1"
down_revision = "a4f2d9c8e1b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE scantype ADD VALUE IF NOT EXISTS 'tls_scan'")


def downgrade() -> None:
    # PostgreSQL nao suporta remocao simples de valores de enum sem recriar o tipo.
    pass
