"""add content fuzz scan type

Revision ID: c91a6f0d5b22
Revises: b7e9a2d4f6c1
Create Date: 2026-06-08

"""
from alembic import op


revision = "c91a6f0d5b22"
down_revision = "b7e9a2d4f6c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE scantype ADD VALUE IF NOT EXISTS 'content_fuzz'")


def downgrade() -> None:
    # PostgreSQL nao suporta remocao simples de valores de enum sem recriar o tipo.
    pass
