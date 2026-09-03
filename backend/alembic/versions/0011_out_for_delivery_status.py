"""Add out_for_delivery order status

Revision ID: 0011_out_for_delivery
Revises: 0010_order_hide
Create Date: 2026-09-03

"""
from typing import Sequence, Union

from alembic import op

revision: str = '0011_out_for_delivery_status'
down_revision: Union[str, None] = '0010_order_hide'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # SQLite stores order status as a plain VARCHAR with no CHECK constraint,
        # so new Python-side enum members need no DDL there. Postgres uses a real
        # native ENUM type, which needs an explicit ALTER TYPE to accept the new
        # value; ADD VALUE cannot run inside the transaction Alembic normally
        # wraps a migration in, hence the autocommit block.
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'out_for_delivery'")


def downgrade() -> None:
    # Postgres does not support removing a value from an existing enum type;
    # downgrading this would require recreating the type, which is not worth
    # the risk for a purely additive status value.
    pass
