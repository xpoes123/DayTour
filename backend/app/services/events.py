"""Events feed (concerts / sports / theater / comedy) via Ticketmaster.

Discovery API docs: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/
Free tier is 5000 calls / day, plenty for our usage. When the key isn't set
we silently return an empty list so the frontend hides the panel — the rest
of the app works fine without it.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date as date_cls
from datetime import datetime, time, timedelta, timezone
from typing import Any

import httpx
import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
_CACHE_TTL = 30 * 60


def _redis() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)


def _cache_key(lat: float, lon: float, day: str) -> str:
    h = hashlib.sha1(f"{lat:.3f},{lon:.3f},{day}".encode()).hexdigest()[:16]
    return f"events:{h}"


async def for_date(
    lat: float,
    lon: float,
    day: date_cls,
    radius_km: int = 15,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """Return up to `limit` events near (lat, lon) on the given local date.

    Each entry:
      {id, name, url, image, start_local, venue_name, venue_lat, venue_lon,
       venue_address, genre}
    """
    s = get_settings()
    key = s.ticketmaster_api_key
    if not key:
        return []

    r = _redis()
    ck = _cache_key(lat, lon, day.isoformat())
    cached = await r.get(ck)
    if cached:
        return json.loads(cached)

    # Search window: the whole local day, encoded as UTC since Ticketmaster
    # expects ISO-8601 with a 'Z'. Imperfect for trips crossing time-zones,
    # but fine for the typical "same-city day trip" case.
    start_dt = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    params = {
        "latlong": f"{lat:.4f},{lon:.4f}",
        "radius": radius_km,
        "unit": "km",
        "startDateTime": start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endDateTime": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "size": limit,
        "sort": "relevance,desc",
        "apikey": key,
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://app.ticketmaster.com/discovery/v2/events.json",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("ticketmaster events lookup failed: %s", e)
        return []

    out: list[dict[str, Any]] = []
    for ev in (data.get("_embedded", {}) or {}).get("events", []):
        venues = (ev.get("_embedded") or {}).get("venues") or []
        if not venues:
            continue
        venue = venues[0]
        loc = venue.get("location") or {}
        if not loc.get("latitude") or not loc.get("longitude"):
            continue
        d = ev.get("dates", {}).get("start", {})
        local = d.get("localDate", "")
        if d.get("localTime"):
            local = f"{local}T{d['localTime']}"
        # Largest image we can fit comfortably as a card thumbnail.
        image: str | None = None
        for im in ev.get("images") or []:
            if im.get("ratio") in {"16_9", "3_2"} and (im.get("width") or 0) >= 600:
                image = im.get("url")
                break
        if not image and ev.get("images"):
            image = ev["images"][0].get("url")
        out.append(
            {
                "id": ev["id"],
                "name": ev["name"],
                "url": ev.get("url"),
                "image": image,
                "start_local": local,
                "venue_name": venue.get("name"),
                "venue_lat": float(loc["latitude"]),
                "venue_lon": float(loc["longitude"]),
                "venue_address": (venue.get("address") or {}).get("line1"),
                "genre": (
                    ((ev.get("classifications") or [{}])[0].get("genre") or {}).get("name")
                ),
            }
        )

    await r.set(ck, json.dumps(out), ex=_CACHE_TTL)
    return out
