"""Add out_for_delivery order status

Revision ID: 0011_out_for_delivery
Revises: 0010_order_hide
Create Date: 2026-09-03

"""
from typing import Sequence, Union

revision: str = '0011_out_for_delivery_status'
down_revision: Union[str, None] = '0010_order_hide'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # orders.status has always been a plain sa.String(32) column (see
    # 0001_initial_schema.py) on both SQLite and Postgres — the Python-side
    # OrderStatus enum on the model is validated at the application layer only,
    # there is no native database ENUM type backing it. So a new Python-side
    # member (out_for_delivery) needs no DDL change at all: this migration only
    # exists to keep the alembic revision chain unbroken.
    pass


def downgrade() -> None:
    pass
