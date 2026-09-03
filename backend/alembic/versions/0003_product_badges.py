"""Add merchandising badges (bestseller, popular, on_sale, sale_price) to products

Revision ID: 0003_product_badges
Revises: 0002_site_settings
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0003_product_badges'
down_revision: Union[str, None] = '0002_site_settings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('is_bestseller', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column('products', sa.Column('is_popular', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column('products', sa.Column('is_on_sale', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column('products', sa.Column('sale_price_net', sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'sale_price_net')
    op.drop_column('products', 'is_on_sale')
    op.drop_column('products', 'is_popular')
    op.drop_column('products', 'is_bestseller')
