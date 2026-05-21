"""Itinerary endpoints.

Guest mode: auth is optional. If a valid Bearer token is sent, the resulting
Itinerary is linked to that user; otherwise it's anonymous (user_id=NULL) and
addressable by id / share_token.
"""

import logging
import uuid
from typing import Annotated

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import optional_current_user
from app.db.session import get_db
from app.models import Itinerary, Place, Stop, User
from app.schemas.itinerary import (
    AlternativeOut,
    FromPromptRequest,
    ItineraryOut,
    PlanRequest,
    RecomputeRequest,
    RestaurantOut,
    StopOut,
    TravelStep,
)
from app.services import google_routes, llm, osrm, places, routing, weather

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


# WMO weather codes considered "actively wet" — we drop outdoor-ish stops
# when the forecast hits any of these AND precip_chance is meaningful, OR
# precip_chance is high regardless of code.
_WET_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}


# Rough total-time-per-stop (travel + dwell) used to estimate when each stop
# would be visited, so we can drop ones whose hours don't cover that window.
_PER_STOP_MINUTES = {
    "walking": 75,    # ~30 walk + ~45 dwell
    "bicycling": 60,  # ~15 ride + ~45 dwell
    "driving": 50,    # ~10 drive + ~40 dwell
    "transit": 75,    # ~30 ride/wait + ~45 dwell
}


def _estimate_visit_minute(start_time: str, position: int, transit_mode: str) -> int:
    """Estimate minutes-since-midnight a stop at given position would be visited."""
    h, m = (int(x) for x in start_time.split(":"))
    per_stop = _PER_STOP_MINUTES.get(transit_mode, 75)
    return h * 60 + m + position * per_stop


def _is_open_at(
    opening_hours: list | None, weekday: int, total_minutes: int
) -> bool:
    """Is the place open on this weekday at this minute-of-day?

    weekday: 0=Sunday..6=Saturday (Google's convention).
    """
    if not opening_hours:
        return True  # unknown → assume open so we don't unfairly cull
    for p in opening_hours:
        o = p.get("open") or {}
        c = p.get("close")
        if c is None:
            return True
        o_day = o.get("day")
        c_day = c.get("day")
        o_min = (o.get("hour") or 0) * 60 + (o.get("minute") or 0)
        c_min = (c.get("hour") or 0) * 60 + (c.get("minute") or 0)
        if o_day == weekday and c_day == weekday and o_min <= total_minutes < c_min:
            return True
        # Period crossing midnight, started today.
        if o_day == weekday and c_day != weekday and total_minutes >= o_min:
            return True
        # Period crossing midnight, started yesterday into today.
        if c_day == weekday and o_day == (weekday - 1) % 7 and total_minutes < c_min:
            return True
    return False


def _open_on_day(opening_hours: list | None, weekday: int) -> bool:
    """Is the place open at any point on this weekday?

    weekday: 0=Sunday..6=Saturday (matches Google's convention).
    Returns True when we have no hours data (assume open) so places without
    coverage aren't unfairly culled.
    """
    if not opening_hours:
        return True
    for p in opening_hours:
        o = p.get("open") or {}
        c = p.get("close")
        if o.get("day") == weekday:
            return True
        # Period crossing midnight that started yesterday into today.
        if c and c.get("day") == weekday and o.get("day") == (weekday - 1) % 7:
            return True
        # Always-open (no close) entry.
        if c is None:
            return True
    return False

# Place types that make a stop unpleasant in the rain (best-effort by name).
_OUTDOOR_TYPES = {
    "park",
    "garden",
    "botanical_garden",
    "national_park",
    "state_park",
    "beach",
    "scenic_lookout",
    "hiking_area",
    "picnic_ground",
    "campground",
    "playground",
    "dog_park",
    "zoo",  # outdoor zoo
    "amusement_park",
}

# Subtle name signals — used as a secondary filter since Google's types
# don't always tag "Point" / "Trail" / "Cove" places as park-family.
_OUTDOOR_NAME_KEYWORDS = (
    "point",
    " trail",
    "trailhead",
    " cove",
    " beach",
    "lookout",
    "overlook",
    " preserve",
    "nature reserve",
)


def _looks_outdoor(candidate: dict) -> bool:
    types = set(candidate.get("types") or [])
    if types & _OUTDOOR_TYPES:
        return True
    if candidate.get("primary_type") in _OUTDOOR_TYPES:
        return True
    n = (candidate.get("name") or "").lower()
    return any(kw in n for kw in _OUTDOOR_NAME_KEYWORDS)


