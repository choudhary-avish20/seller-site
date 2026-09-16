"""Remove stock/inventory tracking fields

Revision ID: 0015_remove_stock_fields
Revises: 0014_pwd_reset_token_version
Create Date: 2026-09-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0015_remove_stock_fields'
down_revision: Union[str, None] = '0014_pwd_reset_token_version'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The seller doesn't track physical inventory — goods are sourced from the
    # wholesale market after an order comes in (see cost_price/stall_location/
    # counter_number, which stay). stock_status here was a plain VARCHAR
    # (sa.String), not a native Postgres ENUM, so no DROP TYPE is needed.
    op.drop_column('products', 'stock_quantity')
    op.drop_column('products', 'stock_status')
    op.drop_column('product_variants', 'stock_quantity')


def downgrade() -> None:
    # server_default backfills existing rows so re-adding a NOT NULL column
    # succeeds on a non-empty table; drop the default afterward to match the
    # original schema, where defaults were applied at the ORM layer only.
    op.add_column('products', sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('products', sa.Column('stock_status', sa.String(length=32), nullable=False, server_default='in_stock'))
    op.add_column('product_variants', sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('products', 'stock_quantity', server_default=None)
    op.alter_column('products', 'stock_status', server_default=None)
    op.alter_column('product_variants', 'stock_quantity', server_default=None)
