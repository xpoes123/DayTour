from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TransitMode = Literal["walking", "driving", "bicycling", "transit"]


class PlanRequest(BaseModel):
    start_loc: str = Field(min_length=1, max_length=255)
    radius_m: int = Field(ge=200, le=50_000, default=4000)
    stop_count: int = Field(ge=2, le=10, default=5)
    transit_mode: TransitMode = "walking"


class FromPromptRequest(BaseModel):
    prompt: str = Field(min_length=4, max_length=500)


class PickRequest(BaseModel):
    selected_place_ids: list[str] = Field(min_length=2, max_length=11)


class StopOut(BaseModel):
    position: int
    place_id: str
    name: str
    latitude: float | None
    longitude: float | None
    photo_url: str | None
    rating: float | None
    # Estimated minutes to travel from the previous stop to this one
    # (null for the first stop). Rough — based on straight-line distance
    # with a 1.3x detour factor and mode-specific avg speeds.
    travel_minutes_from_prev: int | None = None


class ItineraryOut(BaseModel):
    id: int
    title: str | None
    start_loc: str
    radius_m: int
    transit_mode: TransitMode
    share_token: str | None
    created_at: datetime
    stops: list[StopOut]
    total_travel_minutes: int = 0
