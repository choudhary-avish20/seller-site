"""add category_requests

Revision ID: c2a1f3b5d8e9
Revises: b3c3de2baecd
Create Date: 2026-08-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c2a1f3b5d8e9'
down_revision: Union[str, None] = 'b3c3de2baecd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('category_requests',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='category_request_status'), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('requester_id', sa.UUID(), nullable=False),
        sa.Column('created_category_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_category_requests_slug'), 'category_requests', ['slug'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_category_requests_slug'), table_name='category_requests')
    op.drop_table('category_requests')
    # do not drop enum automatically for sqlite, but for postgres we could
    try:
        sa.Enum(name='category_request_status').drop(op.get_bind(), checkfirst=True)
    except Exception:
        pass
