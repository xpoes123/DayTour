"""guest itineraries: user_id nullable

Revision ID: 0002_guest_itineraries
Revises: caebaf8aaa2b
Create Date: 2026-05-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_guest_itineraries"
down_revision: Union[str, None] = "caebaf8aaa2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("itineraries", "user_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.alter_column("itineraries", "user_id", existing_type=sa.Integer(), nullable=False)
