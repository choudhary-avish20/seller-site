"""Add terms_content to site_settings for the admin-editable Terms & Conditions page

Revision ID: 0004_terms_content
Revises: 0003_product_badges
Create Date: 2026-09-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0004_terms_content'
down_revision: Union[str, None] = '0003_product_badges'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('site_settings', sa.Column('terms_content', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('site_settings', 'terms_content')
