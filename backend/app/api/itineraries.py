"""Itinerary endpoints.

Guest mode: auth is optional. If a valid Bearer token is sent, the resulting
Itinerary is linked to that user; otherwise it's anonymous (user_id=NULL) and
addressable by id / share_token.
"""

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import optional_current_user
from app.db.session import get_db
from app.models import Itinerary, Place, Stop, User
from app.schemas.itinerary import (
    FromPromptRequest,
    ItineraryOut,
    PickRequest,
    PlanRequest,
    StopOut,
)
from app.services import llm, places, routing

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


async def _upsert_place(db: AsyncSession, data: dict) -> Place:
    existing = (
        await db.execute(select(Place).where(Place.google_place_id == data["place_id"]))
    ).scalar_one_or_none()
    if existing:
        existing.num_visits += 1
        return existing
    p = Place(
        google_place_id=data["place_id"],
        name=data["name"],
        latitude=data.get("lat"),
        longitude=data.get("lon"),
        rating=data.get("rating"),
        num_visits=1,
    )
    db.add(p)
    await db.flush()
    return p


def _to_out(itinerary: Itinerary, stops_with_places: list[tuple[Stop, Place]]) -> ItineraryOut:
    return ItineraryOut(
        id=itinerary.id,
        title=itinerary.title,
        start_loc=itinerary.start_loc,
        radius_m=itinerary.radius_m,
        transit_mode=itinerary.transit_mode,  # type: ignore[arg-type]
        share_token=itinerary.share_token,
        created_at=itinerary.created_at,
        stops=[
            StopOut(
                position=s.position,
                place_id=p.google_place_id,
                name=p.name,
                latitude=p.latitude,
                longitude=p.longitude,
                photo_url=p.photo_url,
                rating=p.rating,
            )
            for s, p in sorted(stops_with_places, key=lambda sp: sp[0].position)
        ],
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
    nearby = await places.nearby_attractions(
        start["lat"], start["lon"], body.radius_m, max_results=body.stop_count
    )
    if not nearby:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No attractions found near that location")

    itinerary = Itinerary(
        user_id=user.id if user else None,
        start_loc=body.start_loc,
        radius_m=body.radius_m,
        transit_mode=body.transit_mode,
        share_token=secrets.token_urlsafe(8),
    )
    db.add(itinerary)
    await db.flush()

    candidates = [start, *nearby]
    geo_points = [
        routing.GeoPoint(place_id=c["place_id"], lat=c["lat"], lon=c["lon"]) for c in candidates
    ]
    ordered_ids = routing.best_path(geo_points)
    # Drop the loop-close duplicate when persisting stops.
    ordered_ids_unique = ordered_ids[:-1] if ordered_ids[0] == ordered_ids[-1] else ordered_ids
    by_id = {c["place_id"]: c for c in candidates}

    stops_with_places: list[tuple[Stop, Place]] = []
    for position, pid in enumerate(ordered_ids_unique):
        place_row = await _upsert_place(db, by_id[pid])
        stop = Stop(itinerary_id=itinerary.id, place_id=place_row.id, position=position)
        db.add(stop)
        stops_with_places.append((stop, place_row))

    await db.commit()
    return _to_out(itinerary, stops_with_places)


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
    return _to_out(itin, [(s, by_id[s.place_id]) for s in stops])


@router.post("/{itinerary_id}/pick", response_model=ItineraryOut)
async def pick(
    itinerary_id: int,
    body: PickRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # TODO: replace existing stops with the user's selection, re-run routing
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Pick flow lands in phase 1.5")
