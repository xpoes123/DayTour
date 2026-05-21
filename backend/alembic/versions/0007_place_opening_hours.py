"""place opening_hours column

Revision ID: 0007_place_opening_hours
Revises: 0006_itinerary_end_loc
Create Date: 2026-05-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_place_opening_hours"
down_revision: Union[str, None] = "0006_itinerary_end_loc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("places", sa.Column("opening_hours", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("places", "opening_hours")
