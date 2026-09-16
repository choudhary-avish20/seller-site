"""Add cancellation_policy_content to site_settings

Revision ID: 0016_cancellation_policy_content
Revises: 0015_remove_stock_fields
Create Date: 2026-09-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0016_cancellation_policy_content'
down_revision: Union[str, None] = '0015_remove_stock_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('site_settings', sa.Column('cancellation_policy_content', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('site_settings', 'cancellation_policy_content')
