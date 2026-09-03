"""Add addresses table for saved buyer delivery addresses

Revision ID: 0007_addresses
Revises: 0006_content_pages
Create Date: 2026-09-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0007_addresses'
down_revision: Union[str, None] = '0006_content_pages'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'addresses',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('recipient_name', sa.String(length=255), nullable=True),
        sa.Column('recipient_phone', sa.String(length=32), nullable=True),
        sa.Column('street', sa.String(length=255), nullable=False),
        sa.Column('zip_code', sa.String(length=10), nullable=False),
        sa.Column('city', sa.String(length=120), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('company_tax_id', sa.String(length=64), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_addresses_user_id'), 'addresses', ['user_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_addresses_user_id'), table_name='addresses')
    op.drop_table('addresses')
