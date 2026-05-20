# DayTour — Migration Plan

Migrating the original Django prototype at <https://github.com/xpoes123/DayTour>
to a modern, robust, AI-augmented stack.

## What the original is

A Django 5 monolith that:

1. Takes a starting location, radius, transit mode, and desired stop count.
2. Hits Google Places Text Search → Nearby Search to find tourist attractions.
3. Solves a small TSP via a 2-opt heuristic to order stops.
4. Renders an itinerary page with an embedded Google Maps directions iframe and
   restaurant suggestions near each stop.
5. Has a `blog/` app for posting reviews after a trip, an `authuser/` custom
   user model, and a `home/` landing app.

State is mostly *transient* — `request.session['routes']`, `name_lookup`, etc.
Only `Itinerary` (list of location names), `Location`, `Review`, and `BlogPost`
are persisted.

## Problems carrying forward

| Problem | Today | Target |
|---|---|---|
| Secret in git | `G_API_KEY` hardcoded in `settings.py` | env-only via `pydantic-settings`; rotate key |
| Transient itineraries | Stored in Django session | Persist itineraries with stable IDs, sharable URLs |
| Server-rendered templates only | Django templates | Decoupled API + SPA frontend |
| Google Places everywhere | Synchronous `requests` blocking the worker | Async `httpx` + Redis-cached responses |
| No tests | `tests.py` empty in every app | `pytest` with fixtures; CI later |
| Two user models | `authuser.User` AND `django.contrib.auth.models.User` (FK target inconsistent) | Single user model, JWT auth |
| TSP is fine but isolated | `two_opt.py` is the only real algorithm worth keeping | Port verbatim to `services/routing.py` |
| Pre-AI | No LLM features | Natural-language itinerary requests, summaries, vibe-matching |

## Target stack

### Backend — Python, matches the rest of `~/code/`

- **FastAPI** — async, OpenAPI for free, plays nicely with the frontend client
- **SQLAlchemy 2.0 async + Alembic** — same pattern as Sage / Stavid / Sentinel
- **PostgreSQL** — same pattern as Stavid / Sentinel
- **pydantic-settings** — config; no secrets in code
- **httpx** — async HTTP for Google Places
- **Redis** — cache Places responses (24h TTL) to control cost
- **python-jose + passlib[bcrypt]** — JWT auth
- **pytest + pytest-asyncio + httpx test client** — tests
- **Anthropic SDK (Claude API)** — Haiku for itinerary planning from natural
  language; Sonnet for trip summaries / blog suggestions

### Frontend — Next.js, matches scibowl-org

- **Next.js 15 App Router + TypeScript**
- **Tailwind CSS + shadcn/ui** — design system without lock-in
- **Mapbox GL JS** *or* **react-leaflet** — map rendering (decoupled from the
  embedded Google Maps iframe — much better UX, much lower cost)
- **TanStack Query** — server state + caching of itinerary fetches
- **Auth.js (NextAuth v5)** — credentials provider hitting our `/auth` endpoints

### Infra

- **Docker Compose** for local dev (`postgres`, `redis`, `backend`, `frontend`)
- **Hetzner VPS** for prod (same box as Sage/Sentinel/Stavid) → Sentinel can
  pick up deploys later
- **`.env` / `.env.example`** discipline; never commit secrets

## New design — what's robust about it

### Domain model

```
User ─┬─ owns ─► Itinerary ─┬─ ordered list of ─► Stop
      │                     │
      │                     └─ has ─► Route (computed; cached by stop-set hash)
      │
      └─ writes ─► Review ─► targets ─► Place

Place (cached Google Places metadata — keyed by google_place_id)
```

Key shifts from the original:

- **Itinerary holds rich `Stop` rows**, not a JSON list of names. Each `Stop`
  has `position`, `place_id`, `notes`, `arrival_time`, `dwell_minutes`.
- **`Place` is its own cache table** (name, lat/lng, photo ref, rating,
  price level, types) — populated lazily from Google Places, never re-queried
  within the cache TTL.
- **`Route` is derivative** — recomputed from a stop set; the 2-opt result is
  cached so navigating between candidate orderings is instant.

### API surface (REST, all under `/api`)

```
POST  /auth/register
POST  /auth/login              → JWT
GET   /auth/me

POST  /itineraries             body: { start_loc, radius_m, stop_count, transit_mode }
                               → creates draft itinerary, returns candidate stop list
POST  /itineraries/{id}/pick   body: { selected_place_ids }
                               → finalizes stop set, computes route(s)
GET   /itineraries/{id}        → full itinerary with route + restaurants
GET   /itineraries/{id}/share  → public read-only token
GET   /itineraries             → user's history

POST  /itineraries/from-prompt body: { prompt: "chill rainy-day in Madison, ~3 stops, walking" }
                               → Claude translates → POST /itineraries internally

POST  /places/search           proxy: text search
GET   /places/{id}             cached place details
GET   /places/{id}/restaurants nearby restaurants (cached)

POST  /reviews                 body: { place_id, rating, text }
GET   /places/{id}/reviews
```

### Why this is more robust

1. **Itineraries are first-class persisted objects with stable URLs** — share
   `/i/abc123` with a friend; no session magic.
2. **Routing is decoupled from request lifecycle** — `services/routing.py`
   takes a list of stop IDs and returns ordered IDs. Easy to swap 2-opt for
   OR-Tools later.
3. **Google Places usage is monitored and capped** — every call goes through
   `services/places.py` which checks Redis first, logs cost, and refuses to
   exceed a daily budget cap (configurable).
4. **The AI features are additive, not load-bearing** — natural-language
   planning sits on top of the same `/itineraries` endpoint; if Claude is down,
   the form-based flow still works.
5. **Frontend can iterate without backend redeploys** — the API is stable;
   shadcn lets us polish UX freely.

## Cutover sequence

1. **Phase 0 (this commit)** — scaffold both apps, copy 2-opt verbatim, write
   CLAUDE.md, MIGRATION.md. No data migration; the original DB is throwaway.
2. **Phase 1 — backend MVP**: auth, `POST /itineraries`, `services/places.py`
   (with Redis cache stubbed in-memory at first), routing, GET endpoints.
   Pytest coverage on the routing service.
3. **Phase 2 — frontend MVP**: landing → planner form → results page with a
   real map (Mapbox GL) showing the route + numbered stop markers.
4. **Phase 3 — AI**: `POST /itineraries/from-prompt`, post-trip summary
   generation, "places like this one" suggestions.
5. **Phase 4 — Social**: reviews, blog feed, sharable itineraries.
6. **Phase 5 — Deploy**: dockerize, ship to Hetzner alongside the other bots,
   wire into Sentinel's deploy pipeline.

## What we are deliberately NOT bringing forward

- The hardcoded Google API key (rotate it!)
- The dual user model muddle in `authuser/`
- The `home/Home/home.html` casing inconsistency
- Heroku Procfile (we use systemd on Hetzner)
- jupyter / matplotlib / numpy in `requirements.txt` (leaked from a notebook env)
- Storing `locations` as a JSON list of names on `Itinerary` — replaced by `Stop` rows
