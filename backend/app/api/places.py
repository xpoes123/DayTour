from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models import Place
from app.services import places

router = APIRouter(prefix="/places", tags=["places"])


@router.get("/autocomplete")
async def autocomplete(
    q: Annotated[str, Query(min_length=2, max_length=100)],
):
    return await places.autocomplete(q)


@router.get("/{google_place_id}/photo")
async def photo(
    google_place_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    max_width: Annotated[int, Query(ge=80, le=1600, alias="max")] = 480,
):
    """Proxy the first Google Places photo for a given place_id.

    The Place's stored photo_url is actually the photo resource name
    (e.g. 'places/CHIJ.../photos/Ab43m-...'). We materialize the bytes
    via Google's media endpoint so the API key never leaves the server.
    """
    place = (
        await db.execute(select(Place).where(Place.google_place_id == google_place_id))
    ).scalar_one_or_none()
    if not place or not place.photo_url:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no photo")

    api_key = get_settings().google_places_api_key
    url = f"https://places.googleapis.com/v1/{place.photo_url}/media"
    params = {"maxWidthPx": max_width, "key": api_key, "skipHttpRedirect": "true"}
    async with httpx.AsyncClient(timeout=10) as client:
        meta = await client.get(url, params=params)
        if meta.status_code != 200:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "places photo lookup failed")
        photo_uri = meta.json().get("photoUri")
        if not photo_uri:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "no photo uri")
        img = await client.get(photo_uri)
        if img.status_code != 200:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "photo download failed")
    return Response(
        content=img.content,
        media_type=img.headers.get("content-type", "image/jpeg"),
        headers={"Cache-Control": "public, max-age=604800, immutable"},
    )
