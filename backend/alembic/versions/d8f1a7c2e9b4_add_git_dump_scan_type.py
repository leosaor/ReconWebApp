"""add git dump scan type

Revision ID: d8f1a7c2e9b4
Revises: c91a6f0d5b22
Create Date: 2026-06-08

"""
from alembic import op


revision = "d8f1a7c2e9b4"
down_revision = "c91a6f0d5b22"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE scantype ADD VALUE IF NOT EXISTS 'git_dump'")


def downgrade() -> None:
    # PostgreSQL nao suporta remocao simples de valores de enum sem recriar o tipo.
    pass
