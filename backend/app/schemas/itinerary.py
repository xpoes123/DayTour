from datetime import date as date_cls
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field



TransitMode = Literal["walking", "driving", "bicycling", "transit"]
Vibe = Literal["foodie", "art", "family", "outdoors", "nightlife", "hidden_gems"]


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
    # Optional "HH:MM" 24h start time. Combined with date, lets the backend
    # filter out stops that would be closed at the position they'd be
    # visited (approximate — uses a per-mode constant for travel + dwell).
    start_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    # Optional vibe — changes the Google Places type pool we search for, and
    # also adjusts the LLM prompts so summaries / descriptions match the vibe.
    vibe: Vibe | None = None


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


class AddEventRequest(BaseModel):
    # External id (e.g. ticketmaster:abc123) for dedupe; auto-generated for
    # custom events from a stable hash of (name + venue + time).
    external_id: str | None = None
    name: str = Field(min_length=1, max_length=255)
    venue_name: str | None = None
    venue_address: str | None = None
    # For ticketed events we already know the exact lat/lon. For custom
    # events the user typed a venue and we resolve it via places.search_text.
    venue_lat: float | None = Field(default=None, ge=-90, le=90)
    venue_lon: float | None = Field(default=None, ge=-180, le=180)
    venue_query: str | None = None
    start_local: str | None = None
    url: str | None = None


TravelStepMode = Literal["walk", "bus", "subway", "rail"]


class TravelStep(BaseModel):
    mode: TravelStepMode
    duration_sec: int
    distance_m: int
    # e.g. "L", "M14" — the transit line short-name, when present
    label: str | None = None
    # [[lat, lon], ...] for the step's portion of the route. Empty when
    # backend was OSRM (no step-level granularity).
    geometry: list[list[float]] = []


class StopOut(BaseModel):
    position: int
    place_id: str
    name: str
    latitude: float | None
    longitude: float | None
    photo_url: str | None
    # Number of photos available via /api/places/{id}/photo?idx=N. Lets the
    # carousel know how many slides to render without fetching each one.
    photo_count: int = 1
    rating: float | None
    # Trimmed top-rated Google review snippet.
    top_review: str | None = None
    # AI-written one-sentence description, persisted on Place.
    description: str | None = None
    # Weekly opening hours from Google. Null if not available (some place
    # types just don't have hours, e.g. a generic plaza).
    opening_hours: list[dict] | None = None
    # User-authored note for this stop on this trip.
    notes: str | None = None
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