def _is_rainy(forecast_data: dict | None) -> bool:
    if not forecast_data:
        return False
    code = forecast_data.get("code")
    precip = forecast_data.get("precip_chance") or 0
    if precip >= 50:
        return True
    if code in _WET_CODES and precip >= 30:
        return True
    return False


def _photo_url(place: Place) -> str | None:
    """Turn a stored photo-resource-name into the proxy URL the frontend hits."""
    return f"/api/places/{place.google_place_id}/photo" if place.photo_url else None


async def _upsert_place(db: AsyncSession, data: dict) -> Place:
    existing = (
        await db.execute(select(Place).where(Place.google_place_id == data["place_id"]))
    ).scalar_one_or_none()
    if existing:
        existing.num_visits += 1
        if not existing.photo_url and data.get("photo_name"):
            existing.photo_url = data["photo_name"]
        if not existing.opening_hours and data.get("opening_hours"):
            existing.opening_hours = data["opening_hours"]
        return existing
    p = Place(
        google_place_id=data["place_id"],
        name=data["name"],
        latitude=data.get("lat"),
        longitude=data.get("lon"),
        rating=data.get("rating"),
        # photo_url stores the Google photo resource name (e.g.
        # 'places/CHIJ.../photos/Ab43m-...'); the frontend hits our
        # /places/{place_id}/photo proxy to materialize it as bytes.
        photo_url=data.get("photo_name"),
        opening_hours=data.get("opening_hours"),
        num_visits=1,
    )
    db.add(p)
    await db.flush()
    return p


async def _to_out(
    itinerary: Itinerary,
    stops_with_places: list[tuple[Stop, Place]],
    db: AsyncSession | None = None,
    generate_summary: bool = False,
) -> ItineraryOut:
    ordered = sorted(stops_with_places, key=lambda sp: sp[0].position)
    mode = itinerary.transit_mode

    coords: list[tuple[float, float]] = [
        (p.latitude, p.longitude)
        for _, p in ordered
        if p.latitude is not None and p.longitude is not None
    ]

    # Pick the right routing backend. Transit needs Google (real bus/rail
    # schedules); OSRM has no transit data. Walking / cycling / driving go
    # through OSRM, falling back to Google if OSRM fails for any reason.
    routing_result: dict | None = None
    if len(coords) >= 2:
        if mode == "transit":
            routing_result = await google_routes.route(coords, mode)
        else:
            routing_result = await osrm.route(coords, mode)
        if routing_result is None:
            routing_result = await google_routes.route(coords, mode)
    route_legs = routing_result["legs"] if routing_result else None
    geometry = routing_result["geometry"] if routing_result else None

    out_stops: list[StopOut] = []
    total = 0
    leg_idx = 0  # index into route_legs (one fewer than stops)
    prev_pt: routing.GeoPoint | None = None
    for stop_row, place in ordered:
        leg_minutes: int | None = None
        leg_meters: int | None = None
        steps: list[TravelStep] = []
        has_coords = place.latitude is not None and place.longitude is not None

        if prev_pt is not None and has_coords:
            if route_legs is not None and leg_idx < len(route_legs):
                leg = route_legs[leg_idx]
                leg_minutes = max(1, round(leg["duration_sec"] / 60))
                leg_meters = leg.get("distance_m")
                steps = [TravelStep(**s) for s in leg.get("steps", [])]
                leg_idx += 1
            else:
                here = routing.GeoPoint(
                    place_id=place.google_place_id,
                    lat=place.latitude,
                    lon=place.longitude,
                )
                leg_minutes = routing.estimate_leg_minutes(prev_pt, here, mode)
            total += leg_minutes

        if has_coords:
            prev_pt = routing.GeoPoint(
                place_id=place.google_place_id,
                lat=place.latitude,
                lon=place.longitude,
            )

        out_stops.append(
            StopOut(
                position=stop_row.position,
                place_id=place.google_place_id,
                name=place.name,
                latitude=place.latitude,
                longitude=place.longitude,
                photo_url=_photo_url(place),
                rating=place.rating,
                description=place.description,
                opening_hours=place.opening_hours,
                travel_minutes_from_prev=leg_minutes,
                travel_meters_from_prev=leg_meters,
                travel_steps_from_prev=steps,
            )
        )

    # Lazy AI fill: per-place descriptions only. Summary moved behind an
    # explicit button (see POST /itineraries/{id}/summarize) so we don't burn
    # tokens on every page view. Descriptions are per-place and cached
    # across trips, so they're effectively free after the first time we see
    # any given Place.
    if generate_summary and db is not None:
        needs_desc = [(s, p) for s, p in ordered if not p.description]
        if needs_desc:
            try:
                items = [
                    {"name": p.name, "context": itinerary.start_loc} for _, p in needs_desc
                ]
                descs = await llm.describe_places(items)
                for (_, p), d in zip(needs_desc, descs):
                    if d:
                        p.description = d.strip()
            except Exception as e:
                logger.warning(
                    "describe_places failed for itinerary %s: %s", itinerary.id, e
                )
            try:
                await db.commit()
            except Exception as e:
                logger.warning("commit failed: %s", e)

    return ItineraryOut(
        id=itinerary.id,
        title=itinerary.title,
        start_loc=itinerary.start_loc,
        end_loc=itinerary.end_loc,
        radius_m=itinerary.radius_m,
        transit_mode=mode,  # type: ignore[arg-type]
        share_token=itinerary.share_token,
        created_at=itinerary.created_at,
        stops=out_stops,
        total_travel_minutes=total,
        route_geometry=geometry,
        summary=itinerary.summary,
    )


