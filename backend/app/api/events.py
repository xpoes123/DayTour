from datetime import date as date_cls
from typing import Annotated

from fastapi import APIRouter, Query

from app.services import events

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
async def list_events(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    date: Annotated[date_cls, Query()],
):
    """Ticketed events near (lat, lon) on the given local date.

    Returns an empty list when no TICKETMASTER_API_KEY is configured so
    the frontend can hide the panel gracefully.
    """
    return await events.for_date(lat, lon, date)
