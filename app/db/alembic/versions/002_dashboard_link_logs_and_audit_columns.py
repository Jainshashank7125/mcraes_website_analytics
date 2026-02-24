"""dashboard link logs and created_by/updated_by on dashboard_links

Revision ID: 002_dashboard_link_logs
Revises: 001_create_audit_logs
Create Date: 2025-02-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_dashboard_link_logs'
down_revision = '001_create_audit_logs'
branch_labels = None
depends_on = None


def upgrade():
    # Add created_by, updated_by to dashboard_links
    op.add_column('dashboard_links', sa.Column('created_by', sa.String(), nullable=True))
    op.add_column('dashboard_links', sa.Column('updated_by', sa.String(), nullable=True))
    op.create_index('ix_dashboard_links_created_by', 'dashboard_links', ['created_by'])
    op.create_index('ix_dashboard_links_updated_by', 'dashboard_links', ['updated_by'])

    # Create dashboard_link_logs table
    op.create_table(
        'dashboard_link_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dashboard_link_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('changes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['dashboard_link_id'], ['dashboard_links.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dashboard_link_logs_dashboard_link_id', 'dashboard_link_logs', ['dashboard_link_id'])
    op.create_index('ix_dashboard_link_logs_action', 'dashboard_link_logs', ['action'])
    op.create_index('ix_dashboard_link_logs_created_at', 'dashboard_link_logs', ['created_at'])
    op.create_index('ix_dashboard_link_logs_created_by', 'dashboard_link_logs', ['created_by'])


def downgrade():
    op.drop_index('ix_dashboard_link_logs_created_by', table_name='dashboard_link_logs')
    op.drop_index('ix_dashboard_link_logs_created_at', table_name='dashboard_link_logs')
    op.drop_index('ix_dashboard_link_logs_action', table_name='dashboard_link_logs')
    op.drop_index('ix_dashboard_link_logs_dashboard_link_id', table_name='dashboard_link_logs')
    op.drop_table('dashboard_link_logs')

    op.drop_index('ix_dashboard_links_updated_by', table_name='dashboard_links')
    op.drop_index('ix_dashboard_links_created_by', table_name='dashboard_links')
    op.drop_column('dashboard_links', 'updated_by')
    op.drop_column('dashboard_links', 'created_by')
