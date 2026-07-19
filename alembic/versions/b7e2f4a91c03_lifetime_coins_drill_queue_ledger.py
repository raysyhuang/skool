"""Add lifetime_coins, pending_drill_char_ids, and ledger coins_change

Revision ID: b7e2f4a91c03
Revises: da3cbaf1daec
Create Date: 2026-07-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b7e2f4a91c03'
down_revision = 'da3cbaf1daec'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('lifetime_coins', sa.Integer(), server_default='0'))
    op.add_column('users', sa.Column('pending_drill_char_ids', sa.String(), nullable=True))
    op.add_column('points_ledger', sa.Column('coins_change', sa.Integer(), server_default='0'))

    # Backfill lifetime_coins so existing car levels never demote
    greatest = 'GREATEST' if op.get_bind().dialect.name == 'postgresql' else 'MAX'
    op.execute(
        f"UPDATE users SET lifetime_coins = {greatest}("
        "COALESCE(coins, 0), "
        "CASE COALESCE(car_level, 0) WHEN 1 THEN 5 WHEN 2 THEN 15 "
        "WHEN 3 THEN 30 WHEN 4 THEN 50 ELSE 0 END)"
    )


def downgrade():
    op.drop_column('points_ledger', 'coins_change')
    op.drop_column('users', 'pending_drill_char_ids')
    op.drop_column('users', 'lifetime_coins')
