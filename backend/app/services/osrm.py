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

# The public OSRM demo only has the car profile loaded; foot/bike requests
# silently fall through to car routing (same distance + same car-speed duration).
# So we always request "car" (for the geometry + road distance), then compute
# our own per-mode duration from that distance using realistic urban speeds.
_OSRM_PROFILE = "car"

_OSRM_BASE = "https://router.project-osrm.org"
_CACHE_TTL = 60 * 60 * 24 * 7  # 1 week — geometry is stable

# Realistic urban speeds in km/h. Walking is on the slower side because
# tourists stop, wait at lights, take photos. Driving is below freeway because
# urban with signals.
_MODE_KMH: dict[str, float] = {
    "walking": 4.5,
    "bicycling": 14.0,
    "driving": 32.0,
}


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
    kmh = _MODE_KMH.get(transit_mode)
    if kmh is None or len(coords_lat_lon) < 2:
        return None

    # Cache keyed by mode (since the per-mode duration we compute differs)
    # even though OSRM is always queried with the car profile.
    cache_key = _cache_key(f"{_OSRM_PROFILE}-{transit_mode}", coords_lat_lon)
    r = _redis()
    cached = await r.get(cache_key)
    if cached:
        return json.loads(cached)

    # OSRM wants lon,lat;lon,lat...
    coord_str = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coords_lat_lon)
    url = f"{_OSRM_BASE}/route/v1/{_OSRM_PROFILE}/{coord_str}"
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
    # OSRM gives us road-following distance — accurate. Duration we discard
    # and recompute from distance at the mode's realistic speed.
    mps = kmh * 1000 / 3600
    legs = []
    for leg in route_obj.get("legs", []):
        dist_m = int(leg["distance"])
        legs.append(
            {
                "duration_sec": int(round(dist_m / mps)) if mps > 0 else 0,
                "distance_m": dist_m,
                # OSRM doesn't give us step granularity for our purposes;
                # the whole leg is one mode of the requested transit_mode.
                "steps": [],
            }
        )
    geometry = [[lat, lon] for lon, lat in route_obj["geometry"]["coordinates"]]
    total_distance = int(route_obj["distance"])

    result = {
        "legs": legs,
        "geometry": geometry,
        "total_duration_sec": int(round(total_distance / mps)) if mps > 0 else 0,
        "total_distance_m": total_distance,
    }
    await r.set(cache_key, json.dumps(result), ex=_CACHE_TTL)
    return result
