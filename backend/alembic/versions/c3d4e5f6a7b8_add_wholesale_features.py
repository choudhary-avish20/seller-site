"""add wholesale features: tier pricing, stall, buyer approval, order COD details

Revision ID: c3d4e5f6a7b8
Revises: c2a1f3b5d8e9
Create Date: 2026-08-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'c2a1f3b5d8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    buyer_status = sa.Enum('pending', 'approved', 'rejected', name='buyer_status')
    buyer_status.create(op.get_bind(), checkfirst=True)
    payment_method = sa.Enum('cod', name='payment_method')
    payment_method.create(op.get_bind(), checkfirst=True)

    # product_price_tiers
    op.create_table('product_price_tiers',
        sa.Column('product_id', sa.UUID(), nullable=False),
        sa.Column('min_quantity', sa.Integer(), nullable=False),
        sa.Column('max_quantity', sa.Integer(), nullable=True),
        sa.Column('price_net', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_price_tiers_product_id'), 'product_price_tiers', ['product_id'], unique=False)

    # products new columns
    op.add_column('products', sa.Column('pack_increment', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('products', sa.Column('cost_price', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('products', sa.Column('stall_location', sa.String(length=255), nullable=True))
    op.add_column('products', sa.Column('counter_number', sa.String(length=64), nullable=True))

    # users buyer approval
    op.add_column('users', sa.Column('buyer_status', buyer_status, nullable=False, server_default='approved'))
    op.add_column('users', sa.Column('buyer_rejection_reason', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('company_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('company_tax_id', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('company_address', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=32), nullable=True))

    # orders new columns
    op.add_column('orders', sa.Column('company_name', sa.Text(), nullable=True))
    op.add_column('orders', sa.Column('company_tax_id', sa.String(length=64), nullable=True))
    op.add_column('orders', sa.Column('company_address', sa.Text(), nullable=True))
    op.add_column('orders', sa.Column('recipient_name', sa.String(length=255), nullable=True))
    op.add_column('orders', sa.Column('recipient_phone', sa.String(length=32), nullable=True))
    op.add_column('orders', sa.Column('recipient_address', sa.Text(), nullable=True))
    op.add_column('orders', sa.Column('payment_method', payment_method, nullable=False, server_default='cod'))

    # order_items snapshots
    op.add_column('order_items', sa.Column('cost_price_snapshot', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('order_items', sa.Column('stall_location_snapshot', sa.String(length=255), nullable=True))
    op.add_column('order_items', sa.Column('counter_number_snapshot', sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column('order_items', 'counter_number_snapshot')
    op.drop_column('order_items', 'stall_location_snapshot')
    op.drop_column('order_items', 'cost_price_snapshot')
    op.drop_column('orders', 'payment_method')
    op.drop_column('orders', 'recipient_address')
    op.drop_column('orders', 'recipient_phone')
    op.drop_column('orders', 'recipient_name')
    op.drop_column('orders', 'company_address')
    op.drop_column('orders', 'company_tax_id')
    op.drop_column('orders', 'company_name')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'company_address')
    op.drop_column('users', 'company_tax_id')
    op.drop_column('users', 'company_name')
    op.drop_column('users', 'buyer_rejection_reason')
    op.drop_column('users', 'buyer_status')
    op.drop_column('products', 'counter_number')
    op.drop_column('products', 'stall_location')
    op.drop_column('products', 'cost_price')
    op.drop_column('products', 'pack_increment')
    op.drop_index(op.f('ix_product_price_tiers_product_id'), table_name='product_price_tiers')
    op.drop_table('product_price_tiers')
    try:
        sa.Enum(name='buyer_status').drop(op.get_bind(), checkfirst=True)
        sa.Enum(name='payment_method').drop(op.get_bind(), checkfirst=True)
    except Exception:
        pass
