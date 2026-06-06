"""add recon tables

Revision ID: 4b79fc586a84
Revises: 3a0f5da3b885
Create Date: 2026-06-06 17:32:27.160830

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b79fc586a84'
down_revision: str | None = '3a0f5da3b885'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('projects',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('owner_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_owner_id'), 'projects', ['owner_id'], unique=False)
    op.create_table('targets',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('value', sa.String(length=255), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('in_scope', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('project_id', 'value', name='uq_target_project_value')
    )
    op.create_index(op.f('ix_targets_project_id'), 'targets', ['project_id'], unique=False)
    op.create_table('scans',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('target_id', sa.UUID(), nullable=False),
    sa.Column('scan_type', sa.Enum('SUBDOMAIN_ENUM', 'HTTP_PROBE', 'PORT_SCAN', name='scantype'), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', name='scanstatus'), nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['target_id'], ['targets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scans_target_id'), 'scans', ['target_id'], unique=False)
    op.create_table('scan_results',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('scan_id', sa.UUID(), nullable=False),
    sa.Column('value', sa.String(length=512), nullable=False),
    sa.Column('data', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scan_results_scan_id'), 'scan_results', ['scan_id'], unique=False)
def downgrade() -> None:
    op.drop_index(op.f('ix_scan_results_scan_id'), table_name='scan_results')
    op.drop_table('scan_results')
    op.drop_index(op.f('ix_scans_target_id'), table_name='scans')
    op.drop_table('scans')
    op.drop_index(op.f('ix_targets_project_id'), table_name='targets')
    op.drop_table('targets')
    op.drop_index(op.f('ix_projects_owner_id'), table_name='projects')
    op.drop_table('projects')
    op.drop_enum = lambda name: None  # enums dropped automatically with tables in PG
