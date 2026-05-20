"""Google Routes API for real transit (bus / subway / rail) routing.

OSRM has no transit data — for transit mode we hit Google's Routes API which
returns actual schedule-aware durations and the chained leg geometry. Falls
back gracefully (returns None) if the key/permission is missing so callers
can fall through to a haversine estimate.

Pricing: ~$5 per 1000 requests for basic compute mode. Cached in Redis 6h.
"""

from __future__ import annotations

import asyncio
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
    "routes.legs.duration,routes.legs.distanceMeters,"
    "routes.legs.steps.travelMode,"
    "routes.legs.steps.staticDuration,"
    "routes.legs.steps.distanceMeters,"
    "routes.legs.steps.transitDetails.transitLine.nameShort,"
    "routes.legs.steps.transitDetails.transitLine.name,"
    "routes.legs.steps.transitDetails.transitLine.vehicle.type"
)


def _parse_steps(leg_obj: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a Google Routes leg into [{mode, duration_sec, distance_m, label?}].

    mode is normalized to one of: 'walk', 'bus', 'subway', 'rail'.
    label, when present, is the line short-name (e.g. 'L', 'M14').
    """
    out: list[dict[str, Any]] = []
    for step in leg_obj.get("steps", []) or []:
        tm = step.get("travelMode")
        dur = _seconds_from_duration(step.get("staticDuration", "0s"))
        dist = int(step.get("distanceMeters", 0))
        if tm == "WALK":
            mode = "walk"
            label: str | None = None
        elif tm == "TRANSIT":
            td = (step.get("transitDetails") or {}).get("transitLine") or {}
            vtype = ((td.get("vehicle") or {}).get("type") or "").upper()
            if vtype in {"BUS", "TROLLEYBUS", "INTERCITY_BUS", "SHARE_TAXI"}:
                mode = "bus"
            elif vtype in {"SUBWAY", "METRO_RAIL", "MONORAIL", "HEAVY_RAIL"}:
                mode = "subway"
            elif vtype in {"RAIL", "COMMUTER_TRAIN", "HIGH_SPEED_TRAIN", "LONG_DISTANCE_TRAIN"}:
                mode = "rail"
            elif vtype in {"TRAM", "LIGHT_RAIL", "CABLE_CAR", "FUNICULAR", "GONDOLA_LIFT"}:
                mode = "rail"
            else:
                mode = "subway"
            label = td.get("nameShort") or td.get("name") or None
        else:
            continue
        out.append({"mode": mode, "duration_sec": dur, "distance_m": dist, "label": label})
    return out
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


_TRAVEL_MODE = {
    "walking": "WALK",
    "bicycling": "BICYCLE",
    "driving": "DRIVE",
    "transit": "TRANSIT",
}


async def _one_leg(
    client: httpx.AsyncClient,
    a: tuple[float, float],
    b: tuple[float, float],
    travel_mode: str,
    api_key: str,
) -> dict[str, Any] | None:
    """Fetch a single origin→destination route from Google."""
    body: dict[str, Any] = {
        "origin": _waypoint(*a),
        "destination": _waypoint(*b),
        "travelMode": travel_mode,
        "polylineEncoding": "GEO_JSON_LINESTRING",
        "computeAlternativeRoutes": False,
    }
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
        resp = await client.post(_API_URL, headers=headers, json=body)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Google Routes leg failed: %s", e)
        return None


async def route(
    coords_lat_lon: list[tuple[float, float]], transit_mode: str
) -> dict[str, Any] | None:
    """Return {legs, geometry, total_*} via Google Routes, or None on failure.

    TRANSIT mode requires one Google Routes call per leg (the API rejects
    intermediate waypoints for transit), so we fan out the legs in parallel.
    Non-transit modes do a single multi-stop call.
    """
    settings = get_settings()
    api_key = settings.google_places_api_key
    if not api_key or len(coords_lat_lon) < 2:
        return None
    travel_mode = _TRAVEL_MODE.get(transit_mode)
    if travel_mode is None:
        return None

    r = _redis()
    key = _cache_key(transit_mode, coords_lat_lon)
    cached = await r.get(key)
    if cached:
        return json.loads(cached)

    legs: list[dict[str, Any]] = []
    geometry: list[list[float]] = []
    total_duration = 0
    total_distance = 0

    async with httpx.AsyncClient(timeout=12) as client:
        if travel_mode == "TRANSIT":
            # Fan out one call per leg.
            pairs = list(zip(coords_lat_lon, coords_lat_lon[1:]))
            results = await asyncio.gather(
                *(_one_leg(client, a, b, travel_mode, api_key) for a, b in pairs)
            )
            for resp in results:
                if not resp:
                    return None
                routes = resp.get("routes") or []
                if not routes:
                    # Routes API can return 200 with empty routes when there's
                    # no transit option (e.g. very close stops). Treat as a
                    # zero-cost leg and keep the rest of the trip.
                    legs.append({"duration_sec": 0, "distance_m": 0})
                    continue
                ro = routes[0]
                dur = _seconds_from_duration(ro.get("duration", "0s"))
                dist = int(ro.get("distanceMeters", 0))
                # In a one-leg request the whole route is the leg.
                first_leg = (ro.get("legs") or [{}])[0]
                legs.append(
                    {
                        "duration_sec": dur,
                        "distance_m": dist,
                        "steps": _parse_steps(first_leg),
                    }
                )
                total_duration += dur
                total_distance += dist
                ls = ro.get("polyline", {}).get("geoJsonLinestring", {})
                geometry.extend([[lat, lon] for lon, lat in (ls.get("coordinates") or [])])
        else:
            # Single multi-stop call (intermediates are fine for non-transit).
            body: dict[str, Any] = {
                "origin": _waypoint(*coords_lat_lon[0]),
                "destination": _waypoint(*coords_lat_lon[-1]),
                "travelMode": travel_mode,
                "polylineEncoding": "GEO_JSON_LINESTRING",
                "computeAlternativeRoutes": False,
            }
            inter = [_waypoint(lat, lon) for lat, lon in coords_lat_lon[1:-1]]
            if inter:
                body["intermediates"] = inter
            headers = {
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": _FIELD_MASK,
                "Content-Type": "application/json",
            }
            try:
                resp = await client.post(_API_URL, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
            except (httpx.HTTPError, ValueError) as e:
                logger.warning("Google Routes API call failed: %s", e)
                return None
            routes = data.get("routes") or []
            if not routes:
                return None
            ro = routes[0]
            for leg in ro.get("legs") or []:
                legs.append(
                    {
                        "duration_sec": _seconds_from_duration(leg.get("duration", "0s")),
                        "distance_m": int(leg.get("distanceMeters", 0)),
                        "steps": _parse_steps(leg),
                    }
                )
            ls = ro.get("polyline", {}).get("geoJsonLinestring", {})
            geometry = [[lat, lon] for lon, lat in (ls.get("coordinates") or [])]
            total_duration = _seconds_from_duration(ro.get("duration", "0s"))
            total_distance = int(ro.get("distanceMeters", 0))

    result = {
        "legs": legs,
        "geometry": geometry,
        "total_duration_sec": total_duration,
        "total_distance_m": total_distance,
    }
    await r.set(key, json.dumps(result), ex=_CACHE_TTL)
    return result
