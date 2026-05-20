"""place description column

Revision ID: 0004_place_description
Revises: 0003_itinerary_summary
Create Date: 2026-05-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_place_description"
down_revision: Union[str, None] = "0003_itinerary_summary"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("places", sa.Column("description", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("places", "description")
