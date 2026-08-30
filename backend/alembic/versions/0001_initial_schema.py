"""Full initial schema (SQLite + PostgreSQL compatible)

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'categories',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_categories_slug'), 'categories', ['slug'], unique=True)

    op.create_table(
        'users',
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        # Store as plain String so both SQLite and PostgreSQL work without ALTER TYPE
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('buyer_status', sa.String(length=32), nullable=False),
        sa.Column('buyer_rejection_reason', sa.String(length=500), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('company_tax_id', sa.String(length=64), nullable=True),
        sa.Column('company_address', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=32), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'seller_profiles',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('business_name', sa.String(length=255), nullable=False),
        sa.Column('tax_id', sa.String(length=64), nullable=True),
        sa.Column('business_address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(length=32), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('rejection_reason', sa.String(length=500), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_seller_profiles_user_id'), 'seller_profiles', ['user_id'], unique=True)

    op.create_table(
        'orders',
        sa.Column('buyer_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('total_net', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_gross', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('shipping_address', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('company_name', sa.Text(), nullable=True),
        sa.Column('company_tax_id', sa.String(length=64), nullable=True),
        sa.Column('company_address', sa.Text(), nullable=True),
        sa.Column('recipient_name', sa.String(length=255), nullable=True),
        sa.Column('recipient_phone', sa.String(length=32), nullable=True),
        sa.Column('recipient_address', sa.Text(), nullable=True),
        sa.Column('payment_method', sa.String(length=32), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_orders_buyer_id'), 'orders', ['buyer_id'], unique=False)

    op.create_table(
        'products',
        sa.Column('category_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('images', sa.Text(), nullable=False),
        sa.Column('pack_size', sa.Integer(), nullable=False),
        sa.Column('price_net', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('price_gross', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('vat_rate', sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column('pack_increment', sa.Integer(), nullable=False),
        sa.Column('cost_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('stall_location', sa.String(length=255), nullable=True),
        sa.Column('counter_number', sa.String(length=64), nullable=True),
        sa.Column('stock_quantity', sa.Integer(), nullable=False),
        sa.Column('stock_status', sa.String(length=32), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)
    op.create_index(op.f('ix_products_slug'), 'products', ['slug'], unique=True)

    op.create_table(
        'product_price_tiers',
        sa.Column('product_id', sa.UUID(), nullable=False),
        sa.Column('min_quantity', sa.Integer(), nullable=False),
        sa.Column('max_quantity', sa.Integer(), nullable=True),
        sa.Column('price_net', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_product_price_tiers_product_id'), 'product_price_tiers', ['product_id'], unique=False)

    op.create_table(
        'product_variants',
        sa.Column('product_id', sa.UUID(), nullable=False),
        sa.Column('sku', sa.String(length=64), nullable=False),
        sa.Column('option_name', sa.String(length=64), nullable=False),
        sa.Column('option_value', sa.String(length=64), nullable=False),
        sa.Column('price_net_override', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('stock_quantity', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku'),
    )
    op.create_index(op.f('ix_product_variants_product_id'), 'product_variants', ['product_id'], unique=False)

    op.create_table(
        'order_items',
        sa.Column('order_id', sa.UUID(), nullable=False),
        sa.Column('product_id', sa.UUID(), nullable=False),
        sa.Column('variant_id', sa.UUID(), nullable=True),
        sa.Column('product_name_snapshot', sa.String(length=255), nullable=False),
        sa.Column('pack_size_snapshot', sa.Integer(), nullable=False),
        sa.Column('price_net_snapshot', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('price_gross_snapshot', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('cost_price_snapshot', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('stall_location_snapshot', sa.String(length=255), nullable=True),
        sa.Column('counter_number_snapshot', sa.String(length=64), nullable=True),
        sa.Column('pack_quantity', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_order_items_order_id'), table_name='order_items')
    op.drop_table('order_items')
    op.drop_index(op.f('ix_product_variants_product_id'), table_name='product_variants')
    op.drop_table('product_variants')
    op.drop_index(op.f('ix_product_price_tiers_product_id'), table_name='product_price_tiers')
    op.drop_table('product_price_tiers')
    op.drop_index(op.f('ix_products_slug'), table_name='products')
    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_table('products')
    op.drop_index(op.f('ix_orders_buyer_id'), table_name='orders')
    op.drop_table('orders')
    op.drop_index(op.f('ix_seller_profiles_user_id'), table_name='seller_profiles')
    op.drop_table('seller_profiles')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_categories_slug'), table_name='categories')
    op.drop_table('categories')
