from datetime import date as date_cls
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.services import weather

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("")
async def forecast(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    date: Annotated[date_cls, Query()],
):
    """Hourly + daily forecast for a (lat, lon, date). See services.weather."""
    result = await weather.forecast(lat, lon, date)
    if not result:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "weather lookup failed")
    return result
