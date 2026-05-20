"""Road-accurate routing via the public OSRM demo server.

Free, keyless, supports walking ('foot'), cycling ('bike'), and driving
('car'). Transit isn't a thing OSRM does — we fall back to a haversine
estimate for that mode (see app.services.routing.estimate_leg_minutes).

The public demo at router.project-osrm.org is fine for low-volume hobby
traffic but has no SLA. If we ever care about uptime, self-host OSRM.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_PROFILE: dict[str, str] = {
    "walking": "foot",
    "bicycling": "bike",
    "driving": "car",
}

_OSRM_BASE = "https://router.project-osrm.org"
_CACHE_TTL = 60 * 60 * 24 * 7  # 1 week — geometry is stable


def _redis() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)


def _cache_key(profile: str, coords: list[tuple[float, float]]) -> str:
    flat = ",".join(f"{lat:.5f}:{lon:.5f}" for lat, lon in coords)
    return f"osrm:{profile}:{flat}"


async def route(
    coords_lat_lon: list[tuple[float, float]], transit_mode: str
) -> dict[str, Any] | None:
    """Return per-leg durations/distances + geometry, or None if mode unsupported / lookup fails.

    Shape::

        {
            "legs": [{"duration_sec": int, "distance_m": int}, ...],   # len = N - 1
            "geometry": [[lat, lon], ...],                              # the route polyline
            "total_duration_sec": int,
            "total_distance_m": int,
        }
    """
    profile = _PROFILE.get(transit_mode)
    if profile is None or len(coords_lat_lon) < 2:
        return None

    cache_key = _cache_key(profile, coords_lat_lon)
    r = _redis()
    cached = await r.get(cache_key)
    if cached:
        return json.loads(cached)

    # OSRM wants lon,lat;lon,lat...
    coord_str = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coords_lat_lon)
    url = f"{_OSRM_BASE}/route/v1/{profile}/{coord_str}"
    params = {"overview": "full", "geometries": "geojson", "steps": "false"}

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("OSRM lookup failed: %s", e)
        return None

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    route_obj = data["routes"][0]
    legs = [
        {"duration_sec": int(leg["duration"]), "distance_m": int(leg["distance"])}
        for leg in route_obj.get("legs", [])
    ]
    geometry = [[lat, lon] for lon, lat in route_obj["geometry"]["coordinates"]]

    result = {
        "legs": legs,
        "geometry": geometry,
        "total_duration_sec": int(route_obj["duration"]),
        "total_distance_m": int(route_obj["distance"]),
    }
    await r.set(cache_key, json.dumps(result), ex=_CACHE_TTL)
    return result