@router.post("", response_model=ItineraryOut, status_code=201)
async def create_itinerary(
    body: PlanRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(optional_current_user)] = None,
):
    start = await places.search_text(body.start_loc)
    if not start:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Start location not found")

    end = None
    if body.end_loc and body.end_loc.strip():
        end = await places.search_text(body.end_loc)
        if not end:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "End location not found")
        if end["place_id"] == start["place_id"]:
            end = None  # same point as start → fall back to loop behavior

    # If the user named a date and the forecast looks wet, pull a wider pool
    # so we have room to drop outdoor-ish stops without ending up too short.
    rainy = False
    if body.date is not None:
        forecast = await weather.forecast(start["lat"], start["lon"], body.date)
        rainy = _is_rainy(forecast)

    pool_size = body.stop_count if not rainy else max(body.stop_count * 2, 15)
    nearby = await places.nearby_attractions(
        start["lat"], start["lon"], body.radius_m, max_results=pool_size
    )
    if not nearby:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No attractions found near that location")

    if rainy:
        indoor = [c for c in nearby if not _looks_outdoor(c)]
        if indoor:
            nearby = indoor
        # else: leave nearby alone — outdoor-heavy plan beats a 404

    # If a date was given, drop candidates that are closed all day. Skip
    # places with no opening_hours info (assume they're always-on attractions
    # like Picnic Point so we don't cull them by accident).
    if body.date is not None:
        weekday_google = (body.date.weekday() + 1) % 7  # Python Mon=0 → Google Sun=0
        open_today = [c for c in nearby if _open_on_day(c.get("opening_hours"), weekday_google)]
        if open_today:
            nearby = open_today

    nearby = nearby[: body.stop_count]

    itinerary = Itinerary(
        user_id=user.id if user else None,
        start_loc=body.start_loc,
        end_loc=body.end_loc if end else None,
        radius_m=body.radius_m,
        transit_mode=body.transit_mode,
        share_token=uuid.uuid4().hex,
    )
    db.add(itinerary)
    await db.flush()

    # Deduplicate by place_id, then place start first and (if present) end
    # last so routing.best_path with fix_end keeps them as the bookends.
    seen_ids: set[str] = set()
    candidates: list[dict] = []
    middle: list[dict] = []
    for c in [start, *nearby]:
        if c["place_id"] in seen_ids:
            continue
        if end and c["place_id"] == end["place_id"]:
            continue
        seen_ids.add(c["place_id"])
        if c["place_id"] == start["place_id"]:
            candidates.append(c)
        else:
            middle.append(c)
    candidates.extend(middle)
    if end:
        candidates.append(end)
        seen_ids.add(end["place_id"])

    geo_points = [
        routing.GeoPoint(place_id=c["place_id"], lat=c["lat"], lon=c["lon"]) for c in candidates
    ]
    ordered_ids = routing.best_path(geo_points, fix_end=end is not None)
    # When looping (no fixed end), strip the duplicate loop-close anchor.
    ordered_ids_unique = (
        ordered_ids[:-1] if ordered_ids[0] == ordered_ids[-1] else ordered_ids
    )
    by_id = {c["place_id"]: c for c in candidates}

    # Position-aware open-hours filter. Walk in 2-opt order, estimate when
    # each stop would be visited based on its index, drop ones whose open
    # hours don't cover that minute. Skip the start (always kept) and the
    # end_loc (already user-chosen). One-pass: dropping a stop shifts later
    # stops forward into possibly-open slots, but we don't re-route.
    if body.date is not None and body.start_time:
        weekday_google = (body.date.weekday() + 1) % 7  # Mon=0 → Sun=0
        kept_ordered: list[str] = []
        for i, pid in enumerate(ordered_ids_unique):
            data = by_id.get(pid) or {}
            # Always keep position 0 (start) and the explicit end if any.
            is_anchor = i == 0 or (end is not None and pid == end["place_id"])
            if is_anchor:
                kept_ordered.append(pid)
                continue
            mins = _estimate_visit_minute(body.start_time, len(kept_ordered), body.transit_mode)
            # Roll over to the next day if we run past midnight.
            day_offset, mins = divmod(mins, 24 * 60)
            wd = (weekday_google + day_offset) % 7
            if _is_open_at(data.get("opening_hours"), wd, mins):
                kept_ordered.append(pid)
        if len(kept_ordered) >= 2:
            ordered_ids_unique = kept_ordered

    stops_with_places: list[tuple[Stop, Place]] = []
    for position, pid in enumerate(ordered_ids_unique):
        place_row = await _upsert_place(db, by_id[pid])
        stop = Stop(itinerary_id=itinerary.id, place_id=place_row.id, position=position)
        db.add(stop)
        stops_with_places.append((stop, place_row))

    await db.commit()
    return await _to_out(itinerary, stops_with_places)


