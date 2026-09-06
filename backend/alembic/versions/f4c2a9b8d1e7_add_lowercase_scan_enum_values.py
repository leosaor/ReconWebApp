"""add lowercase scan enum values

Revision ID: f4c2a9b8d1e7
Revises: e3b7a1d5c9f2
Create Date: 2026-09-06

"""
from alembic import op


revision = "f4c2a9b8d1e7"
down_revision = "e3b7a1d5c9f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE scantype ADD VALUE IF NOT EXISTS 'subdomain_enum'")
    op.execute("ALTER TYPE scantype ADD VALUE IF NOT EXISTS 'http_probe'")
    op.execute("ALTER TYPE scantype ADD VALUE IF NOT EXISTS 'port_scan'")
    op.execute("ALTER TYPE scanstatus ADD VALUE IF NOT EXISTS 'pending'")
    op.execute("ALTER TYPE scanstatus ADD VALUE IF NOT EXISTS 'running'")
    op.execute("ALTER TYPE scanstatus ADD VALUE IF NOT EXISTS 'completed'")
    op.execute("ALTER TYPE scanstatus ADD VALUE IF NOT EXISTS 'failed'")


def downgrade() -> None:
    # PostgreSQL nao suporta remocao simples de valores de enum sem recriar o tipo.
    pass
