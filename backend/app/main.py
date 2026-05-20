from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, itineraries
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title="DayTour API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(itineraries.router, prefix="/api")


@app.get("/health")
async def health():
    return {"ok": True}