@router.post("/from-prompt", response_model=ItineraryOut, status_code=201)
async def create_from_prompt(
    body: FromPromptRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(optional_current_user)] = None,
):
    try:
        plan = await llm.prompt_to_plan(body.prompt)
        parsed = PlanRequest(**plan)
    except Exception as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Could not parse prompt: {e}")
    return await create_itinerary(parsed, db, user)


@router.get("/by-share/{token}", response_model=ItineraryOut)
async def get_by_share(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Public read-only fetch by share_token — no auth needed."""
    itin = (
        await db.execute(select(Itinerary).where(Itinerary.share_token == token))
    ).scalar_one_or_none()
    if not itin:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    stops = (
        await db.execute(select(Stop).where(Stop.itinerary_id == itin.id))
    ).scalars().all()
    place_rows = (
        await db.execute(select(Place).where(Place.id.in_([s.place_id for s in stops])))
    ).scalars().all()
    by_id = {p.id: p for p in place_rows}
    return await _to_out(
        itin, [(s, by_id[s.place_id]) for s in stops], db=db, generate_summary=True
    )


@router.get("/{itinerary_id}", response_model=ItineraryOut)
async def get_itinerary(
    itinerary_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    itin = (
        await db.execute(select(Itinerary).where(Itinerary.id == itinerary_id))
    ).scalar_one_or_none()
    if not itin:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    stops = (
        await db.execute(select(Stop).where(Stop.itinerary_id == itin.id))
    ).scalars().all()
    place_rows = (
        await db.execute(select(Place).where(Place.id.in_([s.place_id for s in stops])))
    ).scalars().all()
    by_id = {p.id: p for p in place_rows}
    return await _to_out(
        itin, [(s, by_id[s.place_id]) for s in stops], db=db, generate_summary=True
    )


@router.post("/{itinerary_id}/summarize")
async def summarize(
    itinerary_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Generate (or return cached) AI summary for an itinerary.

    Returns { "summary": str }. Persisted on Itinerary.summary so subsequent
    GETs include it without re-billing the model.
    """
    itin = (
        await db.execute(select(Itinerary).where(Itinerary.id == itinerary_id))
    ).scalar_one_or_none()
    if not itin:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if itin.summary:
        return {"summary": itin.summary}

    stops = (
        await db.execute(select(Stop).where(Stop.itinerary_id == itin.id).order_by(Stop.position))
    ).scalars().all()
    place_rows = (
        await db.execute(select(Place).where(Place.id.in_([s.place_id for s in stops])))
    ).scalars().all()
    by_id = {p.id: p for p in place_rows}
    names = [by_id[s.place_id].name for s in stops]
    if not names:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Itinerary has no stops")

    try:
        text = await llm.summarize_itinerary(names, itin.start_loc, itin.transit_mode)
    except Exception as e:
        logger.warning("summarize_itinerary failed for %s: %s", itin.id, e)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Could not generate summary")
    if not text:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Empty summary from model")

    itin.summary = text
    await db.commit()
    return {"summary": text}


@router.get("/{itinerary_id}/stops/{place_id}/restaurants", response_model=list[RestaurantOut])
async def stop_restaurants(
    itinerary_id: int,
    place_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 4,
):
    """Nearby restaurants around a specific stop on the itinerary."""
    # itinerary_id is in the path mostly for hygiene; we just look up the Place.
    place = (
        await db.execute(select(Place).where(Place.google_place_id == place_id))
    ).scalar_one_or_none()
    if not place or place.latitude is None or place.longitude is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "stop not found")
    raw = await places.nearby_restaurants(
        place.latitude, place.longitude, radius_m=600, max_results=limit
    )
    out: list[RestaurantOut] = []
    for c in raw:
        # Persist into the places table so the photo proxy works the same way.
        p = await _upsert_place(db, c)
        out.append(
            RestaurantOut(
                place_id=p.google_place_id,
                name=p.name,
                rating=p.rating,
                price_level=c.get("price_level"),
                address=c.get("address"),
                photo_url=_photo_url(p),
            )
        )
    await db.commit()
    return out


