"""create audit logs table

Revision ID: 001_create_audit_logs
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_create_audit_logs'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enum type for audit log actions
    op.execute("""
        CREATE TYPE auditlogaction AS ENUM (
            'login',
            'logout',
            'user_created',
            'sync_brands',
            'sync_prompts',
            'sync_responses',
            'sync_ga4',
            'sync_agency_analytics',
            'sync_all'
        )
    """)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', postgresql.ENUM('login', 'logout', 'user_created', 'sync_brands', 'sync_prompts', 'sync_responses', 'sync_ga4', 'sync_agency_analytics', 'sync_all', name='auditlogaction'), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('user_email', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_user_email', 'audit_logs', ['user_email'])
    op.create_index('ix_audit_logs_status', 'audit_logs', ['status'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_status', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_email', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    
    # Drop table
    op.drop_table('audit_logs')
    
    # Drop enum type
    op.execute('DROP TYPE auditlogaction')

