"""add composite indexes for performance

Revision ID: e8f3a1b2c4d5
Revises: d5f92a3c81b4
Create Date: 2026-11-01 18:24:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8f3a1b2c4d5'
down_revision = 'd5f92a3c81b4'
branch_labels = None
depends_on = None


def upgrade():
    # Composite index for review schedule queries (user_id, next_review_date)
    op.create_index(
        'ix_user_char_progress_review',
        'user_character_progress',
        ['user_id', 'next_review_date'],
        unique=False
    )
    
    # Composite index for weakest characters queries (user_id, mastery_score)
    op.create_index(
        'ix_user_char_progress_mastery',
        'user_character_progress',
        ['user_id', 'mastery_score'],
        unique=False
    )
    
    # Composite index for topic progress queries (user_id, topic_id)
    op.create_index(
        'ix_user_topic_progress_lookup',
        'user_topic_progress',
        ['user_id', 'topic_id'],
        unique=False
    )


def downgrade():
    op.drop_index('ix_user_topic_progress_lookup', table_name='user_topic_progress')
    op.drop_index('ix_user_char_progress_mastery', table_name='user_character_progress')
    op.drop_index('ix_user_char_progress_review', table_name='user_character_progress')
