"""Add country fields to tasks and contacts tables

Revision ID: 002
Revises: 001
Create Date: 2025-01-04

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Import for checking if column exists
    from sqlalchemy import inspect
    from alembic import op
    
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Add country column to tasks table if it doesn't exist
    tasks_columns = [col['name'] for col in inspector.get_columns('tasks')]
    if 'country' not in tasks_columns:
        op.add_column('tasks', sa.Column('country', sa.String(2), nullable=False, server_default='ID', comment='國家代碼'))
    
    # Add country column to contacts table if it doesn't exist
    contacts_columns = [col['name'] for col in inspector.get_columns('contacts')]
    if 'country' not in contacts_columns:
        op.add_column('contacts', sa.Column('country', sa.String(2), nullable=False, server_default='ID', comment='國家代碼'))
    
    # Create indexes for country fields if they don't exist
    tasks_indexes = [idx['name'] for idx in inspector.get_indexes('tasks')]
    if 'idx_tasks_country' not in tasks_indexes:
        op.create_index('idx_tasks_country', 'tasks', ['country'])
    
    contacts_indexes = [idx['name'] for idx in inspector.get_indexes('contacts')]
    if 'idx_contacts_country' not in contacts_indexes:
        op.create_index('idx_contacts_country', 'contacts', ['country'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_contacts_country', table_name='contacts')
    op.drop_index('idx_tasks_country', table_name='tasks')
    
    # Drop country columns
    op.drop_column('contacts', 'country')
    op.drop_column('tasks', 'country')
