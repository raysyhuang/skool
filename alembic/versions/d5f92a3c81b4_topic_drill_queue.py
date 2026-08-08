"""Add a queued math/English topic drill

Revision ID: d5f92a3c81b4
Revises: c4d81f0a2b17
Create Date: 2026-08-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd5f92a3c81b4'
down_revision = 'c4d81f0a2b17'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('pending_drill_topic_ids', sa.String(), nullable=True))


def downgrade():
    op.drop_column('users', 'pending_drill_topic_ids')
