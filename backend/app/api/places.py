from typing import Annotated

from fastapi import APIRouter, Query

from app.services import places

router = APIRouter(prefix="/places", tags=["places"])


@router.get("/autocomplete")
async def autocomplete(
    q: Annotated[str, Query(min_length=2, max_length=100)],
):
    return await places.autocomplete(q)