@router.get("/{itinerary_id}/alternatives", response_model=list[AlternativeOut])
async def alternatives(
    itinerary_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 8,
):
    """Suggest other tourist attractions in the itinerary's radius for swaps.

    Re-runs Google Places nearby search anchored at the original start_loc,
    excludes already-used place_ids, persists each candidate to the places
    table so the user can pick them in /recompute.
    """
    itin = (
        await db.execute(select(Itinerary).where(Itinerary.id == itinerary_id))
    ).scalar_one_or_none()
    if not itin:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    start = await places.search_text(itin.start_loc)
    if not start:
        return []
    nearby = await places.nearby_attractions(
        start["lat"], start["lon"], itin.radius_m, max_results=max(limit + 6, 12)
    )

    existing_stops = (
        await db.execute(select(Stop).where(Stop.itinerary_id == itin.id))
    ).scalars().all()
    place_rows = (
        await db.execute(select(Place).where(Place.id.in_([s.place_id for s in existing_stops])))
    ).scalars().all()
    existing_google_ids = {p.google_place_id for p in place_rows} | {start["place_id"]}

    out: list[AlternativeOut] = []
    for c in nearby:
        if c["place_id"] in existing_google_ids:
            continue
        place = await _upsert_place(db, c)
        out.append(
            AlternativeOut(
                place_id=place.google_place_id,
                name=place.name,
                latitude=place.latitude,
                longitude=place.longitude,
                photo_url=_photo_url(place),
                rating=place.rating,
            )
        )
        if len(out) >= limit:
            break

    await db.commit()
    return out


@router.post("/{itinerary_id}/recompute", response_model=ItineraryOut)
async def recompute(
    itinerary_id: int,
    body: RecomputeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Rebuild the itinerary's stops as the given place_ids, re-route.

    The kept_place_ids can be the original stops minus rejections, plus any
    alternative place_ids the user picked. All must exist in the places
    table (the /alternatives endpoint persists them on the way out).
    """
    itin = (
        await db.execute(select(Itinerary).where(Itinerary.id == itinerary_id))
    ).scalar_one_or_none()
    if not itin:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    # Resolve every requested place_id against the places table.
    found_rows = (
        await db.execute(select(Place).where(Place.google_place_id.in_(body.kept_place_ids)))
    ).scalars().all()
    place_by_google = {p.google_place_id: p for p in found_rows}
    kept = [pid for pid in body.kept_place_ids if pid in place_by_google]
    if len(kept) < 2:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Keep at least 2 known places — call /alternatives first for new ones.",
        )

    kept_places = [place_by_google[pid] for pid in kept]
    geo_points = [
        routing.GeoPoint(place_id=p.google_place_id, lat=p.latitude, lon=p.longitude)
        for p in kept_places
        if p.latitude is not None and p.longitude is not None
    ]
    if len(geo_points) < 2:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Kept stops are missing coordinates — can't recompute.",
        )
    ordered_ids = routing.best_path(geo_points)
    ordered_unique = ordered_ids[:-1] if ordered_ids[0] == ordered_ids[-1] else ordered_ids

    # Replace the itinerary's stop set with the kept-and-reordered subset.
    existing_stops = (
        await db.execute(select(Stop).where(Stop.itinerary_id == itin.id))
    ).scalars().all()
    for s in existing_stops:
        await db.delete(s)
    await db.flush()

    new_stops_with_places: list[tuple[Stop, Place]] = []
    for pos, pid in enumerate(ordered_unique):
        p = place_by_google[pid]
        stop = Stop(itinerary_id=itin.id, place_id=p.id, position=pos)
        db.add(stop)
        new_stops_with_places.append((stop, p))

    await db.commit()
    return await _to_out(itin, new_stops_with_places)
