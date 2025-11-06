"""add stored keywords and cities table

Revision ID: 004
Revises: 003
Create Date: 2025-01-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Create stored_keywords table for user-defined keywords and cities"""
    # Create stored_keywords table
    op.create_table(
        'stored_keywords',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('country', sa.String(2), nullable=False, comment='國家代碼'),
        sa.Column('keyword', sa.String(255), nullable=True, comment='關鍵字'),
        sa.Column('city', sa.String(100), nullable=True, comment='城市'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='建立時間'),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False, comment='是否已刪除'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('country', 'keyword', 'city', name='uix_stored_keywords_unique'),
        comment='儲存用戶自定義的關鍵字和城市'
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_stored_keywords_country', 'stored_keywords', ['country'])
    op.create_index('idx_stored_keywords_keyword', 'stored_keywords', ['keyword'])
    op.create_index('idx_stored_keywords_city', 'stored_keywords', ['city'])
    op.create_index('idx_stored_keywords_country_keyword', 'stored_keywords', ['country', 'keyword'])
    op.create_index('idx_stored_keywords_country_city', 'stored_keywords', ['country', 'city'])


def downgrade():
    """Remove stored_keywords table"""
    # Drop indexes
    op.drop_index('idx_stored_keywords_country_city', table_name='stored_keywords')
    op.drop_index('idx_stored_keywords_country_keyword', table_name='stored_keywords')
    op.drop_index('idx_stored_keywords_city', table_name='stored_keywords')
    op.drop_index('idx_stored_keywords_keyword', table_name='stored_keywords')
    op.drop_index('idx_stored_keywords_country', table_name='stored_keywords')
    
    # Drop table
    op.drop_table('stored_keywords')



