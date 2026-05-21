# DayTour

Multi-stop day itinerary planner. User gives a starting location (or just
types a vibe in prose), and the app builds a real day: ordered stops along an
actual road-following route, real bus/subway schedules where applicable,
photos and AI-written previews for every place, restaurant suggestions, and
share/export back out to Google or Apple Maps.

This is a **rewrite** of <https://github.com/xpoes123/DayTour>. See
[MIGRATION.md](./MIGRATION.md) for what changed and why. The original Django
codebase is reference-only.

Live: <https://daytour.djiang.xyz>.

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, SQLAlchemy 2.0 async, Alembic, PostgreSQL, Redis, httpx |
| Auth | JWT (python-jose) + bcrypt (passlib) — optional / guest mode |
| AI | Anthropic Claude API — Haiku for prompt→plan, Sonnet for summaries + per-place blurbs |
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind, shadcn-style components, TanStack Query |
| Map | Leaflet + OpenStreetMap tiles (no map key needed) |
| Routing | OSRM public demo for walk/bike/drive (distance is real, duration we compute from distance × per-mode speed because the demo only loads the car profile); Google Routes API for transit (real schedules, anchored to a 10am-UTC departureTime to avoid late-night detours) |
| External | Google Places (Text Search, Nearby Search, Autocomplete, Place Photos via media proxy) |
| Self-verification | Playwright + scripts in `scripts/` (`preview.py`, `preview_curation.py`, ...) |
| Infra | Caddy + TLS (autocert) on Hetzner VPS; systemd units (`daytour-backend`, `daytour-frontend`) |

Matches the conventions of Sage / Sentinel / Stavid in `~/code/`:
Python 3.12+, async SQLAlchemy 2.0, `pydantic-settings`, pytest.

## URLs

- `/` — landing with logo, three CTAs (Plan / Describe / Surprise me), featured example trip, value pillars
- `/plan` — form-based planner: start + optional end autocomplete, date + start_time, radius slider in m + mi, stops slider, vibe chips, transit mode icon buttons
- `/plan/prompt` — natural-language planner ("a chill walking day in Madison with art and lakefront")
- `/auth` — combined sign-in / register
- `/itinerary/[id]` — owner view (curation, recompute, swaps)
- `/share/[token]` — public read-only view of an itinerary

## How the planner works

```
plan request                  POST /api/itineraries
  → Google Places Text Search (start_loc → lat/lon)
  → Google Places Nearby Search (tourist_attraction in radius)
  → dedupe by place_id
  → 2-opt TSP on the candidate set
  → persist Itinerary + Stop[] + share_token

itinerary GET                 GET /api/itineraries/{id}  (or /by-share/{token})
  → load stops + places
  → routing.route(coords, mode):
      transit → google_routes.route   (per-leg parallel calls, departureTime=10am UTC)
      else    → osrm.route             (single multi-stop call; we override duration from distance)
      either fails → fall back to google_routes
  → leg-level steps (walk / bus / subway / rail) collapsed by mode+label, sub-2min walks hidden
  → lazy AI fill on the first read:
      itinerary.summary       Claude Sonnet, 1 paragraph
      place.description       Claude Sonnet, ~20 words each, batched
      (cached per-Place so repeat trips reuse them)

curation                      X a stop → removed immediately, route recomputes
                              "You might also like" panel below → click + → adds + recomputes
                              Drag the grip handle to reorder → POST /reorder (skips 2-opt)
                              "Lock my order" toggle: when on, add/remove also use /reorder
```

## Plan-time filters

When PlanRequest carries `date` and/or `start_time`, the backend stacks
filters on top of the Google Places result pool:
- **Vibe** (foodie / art / family / outdoors / nightlife / hidden_gems) shapes
  the included + excluded type lists in `_VIBE_TYPES`. Default to nightlife
  when `start_time >= 17:00` and no vibe is set.
- **Rainy day**: precip ≥50% (or ≥30% on a wet weather_code) drops outdoor
  candidates by type + name keyword.
- **Closed all day**: drops candidates whose `opening_hours` have no period
  on the trip weekday.
- **Closed at the assigned slot**: post-2-opt walk through stops, estimate
  visit minute (start + position × per-mode constant), drop any whose hours
  don't cover that minute.

## API surface

```
POST  /api/auth/register
POST  /api/auth/login
GET   /api/auth/me

POST  /api/itineraries                                            build a new trip
POST  /api/itineraries/from-prompt                                Claude Haiku translates prose → PlanRequest
GET   /api/itineraries/{id}                                       owner view
GET   /api/itineraries/by-share/{token}                           public read-only
POST  /api/itineraries/{id}/recompute                             { kept_place_ids: [...] } — 2-opt re-route
POST  /api/itineraries/{id}/reorder                               { kept_place_ids: [...] } — keep order, just re-route
POST  /api/itineraries/{id}/summarize                             generate + persist AI summary on demand
GET   /api/itineraries/{id}/alternatives                          nearby attractions excluding current stops
GET   /api/itineraries/{id}/stops/{place_id}/restaurants          4 nearest restaurants, persisted to Place
PATCH /api/itineraries/{id}/stops/{place_id}/notes                { notes: str|null } — user-authored note

GET   /api/places/autocomplete?q=...                              Google Places Autocomplete proxy
GET   /api/places/{google_place_id}/photo?max=480&idx=0           proxies the Nth Place photo (server-side key)
GET   /api/weather?lat=&lon=&date=                                Open-Meteo daily + hourly forecast
```

