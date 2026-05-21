"""Hourly + daily forecast for a (lat, lon, date).

Backed by Open-Meteo's free, no-key API. We return a compact daily summary
plus per-hour conditions for the requested date so the frontend can:

- show "63° / 48° · Partly cloudy · 10% rain" near the schedule
- annotate each stop with the temp + icon at its arrival time

Cached in Redis for 30 minutes — forecasts shift on a half-hour-ish cadence
and we don't want to spam the upstream when many users hit the same trip.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date as date_cls
from typing import Any

import httpx
import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_CACHE_TTL = 30 * 60  # 30 minutes


# WMO weather-code → (label, emoji). Trimmed buckets.
_WMO: dict[int, tuple[str, str]] = {
    0: ("Clear", "☀️"),
    1: ("Mostly clear", "🌤"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫"),
    48: ("Fog", "🌫"),
    51: ("Drizzle", "🌦"),
    53: ("Drizzle", "🌦"),
    55: ("Drizzle", "🌦"),
    56: ("Freezing drizzle", "🌧"),
    57: ("Freezing drizzle", "🌧"),
    61: ("Light rain", "🌧"),
    63: ("Rain", "🌧"),
    65: ("Heavy rain", "🌧"),
    66: ("Freezing rain", "🌧"),
    67: ("Freezing rain", "🌧"),
    71: ("Light snow", "🌨"),
    73: ("Snow", "🌨"),
    75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "🌨"),
    80: ("Rain showers", "🌦"),
    81: ("Rain showers", "🌦"),
    82: ("Heavy showers", "⛈"),
    85: ("Snow showers", "🌨"),
    86: ("Snow showers", "🌨"),
    95: ("Thunderstorm", "⛈"),
    96: ("Thunderstorm w/ hail", "⛈"),
    99: ("Thunderstorm w/ hail", "⛈"),
}


def _describe(code: int) -> tuple[str, str]:
    return _WMO.get(code, ("Unknown", "🌡"))


def _redis() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)


def _cache_key(lat: float, lon: float, day: str) -> str:
    h = hashlib.sha1(f"{lat:.3f},{lon:.3f},{day}".encode()).hexdigest()[:16]
    return f"weather:{h}"


async def forecast(
    lat: float, lon: float, day: date_cls
) -> dict[str, Any] | None:
    """Return a daily summary + 24 hourly entries for the given date.

    Shape::

        {
          "date": "2026-05-21",
          "high_c": 22.4, "low_c": 13.1, "high_f": 72, "low_f": 56,
          "code": 2, "label": "Partly cloudy", "icon": "⛅",
          "precip_chance": 18,                  # max % across the day
          "hourly": [
            {"hour": 0, "temp_c": 14.2, "temp_f": 58, "code": 2, "label": "...", "icon": "⛅", "precip_chance": 5},
            ...                                # 24 entries
          ],
        }

    Returns None on lookup failure so callers can render without weather.
    """
    day_s = day.isoformat()
    r = _redis()
    key = _cache_key(lat, lon, day_s)
    cached = await r.get(key)
    if cached:
        return json.loads(cached)

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation_probability,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
        "temperature_unit": "celsius",
        "timezone": "auto",
        "start_date": day_s,
        "end_date": day_s,
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast", params=params
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("open-meteo forecast failed for %s,%s %s: %s", lat, lon, day_s, e)
        return None

    daily = data.get("daily", {})
    if not daily.get("time"):
        return None

    high_c = float(daily["temperature_2m_max"][0])
    low_c = float(daily["temperature_2m_min"][0])
    day_code = int(daily["weather_code"][0])
    precip_max = daily.get("precipitation_probability_max") or [None]
    precip_chance = int(precip_max[0]) if precip_max[0] is not None else 0
    label, icon = _describe(day_code)

    hourly_block = data.get("hourly", {})
    times = hourly_block.get("time") or []
    temps = hourly_block.get("temperature_2m") or []
    codes = hourly_block.get("weather_code") or []
    precs = hourly_block.get("precipitation_probability") or []
    hourly: list[dict[str, Any]] = []
    for i in range(min(24, len(times))):
        # times like "2026-05-21T13:00" — take the hour from the ISO timestamp.
        hour = int(times[i].split("T", 1)[1][:2]) if "T" in times[i] else i
        c = float(temps[i]) if i < len(temps) else None
        wc = int(codes[i]) if i < len(codes) else 0
        h_label, h_icon = _describe(wc)
        hourly.append(
            {
                "hour": hour,
                "temp_c": c,
                "temp_f": round(c * 9 / 5 + 32) if c is not None else None,
                "code": wc,
                "label": h_label,
                "icon": h_icon,
                "precip_chance": int(precs[i]) if i < len(precs) and precs[i] is not None else 0,
            }
        )

    result = {
        "date": day_s,
        "high_c": round(high_c, 1),
        "low_c": round(low_c, 1),
        "high_f": round(high_c * 9 / 5 + 32),
        "low_f": round(low_c * 9 / 5 + 32),
        "code": day_code,
        "label": label,
        "icon": icon,
        "precip_chance": precip_chance,
        "hourly": hourly,
    }
    await r.set(key, json.dumps(result), ex=_CACHE_TTL)
    return result
