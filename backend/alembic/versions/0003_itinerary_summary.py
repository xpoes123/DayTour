"""itinerary summary column

Revision ID: 0003_itinerary_summary
Revises: 0002_guest_itineraries
Create Date: 2026-05-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_itinerary_summary"
down_revision: Union[str, None] = "0002_guest_itineraries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("itineraries", sa.Column("summary", sa.String(length=2000), nullable=True))


def downgrade() -> None:
    op.drop_column("itineraries", "summary")
