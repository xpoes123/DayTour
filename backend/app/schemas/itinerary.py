from datetime import date as date_cls
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field



TransitMode = Literal["walking", "driving", "bicycling", "transit"]


class PlanRequest(BaseModel):
    start_loc: str = Field(min_length=1, max_length=255)
    # Optional explicit endpoint. When omitted, the trip loops back to start.
    end_loc: str | None = Field(default=None, max_length=255)
    radius_m: int = Field(ge=200, le=50_000, default=4000)
    stop_count: int = Field(ge=2, le=10, default=5)
    transit_mode: TransitMode = "walking"
    # Optional. If provided, backend looks up the forecast and culls
    # outdoor-ish places when rain is likely.
    date: date_cls | None = None


class FromPromptRequest(BaseModel):
    prompt: str = Field(min_length=4, max_length=500)


class RecomputeRequest(BaseModel):
    # Google place_ids for the final stop set. May include place_ids that
    # weren't part of the original itinerary as long as they exist in the
    # places table (typically populated via /alternatives first).
    kept_place_ids: list[str] = Field(min_length=2, max_length=12)


class AlternativeOut(BaseModel):
    place_id: str
    name: str
    latitude: float | None
    longitude: float | None
    photo_url: str | None
    rating: float | None


class RestaurantOut(BaseModel):
    place_id: str
    name: str
    rating: float | None
    price_level: str | None
    address: str | None
    photo_url: str | None


TravelStepMode = Literal["walk", "bus", "subway", "rail"]


class TravelStep(BaseModel):
    mode: TravelStepMode
    duration_sec: int
    distance_m: int
    # e.g. "L", "M14" — the transit line short-name, when present
    label: str | None = None


class StopOut(BaseModel):
    position: int
    place_id: str
    name: str
    latitude: float | None
    longitude: float | None
    photo_url: str | None
    rating: float | None
    # AI-written one-sentence description, persisted on Place.
    description: str | None = None
    # Weekly opening hours from Google. Null if not available (some place
    # types just don't have hours, e.g. a generic plaza).
    opening_hours: list[dict] | None = None
    # Minutes to travel from the previous stop to this one (null for first).
    travel_minutes_from_prev: int | None = None
    # Road-distance for that leg, in meters.
    travel_meters_from_prev: int | None = None
    # For transit legs: the step breakdown (walk → ride → walk). For other
    # modes this is an empty list; the whole leg is the chosen transit mode.
    travel_steps_from_prev: list[TravelStep] = []


class ItineraryOut(BaseModel):
    id: int
    title: str | None
    start_loc: str
    end_loc: str | None = None
    radius_m: int
    transit_mode: TransitMode
    share_token: str | None
    created_at: datetime
    stops: list[StopOut]
    total_travel_minutes: int = 0
    # [[lat, lon], ...] road-following polyline from OSRM, or null when the
    # transit mode isn't road-routable (e.g. transit) or OSRM failed.
    route_geometry: list[list[float]] | None = None
    # Claude-written preview paragraph; null while still generating or if
    # the model failed.
    summary: str | None = None
