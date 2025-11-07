"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('keyword', sa.String(255), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('target_platforms', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('max_results', sa.Integer, default=100),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('progress', sa.Integer, default=0),
        sa.Column('results_count', sa.Integer, default=0),
        sa.Column('error_message', sa.String, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
    )
    
    # Create contacts table
    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('institution_name', sa.String(500), nullable=False),
        sa.Column('institution_type', sa.String(50), nullable=True),
        sa.Column('source_url', sa.String, nullable=False),
        sa.Column('source_platform', sa.String(20), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('whatsapp', sa.String(50), nullable=True),
        sa.Column('additional_info', postgresql.JSONB, nullable=True),
        sa.Column('quality_score', sa.Float, nullable=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('extracted_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('source_url', 'email', 'whatsapp', name='uix_contact_unique'),
    )
    
    # Create scraping_logs table
    op.create_table(
        'scraping_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String, nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error_message', sa.String, nullable=True),
        sa.Column('response_time', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_created_at', 'tasks', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_contacts_task_id', 'contacts', ['task_id'])
    op.create_index('idx_contacts_institution_type', 'contacts', ['institution_type'])
    op.create_index('idx_contacts_extracted_at', 'contacts', ['extracted_at'], postgresql_ops={'extracted_at': 'DESC'})
    op.create_index('idx_contacts_quality_score', 'contacts', ['quality_score'], postgresql_ops={'quality_score': 'DESC'})
    op.create_index('idx_scraping_logs_task_id', 'scraping_logs', ['task_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_scraping_logs_task_id', table_name='scraping_logs')
    op.drop_index('idx_contacts_quality_score', table_name='contacts')
    op.drop_index('idx_contacts_extracted_at', table_name='contacts')
    op.drop_index('idx_contacts_institution_type', table_name='contacts')
    op.drop_index('idx_contacts_task_id', table_name='contacts')
    op.drop_index('idx_tasks_created_at', table_name='tasks')
    op.drop_index('idx_tasks_status', table_name='tasks')
    
    # Drop tables
    op.drop_table('scraping_logs')
    op.drop_table('contacts')
    op.drop_table('tasks')
