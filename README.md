# DayTour

Plan a multi-stop day trip in seconds. A modern rewrite of
<https://github.com/xpoes123/DayTour>.

- **Backend**: FastAPI + SQLAlchemy 2.0 async + Postgres + Redis
- **Frontend**: Next.js 15 + TypeScript + Tailwind + Mapbox GL
- **AI**: Claude (Haiku for prompt→plan, Sonnet for trip summaries)

See [`CLAUDE.md`](./CLAUDE.md) for project conventions and
[`MIGRATION.md`](./MIGRATION.md) for what changed vs the Django original.

## Quick start (dev)

```bash
# 1. Postgres + Redis (your preference — local services or docker compose)

# 2. Backend
cd backend
cp .env.example .env  # fill in keys
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
alembic revision --autogenerate -m "init"   # first time only
alembic upgrade head
uvicorn app.main:app --reload

# 3. Frontend
cd ../frontend
cp .env.example .env.local  # fill in mapbox token
pnpm install
pnpm dev
```

API: <http://localhost:8000>  ·  Web: <http://localhost:3000>

## Status

Scaffold complete. Next: wire up auth flow on the frontend, finish the
`/itineraries/{id}/pick` endpoint, and ship phase-1 to the VPS.
