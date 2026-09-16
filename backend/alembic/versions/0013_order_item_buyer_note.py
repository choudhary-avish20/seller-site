"""Add per-item buyer note to order_items

Revision ID: 0013_order_item_buyer_note
Revises: 0012_category_sort_order
Create Date: 2026-09-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0013_order_item_buyer_note'
down_revision: Union[str, None] = '0012_category_sort_order'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Distinct from orders.notes (the one whole-order shipping/delivery note) —
    # this is a free-text note the buyer can leave against each individual
    # product while it's in their cart.
    op.add_column('order_items', sa.Column('buyer_note', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('order_items', 'buyer_note')
