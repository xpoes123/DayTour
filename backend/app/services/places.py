"""Google Places client with Redis-backed caching and daily budget cap.

All external Places calls flow through this module so we can:
- Cache results (24h) keyed by request parameters → cuts API spend
- Enforce a daily call budget (`GOOGLE_PLACES_DAILY_CAP`)
- Centralize error handling and field-mask discipline
"""

import hashlib
import json
import logging
from datetime import date
from typing import Any

import httpx
import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_CACHE_TTL = 60 * 60 * 24  # 24h
_settings = get_settings()


class PlacesBudgetExceeded(Exception):
    pass


def _cache_key(method: str, payload: dict[str, Any]) -> str:
    h = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    return f"places:{method}:{h}"


def _budget_key() -> str:
    return f"places:budget:{date.today().isoformat()}"


def _redis() -> redis.Redis:
    return redis.from_url(_settings.redis_url, decode_responses=True)


async def _check_and_increment_budget() -> None:
    r = _redis()
    key = _budget_key()
    n = await r.incr(key)
    if n == 1:
        await r.expire(key, 60 * 60 * 36)
    if n > _settings.google_places_daily_cap:
        raise PlacesBudgetExceeded(
            f"Daily Google Places cap ({_settings.google_places_daily_cap}) reached"
        )


async def _cached_or_call(
    method: str, payload: dict[str, Any], fetcher
) -> Any:
    r = _redis()
    key = _cache_key(method, payload)
    cached = await r.get(key)
    if cached:
        return json.loads(cached)
    await _check_and_increment_budget()
    result = await fetcher()
    await r.set(key, json.dumps(result), ex=_CACHE_TTL)
    return result


async def search_text(text_query: str) -> dict[str, Any] | None:
    """Return {place_id, name, lat, lon} for the best match, or None."""

    async def fetch():
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "X-Goog-Api-Key": _settings.google_places_api_key,
            "X-Goog-FieldMask": "places.displayName,places.id,places.location",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, headers=headers, json={"textQuery": text_query})
            resp.raise_for_status()
            data = resp.json()
        if not data.get("places"):
            return None
        p = data["places"][0]
        return {
            "place_id": p["id"],
            "name": p["displayName"]["text"],
            "lat": p["location"]["latitude"],
            "lon": p["location"]["longitude"],
        }

    return await _cached_or_call("searchText", {"q": text_query}, fetch)


async def nearby_attractions(
    lat: float, lon: float, radius_m: int, max_results: int = 10
) -> list[dict[str, Any]]:
    """Return up to `max_results` tourist attractions in the circle."""

    payload = {"lat": lat, "lon": lon, "radius": radius_m, "n": max_results}

    async def fetch():
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "X-Goog-Api-Key": _settings.google_places_api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.photos,places.rating",
            "Content-Type": "application/json",
        }
        body = {
            "includedTypes": ["tourist_attraction"],
            "maxResultCount": max_results,
            "locationRestriction": {
                "circle": {"center": {"latitude": lat, "longitude": lon}, "radius": radius_m}
            },
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        out = []
        for p in data.get("places", []):
            out.append({
                "place_id": p["id"],
                "name": p["displayName"]["text"],
                "lat": p["location"]["latitude"],
                "lon": p["location"]["longitude"],
                "rating": p.get("rating"),
            })
        return out

    return await _cached_or_call("searchNearby", payload, fetch)