## Repo layout

```
backend/
  app/
    main.py
    api/
      auth.py          register, login, me
      itineraries.py   plan, from-prompt, get, by-share, recompute, alternatives, stop-restaurants
      places.py        autocomplete + photo proxy
    core/              config (pydantic-settings), security (JWT), deps (current_user, optional_current_user)
    db/                async session, Base
    models/            user, place, itinerary, stop, route, review
    schemas/           Pydantic request/response models
    services/
      places.py        Google Places client (Redis-cached, daily budget cap)
      routing.py       2-opt TSP + GeoPoint + haversine fallback
      osrm.py          OSRM demo client (distance accurate; duration recomputed)
      google_routes.py Google Routes API (transit + multi-stop)
      llm.py           Claude clients: prompt→plan, trip summaries, per-place blurbs
  alembic/             migrations 0001–0004
  tests/               pytest
  pyproject.toml
frontend/
  app/
    page.tsx           landing with featured trip
    plan/page.tsx      form planner
    plan/prompt/       natural-language planner
    auth/              login + register
    itinerary/[id]/    owner view with curation
    share/[token]/     public view
    providers.tsx      react-query
    layout.tsx
    globals.css        Tailwind + .field component
  components/
    itinerary-map.tsx + itinerary-map-inner.tsx     Leaflet wrapped in next/dynamic
    place-autocomplete.tsx
    nearby-restaurants.tsx
    trip-actions.tsx                                share + maps deep links
  lib/api.ts                                        fetch wrapper, types, formatters, schedule computer
scripts/
  preview.py                                        Playwright headless screenshot
  preview_curation.py, preview_restaurants.py, preview_itinerary_flow.py
  preview_autocomplete.py
deploy/
  daytour-backend.service
  daytour-frontend.service
  Caddyfile.snippet                                 daytour.djiang.xyz → /api → :7782, else :7783
```

## Coding conventions

- Type hints on signatures only.
- Async everywhere on the backend; never block in a handler.
- Tests sit in `backend/tests/`; routing is pure and easy to unit-test — `test_routing.py` is the model.
- **Secrets**: `.env` only. The original repo leaked a Google key — do not repeat.
- **Migrations**: every model change → `alembic revision --autogenerate -m "..."` → review SQL before commit.
- Comments only where the WHY is non-obvious. Don't restate what the code already says.

## UI self-verification (Playwright)

When making frontend changes, snapshot the live (or local) URL and inspect:

```bash
~/code/daytour/.venv/bin/python ~/code/daytour/scripts/preview.py \
    https://daytour.djiang.xyz/itinerary/17 /tmp/x.png
```

There's a `preview_*` script per non-trivial interaction (curation, restaurants,
autocomplete dropdown). Add new ones rather than reusing the generic one when
the page state matters.

## Cost discipline

- All Places + Routes calls flow through the relevant service module, which
  caches in Redis (24h for Places search, 6h for Routes/transit, 1 week for
  OSRM geometry). Daily budget cap from `settings.google_places_daily_cap`;
  exceed it and endpoints 503 with a friendly message.
- Place descriptions and itinerary summaries persist on the DB row, so they
  don't regenerate per request.
- Photos are a single server-side proxy → CDN-cacheable response with 1-week
  `Cache-Control`.

## Running locally

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in keys
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd ../frontend
npm install
cp .env.example .env.local
npm run dev
```

API: <http://localhost:8000>  ·  Web: <http://localhost:3000>

## Things to not do

- Don't reintroduce server-side session state for itinerary candidates. The
  original code stuffed `routes` and `name_lookup` into `request.session` —
  exactly the brittleness we left behind. Persist instead.
- Don't pull notebook deps (numpy / matplotlib / jupyter) into backend.
- Don't add a custom user model just to add fields — use a `Profile` relation.
- Don't render maps with the Google Maps `/maps/embed` iframe; we use Leaflet
  on OSM tiles.
- Don't expose the Google API key to the browser. The autocomplete and photo
  endpoints exist specifically so it stays server-side.
- Don't call Google Routes API for transit without `departureTime` — the
  default is "now" and produces overnight-bus detours at 3am.

## VPS deployment

- Lives at `/opt/daytour/` on the Hetzner VPS, two systemd units
  (`daytour-backend.service` on `127.0.0.1:7782`,
  `daytour-frontend.service` on `127.0.0.1:7783`).
- Caddy in front terminates TLS for `daytour.djiang.xyz` and path-routes
  `/api/*` → backend, everything else → frontend.
- Manual deploy idiom (Sentinel was offline at time of writing):

```bash
ssh root@87.99.136.82
cd /opt/daytour && git pull
cd backend && .venv/bin/pip install -e . && .venv/bin/alembic upgrade head
systemctl restart daytour-backend
cd ../frontend && npm install && npm run build
systemctl restart daytour-frontend
```
