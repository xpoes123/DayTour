"""Google Routes API for real transit (bus / subway / rail) routing.

OSRM has no transit data — for transit mode we hit Google's Routes API which
returns actual schedule-aware durations and the chained leg geometry. Falls
back gracefully (returns None) if the key/permission is missing so callers
can fall through to a haversine estimate.

Pricing: ~$5 per 1000 requests for basic compute mode. Cached in Redis 6h.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import httpx
import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
_FIELD_MASK = (
    "routes.duration,routes.distanceMeters,"
    "routes.polyline.geoJsonLinestring,"
    "routes.legs.duration,routes.legs.distanceMeters"
)
_CACHE_TTL = 60 * 60 * 6  # 6h — transit schedules drift


def _redis() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)


def _cache_key(mode: str, coords: list[tuple[float, float]]) -> str:
    flat = ",".join(f"{lat:.5f}:{lon:.5f}" for lat, lon in coords)
    return "google_routes:" + hashlib.sha1(f"{mode}|{flat}".encode()).hexdigest()[:24]


def _waypoint(lat: float, lon: float) -> dict:
    return {"location": {"latLng": {"latitude": lat, "longitude": lon}}}


def _seconds_from_duration(s: str | int | float) -> int:
    """Routes API returns duration as e.g. '320s'. Sometimes int/float too."""
    if isinstance(s, (int, float)):
        return int(s)
    s = str(s).strip()
    if s.endswith("s"):
        s = s[:-1]
    try:
        return int(float(s))
    except ValueError:
        return 0


async def route(
    coords_lat_lon: list[tuple[float, float]], transit_mode: str
) -> dict[str, Any] | None:
    """Return {legs, geometry, total_*} via Google Routes, or None on failure."""
    settings = get_settings()
    api_key = settings.google_places_api_key
    if not api_key or len(coords_lat_lon) < 2:
        return None

    travel_mode = {
        "walking": "WALK",
        "bicycling": "BICYCLE",
        "driving": "DRIVE",
        "transit": "TRANSIT",
    }.get(transit_mode)
    if travel_mode is None:
        return None

    r = _redis()
    key = _cache_key(transit_mode, coords_lat_lon)
    cached = await r.get(key)
    if cached:
        return json.loads(cached)

    origin = _waypoint(*coords_lat_lon[0])
    destination = _waypoint(*coords_lat_lon[-1])
    intermediates = [_waypoint(lat, lon) for lat, lon in coords_lat_lon[1:-1]]

    body: dict[str, Any] = {
        "origin": origin,
        "destination": destination,
        "travelMode": travel_mode,
        "polylineEncoding": "GEO_JSON_LINESTRING",
        "computeAlternativeRoutes": False,
    }
    if intermediates:
        body["intermediates"] = intermediates
    if travel_mode == "TRANSIT":
        body["transitPreferences"] = {
            "allowedTravelModes": ["BUS", "SUBWAY", "TRAIN", "LIGHT_RAIL", "RAIL"]
        }

    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": _FIELD_MASK,
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(_API_URL, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Google Routes API call failed: %s", e)
        return None

    routes = data.get("routes") or []
    if not routes:
        return None
    route_obj = routes[0]

    legs_raw = route_obj.get("legs") or []
    legs = [
        {
            "duration_sec": _seconds_from_duration(leg.get("duration", "0s")),
            "distance_m": int(leg.get("distanceMeters", 0)),
        }
        for leg in legs_raw
    ]
    ls = route_obj.get("polyline", {}).get("geoJsonLinestring", {})
    geometry = [[lat, lon] for lon, lat in (ls.get("coordinates") or [])]

    result = {
        "legs": legs,
        "geometry": geometry,
        "total_duration_sec": _seconds_from_duration(route_obj.get("duration", "0s")),
        "total_distance_m": int(route_obj.get("distanceMeters", 0)),
    }
    await r.set(key, json.dumps(result), ex=_CACHE_TTL)
    return result
