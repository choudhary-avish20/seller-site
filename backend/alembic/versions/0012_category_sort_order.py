"""Add sort_order to categories for manual top-level reordering

Revision ID: 0012_category_sort_order
Revises: 0011_out_for_delivery_status
Create Date: 2026-09-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0012_category_sort_order'
down_revision: Union[str, None] = '0011_out_for_delivery_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('categories', sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False))

    # Backfill existing top-level categories with a stable order matching the
    # alphabetical order they've always displayed in, so nothing visibly
    # reshuffles the moment this ships. Subcategories are left at the default
    # 0 — they're always sorted by name, sort_order is meaningless for them.
    # Gaps of 10 leave room to insert a category between two others later
    # without a bulk renumber.
    conn = op.get_bind()
    categories = sa.table(
        'categories',
        sa.column('id', sa.UUID()),
        sa.column('name', sa.String()),
        sa.column('parent_id', sa.UUID()),
        sa.column('sort_order', sa.Integer()),
    )
    roots = conn.execute(
        sa.select(categories.c.id)
        .where(categories.c.parent_id.is_(None))
        .order_by(categories.c.name)
    ).fetchall()
    for i, row in enumerate(roots):
        conn.execute(
            categories.update().where(categories.c.id == row.id).values(sort_order=i * 10)
        )


def downgrade() -> None:
    op.drop_column('categories', 'sort_order')
