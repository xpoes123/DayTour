from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Itinerary(Base):
    __tablename__ = "itineraries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_loc: Mapped[str] = mapped_column(String(255))
    radius_m: Mapped[int] = mapped_column(Integer)
    transit_mode: Mapped[str] = mapped_column(String(16), default="walking")
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    summary: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    stops: Mapped[list["Stop"]] = relationship(
        back_populates="itinerary",
        cascade="all, delete-orphan",
        order_by="Stop.position",
    )


class Stop(Base):
    __tablename__ = "stops"

    id: Mapped[int] = mapped_column(primary_key=True)
    itinerary_id: Mapped[int] = mapped_column(
        ForeignKey("itineraries.id", ondelete="CASCADE"), index=True
    )
    place_id: Mapped[int] = mapped_column(ForeignKey("places.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    dwell_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    itinerary: Mapped["Itinerary"] = relationship(back_populates="stops")


class Route(Base):
    """Cached 2-opt result keyed by hash of sorted stop place ids."""

    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    stop_set_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    ordered_place_ids: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
