"""add performance indexes

Revision ID: 005
Revises: 004
Create Date: 2025-01-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for frequently queried columns"""
    # Add index on contacts.source_platform for filtering
    op.create_index('idx_contacts_source_platform', 'contacts', ['source_platform'])
    
    # Add index on tasks.city for filtering (if not exists)
    # Check if index exists first
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tasks_indexes = [idx['name'] for idx in inspector.get_indexes('tasks')]
    if 'idx_tasks_city' not in tasks_indexes:
        op.create_index('idx_tasks_city', 'tasks', ['city'])
    
    # Add composite index for common query patterns
    # Index on (country, keyword) for contacts
    op.create_index('idx_contacts_country_keyword', 'contacts', ['country', 'keyword'])
    
    # Index on (country, city) for tasks
    op.create_index('idx_tasks_country_city', 'tasks', ['country', 'city'])


def downgrade():
    """Remove performance indexes"""
    op.drop_index('idx_tasks_country_city', table_name='tasks')
    op.drop_index('idx_contacts_country_keyword', table_name='contacts')
    op.drop_index('idx_tasks_city', table_name='tasks')
    op.drop_index('idx_contacts_source_platform', table_name='contacts')



