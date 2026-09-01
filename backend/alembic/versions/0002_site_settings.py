"""Add site_settings table for public contact page info

Revision ID: 0002_site_settings
Revises: 5e8578a7fb32
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0002_site_settings'
down_revision: Union[str, None] = '5e8578a7fb32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'site_settings',
        sa.Column('phone', sa.String(length=32), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('working_hours', sa.String(length=255), nullable=True),
        sa.Column('facebook_url', sa.String(length=500), nullable=True),
        sa.Column('instagram_url', sa.String(length=500), nullable=True),
        sa.Column('whatsapp_number', sa.String(length=32), nullable=True),
        sa.Column('contact_note', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('site_settings')
