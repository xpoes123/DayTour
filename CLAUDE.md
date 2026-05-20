# DayTour

Multi-stop day itinerary planner. User gives a starting location, radius, and
desired number of stops; the app picks tourist attractions nearby, orders them
with a 2-opt TSP heuristic, and renders a map + per-stop restaurant
suggestions. Natural-language planning ("chill walking day in Madison, ~4
stops") routes through Claude.

This is a **rewrite** of <https://github.com/xpoes123/DayTour>. See
[MIGRATION.md](./MIGRATION.md) for what changed and why. The original Django
codebase is reference-only — do not import from it.

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, SQLAlchemy 2.0 async, Alembic, PostgreSQL, Redis, httpx |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| AI | Anthropic Claude API — Haiku for prompt→params, Sonnet for summaries |
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind, shadcn/ui, TanStack Query |
| Map | Mapbox GL JS (decoupled from Google Maps iframe) |
| External | Google Places API (Text Search, Nearby Search, Details, Photos) |
| Infra | Docker Compose (dev), systemd on Hetzner VPS (prod) |

Matches the conventions of Sage / Sentinel / Stavid in `~/code/`:
Python 3.12+, async SQLAlchemy, pydantic-settings, pytest.

## Repo layout

```
backend/
  app/
    main.py              FastAPI app entry
    api/                 route handlers grouped by resource
    core/                config (pydantic-settings), security (JWT), deps
    db/                  session, base, init
    models/              SQLAlchemy ORM models
    schemas/             Pydantic request/response models
    services/
      places.py          Google Places + Redis cache
      routing.py         2-opt TSP (ported from the original two_opt.py)
      llm.py             Anthropic client + prompt→itinerary translation
  alembic/               migrations
  tests/                 pytest
  pyproject.toml
frontend/
  app/                   Next.js App Router pages
  components/
  lib/                   api client, auth, hooks
  package.json
MIGRATION.md             what changed vs the Django original
```

## Coding conventions

- **Python**: type hints on function signatures; async by default; no
  `import *`; no comments unless the WHY is non-obvious.
- **SQLAlchemy**: 2.0 declarative-style models; async sessions; never block
  on sync I/O in a request handler.
- **TS**: strict mode; functional components; colocate component state.
- **Tests**: every PR with non-trivial logic gets a pytest test. The 2-opt
  routing service is pure and easy to unit-test — start there.
- **Secrets**: `.env` only, loaded by `pydantic-settings`. Never commit a
  Google or Anthropic key. The original repo leaked one — do not repeat.
- **Migrations**: every model change → `alembic revision --autogenerate -m
  "..."` → review the generated SQL before committing.

## How the planner works

```
user submits planner form
  ↓ POST /itineraries  { start, radius, stop_count, transit_mode }
backend → services/places.py  (Redis-cached Google Text Search + Nearby)
  ↓ creates draft Itinerary + candidate Stops
user picks subset (optional) → POST /itineraries/{id}/pick
  ↓ services/routing.py runs 2-opt on the Place IDs (distance via Google or haversine)
  ↓ caches Route keyed by hash(sorted(stop_ids))
GET /itineraries/{id} → ordered stops + map polyline + nearby restaurants per stop
```

For the AI flow: `POST /itineraries/from-prompt` sends the user's text to
Haiku with a system prompt that asks for a JSON `{start_loc, radius_m,
stop_count, transit_mode}`, then internally calls `POST /itineraries`.

## Google Places cost discipline

The original code calls Places APIs on every form submit and never caches.
That's expensive. In the new design:

- All Places calls go through `services/places.py`
- Responses cached in Redis keyed by request params, 24h TTL
- Daily budget cap from `settings.GOOGLE_PLACES_DAILY_CAP`; once exceeded,
  endpoints return 503 and the frontend shows a friendly "back tomorrow"
- Log every cache miss so we can audit spend

## Running locally

```bash
# Backend
cd backend
uv venv && source .venv/bin/activate
uv pip install -e .
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
pnpm install
pnpm dev
```

Both expect `.env` files — see `.env.example` in each subdir.

## Things to not do

- Don't reintroduce server-side session state for itinerary candidates. The
  original code stuffed `routes` and `name_lookup` into `request.session` and
  that's exactly the brittleness we're moving away from. Persist instead.
- Don't pull `numpy` / `matplotlib` / `jupyter` into backend deps. They leaked
  into the original `requirements.txt` from a notebook env.
- Don't add a custom user model just to add fields. Add a `Profile` relation
  if you need more. (The original repo had two user models that fought each
  other — `authuser.User` vs `django.contrib.auth.models.User`.)
- Don't render maps with the Google Maps `/maps/embed` iframe. We're using
  Mapbox GL for a real interactive map.

## VPS deployment (later)

When ready: same pattern as Sage/Stavid — systemd unit on the Hetzner VPS at
`87.99.136.82`, deployed via Sentinel. Will need a domain (probably
`daytour.djiang.xyz`).
