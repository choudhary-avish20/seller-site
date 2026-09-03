"""Add privacy/FAQ/shipping content fields to site_settings for admin-editable info pages

Revision ID: 0006_content_pages
Revises: 0005_wishlist
Create Date: 2026-09-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0006_content_pages'
down_revision: Union[str, None] = '0005_wishlist'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('site_settings', sa.Column('privacy_content', sa.Text(), nullable=True))
    op.add_column('site_settings', sa.Column('faq_content', sa.Text(), nullable=True))
    op.add_column('site_settings', sa.Column('shipping_content', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('site_settings', 'shipping_content')
    op.drop_column('site_settings', 'faq_content')
    op.drop_column('site_settings', 'privacy_content')
