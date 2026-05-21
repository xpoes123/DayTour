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
            "X-Goog-FieldMask": (
                "places.displayName,places.id,places.location,places.photos,"
                "places.rating,places.regularOpeningHours.periods,"
                "places.reviews.text,places.reviews.rating"
            ),
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, headers=headers, json={"textQuery": text_query})
            resp.raise_for_status()
            data = resp.json()
        if not data.get("places"):
            return None
        p = data["places"][0]
        photos = p.get("photos") or []
        photo_names = [ph["name"] for ph in photos[:5]]
        hours = (p.get("regularOpeningHours") or {}).get("periods")
        top_review = None
        for rv in p.get("reviews") or []:
            t = ((rv.get("text") or {}).get("text") or "").strip()
            if t and len(t) >= 20 and (rv.get("rating") or 0) >= 4:
                if len(t) > 280:
                    top_review = t[:280].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
                else:
                    top_review = t
                break
        return {
            "place_id": p["id"],
            "name": p["displayName"]["text"],
            "lat": p["location"]["latitude"],
            "lon": p["location"]["longitude"],
            "rating": p.get("rating"),
            "photo_name": photo_names[0] if photo_names else None,
            "photos": photo_names,
            "top_review": top_review,
            "opening_hours": hours,
        }

    return await _cached_or_call("searchText", {"q": text_query}, fetch)


async def autocomplete(query: str, limit: int = 6) -> list[dict[str, str]]:
    """Suggest place predictions for a partial query.

    Returns a list of {place_id, label} where label is the primary text
    (e.g. "Wisconsin State Capitol") with secondary text (city / state)
    appended in parens when present.
    """
    payload = {"q": query, "n": limit}

    async def fetch():
        url = "https://places.googleapis.com/v1/places:autocomplete"
        headers = {
            "X-Goog-Api-Key": _settings.google_places_api_key,
            "Content-Type": "application/json",
        }
        body = {"input": query, "includeQueryPredictions": False}
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        out: list[dict[str, str]] = []
        for s in data.get("suggestions", [])[:limit]:
            p = s.get("placePrediction")
            if not p:
                continue
            primary = p.get("structuredFormat", {}).get("mainText", {}).get("text") or p.get(
                "text", {}
            ).get("text", "")
            secondary = p.get("structuredFormat", {}).get("secondaryText", {}).get("text", "")
            label = f"{primary} ({secondary})" if secondary else primary
            out.append({"place_id": p["placeId"], "label": label, "primary": primary})
        return out

    # Autocomplete is volatile per-keystroke — keep cache short.
    r = _redis()
    key = _cache_key("autocomplete", payload)
    cached = await r.get(key)
    if cached:
        return json.loads(cached)
    await _check_and_increment_budget()
    result = await fetch()
    await r.set(key, json.dumps(result), ex=60 * 60)  # 1h
    return result


async def nearby_restaurants(
    lat: float, lon: float, radius_m: int = 600, max_results: int = 4
) -> list[dict[str, Any]]:
    """Return up to `max_results` restaurants near a point."""

    payload = {"lat": lat, "lon": lon, "radius": radius_m, "n": max_results, "k": "rest"}

    async def fetch():
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "X-Goog-Api-Key": _settings.google_places_api_key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.location,places.photos,"
                "places.rating,places.priceLevel,places.formattedAddress"
            ),
            "Content-Type": "application/json",
        }
        body = {
            "includedTypes": ["restaurant"],
            "maxResultCount": max_results,
            "rankPreference": "DISTANCE",
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": radius_m,
                }
            },
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        out = []
        for p in data.get("places", []):
            photos = p.get("photos") or []
            out.append({
                "place_id": p["id"],
                "name": p["displayName"]["text"],
                "lat": p["location"]["latitude"],
                "lon": p["location"]["longitude"],
                "rating": p.get("rating"),
                "price_level": p.get("priceLevel"),
                "address": p.get("formattedAddress"),
                "photo_name": photos[0]["name"] if photos else None,
            })
        return out

    return await _cached_or_call("searchNearbyRest", payload, fetch)


