from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Place(Base):
    __tablename__ = "places"

    id: Mapped[int] = mapped_column(primary_key=True)
    google_place_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Full list of Google photo resource names. photo_url stays as the
    # first one for back-compat (it's referenced in indexes and shorthand
    # accesses); photos[] feeds the carousel.
    photos: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # One short top-review quote (already trimmed). Renders under the
    # stop name as social proof.
    top_review: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Google Places regularOpeningHours.periods: list of weekly periods,
    # each {open: {day, hour, minute}, close: {day, hour, minute}}.
    # day is 0=Sunday..6=Saturday per Google's convention.
    opening_hours: Mapped[list | None] = mapped_column(JSON, nullable=True)
    price_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_visits: Mapped[int] = mapped_column(Integer, default=0)
    refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
