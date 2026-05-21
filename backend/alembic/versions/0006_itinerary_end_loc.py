"""itinerary end_loc column

Revision ID: 0006_itinerary_end_loc
Revises: 0005_share_token_widen
Create Date: 2026-05-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_itinerary_end_loc"
down_revision: Union[str, None] = "0005_share_token_widen"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("itineraries", sa.Column("end_loc", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("itineraries", "end_loc")