# Per-vibe config for the Google Places nearby search. Each entry shapes the
# (includedTypes, excludedPrimaryTypes, excludedTypes) triplet so the type
# pool matches the user's intent for the trip.
_VIBE_TYPES: dict[str | None, dict[str, list[str]]] = {
    None: {
        "included": [
            "tourist_attraction", "museum", "art_gallery", "historical_landmark",
            "monument", "aquarium", "zoo", "observation_deck", "plaza", "sculpture",
        ],
        "excluded_primary": ["park", "garden", "playground", "dog_park"],
        "excluded": [
            "performing_arts_theater", "concert_hall", "movie_theater",
            "casino", "night_club", "bar",
        ],
    },
    "foodie": {
        "included": [
            "restaurant", "bakery", "cafe", "ice_cream_shop", "food_court",
            "market", "brewery", "winery", "bagel_shop", "coffee_shop",
        ],
        "excluded_primary": ["park", "garden", "playground", "dog_park"],
        "excluded": ["casino", "night_club"],
    },
    "art": {
        "included": [
            "museum", "art_gallery", "sculpture", "monument", "historical_landmark",
            "performing_arts_theater", "cultural_center", "observation_deck",
            "tourist_attraction",
        ],
        "excluded_primary": ["park", "garden", "playground", "dog_park"],
        "excluded": ["casino", "night_club", "bar"],
    },
    "family": {
        "included": [
            "zoo", "aquarium", "museum", "amusement_park", "park", "library",
            "sculpture", "observation_deck", "tourist_attraction", "bowling_alley",
            "ice_skating_rink",
        ],
        "excluded_primary": [],
        "excluded": ["casino", "night_club", "bar", "performing_arts_theater"],
    },
    "outdoors": {
        "included": [
            "park", "garden", "botanical_garden", "national_park", "state_park",
            "marina", "beach", "hiking_area", "picnic_ground",
            "plaza", "sculpture", "tourist_attraction",
        ],
        "excluded_primary": [],
        "excluded": [
            "casino", "night_club", "bar", "movie_theater",
            "performing_arts_theater", "shopping_mall",
        ],
    },
    "nightlife": {
        "included": [
            "bar", "night_club", "restaurant", "brewery", "winery",
            "performing_arts_theater", "casino", "comedy_club", "karaoke",
            "wine_bar", "pub",
        ],
        "excluded_primary": ["park", "garden", "playground", "dog_park"],
        "excluded": [],
    },
    "hidden_gems": {
        "included": [
            "art_gallery", "sculpture", "monument", "market", "cultural_center",
            "plaza", "museum", "tourist_attraction", "library",
        ],
        "excluded_primary": ["park", "garden", "playground", "dog_park", "parking_lot"],
        "excluded": ["casino", "night_club", "bar", "amusement_park"],
    },
}


def _vibe_config(vibe: str | None) -> dict[str, list[str]]:
    return _VIBE_TYPES.get(vibe) or _VIBE_TYPES[None]


async def nearby_attractions(
    lat: float,
    lon: float,
    radius_m: int,
    max_results: int = 10,
    vibe: str | None = None,
) -> list[dict[str, Any]]:
    """Return up to `max_results` attractions matching the vibe."""

    cfg = _vibe_config(vibe)
    payload = {
        "lat": lat,
        "lon": lon,
        "radius": radius_m,
        "n": max_results,
        "vibe": vibe or "default",
    }

    async def fetch():
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "X-Goog-Api-Key": _settings.google_places_api_key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.location,places.photos,"
                "places.rating,places.primaryType,places.types,"
                "places.regularOpeningHours.periods,"
                "places.reviews.text,places.reviews.rating"
            ),
            "Content-Type": "application/json",
        }
        body = {
            "includedTypes": cfg["included"],
            "excludedPrimaryTypes": cfg["excluded_primary"],
            "excludedTypes": cfg["excluded"],
            "maxResultCount": max(max_results, 15),
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
            photos = p.get("photos") or []
            photo_names = [ph["name"] for ph in photos[:5]]
            hours = (p.get("regularOpeningHours") or {}).get("periods")
            top_review = None
            for rv in p.get("reviews") or []:
                t = ((rv.get("text") or {}).get("text") or "").strip()
                if t and len(t) >= 20 and (rv.get("rating") or 0) >= 4:
                    # Trim to ~280 chars on a word boundary.
                    if len(t) > 280:
                        cut = t[:280].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
                        top_review = cut
                    else:
                        top_review = t
                    break
            out.append({
                "place_id": p["id"],
                "name": p["displayName"]["text"],
                "lat": p["location"]["latitude"],
                "lon": p["location"]["longitude"],
                "rating": p.get("rating"),
                "photo_name": photo_names[0] if photo_names else None,
                "photos": photo_names,
                "top_review": top_review,
                "primary_type": p.get("primaryType"),
                "types": p.get("types") or [],
                "opening_hours": hours,
            })
        return out[:max_results]

    return await _cached_or_call("searchNearby", payload, fetch)
