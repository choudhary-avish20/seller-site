"""Add hidden_by_buyer flag to orders

Revision ID: 0010_order_hide
Revises: 0009_coupons
Create Date: 2026-09-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0010_order_hide'
down_revision: Union[str, None] = '0009_coupons'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('hidden_by_buyer', sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    op.drop_column('orders', 'hidden_by_buyer')
