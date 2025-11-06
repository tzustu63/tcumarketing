"""add keyword to contacts

Revision ID: 003
Revises: 002
Create Date: 2025-01-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Add keyword column to contacts table"""
    # Add keyword column
    op.add_column('contacts', sa.Column('keyword', sa.String(255), nullable=True, comment='搜尋關鍵字'))
    
    # Create index on keyword for efficient filtering
    op.create_index('idx_contacts_keyword', 'contacts', ['keyword'])


def downgrade():
    """Remove keyword column from contacts table"""
    # Drop index
    op.drop_index('idx_contacts_keyword', table_name='contacts')
    
    # Drop column
    op.drop_column('contacts', 'keyword')
