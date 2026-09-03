"""Add coupons table and order discount tracking

Revision ID: 0009_coupons
Revises: 0008_reviews
Create Date: 2026-09-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0009_coupons'
down_revision: Union[str, None] = '0008_reviews'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'coupons',
        sa.Column('code', sa.String(64), nullable=False),
        sa.Column('discount_type', sa.Enum('percent', 'fixed', name='coupon_discount_type'), nullable=False),
        sa.Column('discount_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('min_order_net', sa.Numeric(10, 2), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_coupon_code'),
    )
    op.create_index(op.f('ix_coupons_code'), 'coupons', ['code'])

    op.add_column('orders', sa.Column('coupon_code', sa.String(64), nullable=True))
    op.add_column('orders', sa.Column('discount_amount', sa.Numeric(10, 2), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('orders', 'discount_amount')
    op.drop_column('orders', 'coupon_code')
    op.drop_index(op.f('ix_coupons_code'), table_name='coupons')
    op.drop_table('coupons')
