"""place photos array + top_review

Revision ID: 0008_place_photos_review
Revises: 0007_place_opening_hours
Create Date: 2026-05-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_place_photos_review"
down_revision: Union[str, None] = "0007_place_opening_hours"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("places", sa.Column("photos", sa.JSON(), nullable=True))
    op.add_column("places", sa.Column("top_review", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("places", "top_review")
    op.drop_column("places", "photos")
