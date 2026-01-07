"""Initial schema

Revision ID: 001
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial AegisTwin schema."""
    
    # Runs table
    op.create_table(
        'runs',
        sa.Column('run_id', sa.String(32), primary_key=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('source', sa.String(255), nullable=True),
        sa.Column('event_count', sa.Integer(), server_default='0'),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
    )
    
    # Events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.String(32), sa.ForeignKey('runs.run_id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_id', sa.String(64), nullable=False),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('payload_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Indexes for events
    op.create_index('idx_events_run_id', 'events', ['run_id'])
    op.create_index('idx_events_type', 'events', ['event_type'])
    op.create_index('idx_events_timestamp', 'events', ['timestamp'])
    
    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('actor', sa.String(255), nullable=False),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('resource', sa.String(255), nullable=False),
        sa.Column('outcome', sa.String(64), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
    )
    
    # Indexes for audit logs
    op.create_index('idx_audit_actor', 'audit_logs', ['actor'])
    op.create_index('idx_audit_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('idx_audit_timestamp', 'audit_logs')
    op.drop_index('idx_audit_action', 'audit_logs')
    op.drop_index('idx_audit_actor', 'audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('idx_events_timestamp', 'events')
    op.drop_index('idx_events_type', 'events')
    op.drop_index('idx_events_run_id', 'events')
    op.drop_table('events')
    
    op.drop_table('runs')
