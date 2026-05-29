"""add attached_link_ids to dashboard_links

Revision ID: 003_add_attached_link_ids
Revises: 002_dashboard_link_logs
Create Date: 2026-05-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003_add_attached_link_ids'
down_revision = '002_dashboard_link_logs'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'dashboard_links',
        sa.Column(
            'attached_link_ids',
            postgresql.ARRAY(sa.Integer()),
            nullable=True
        )
    )


def downgrade():
    op.drop_column('dashboard_links', 'attached_link_ids')
