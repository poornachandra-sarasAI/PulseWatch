# PulseWatch

A locally deployable HTTP uptime-monitoring tool. PulseWatch periodically checks your HTTP endpoints, records latency and status history, and presents everything in a dark-mode dashboard.

---

## Quick Start (Docker Compose)

**Prerequisites**: Docker + Docker Compose (v2).

```bash
git clone <your-repo-url>
cd PulseWatch

# Copy env template (no secrets to set for local use)
cp .env.example .env

# Build and start all four services
docker compose up --build
```

Services started:

| Service   | Port | Description                                 |
|-----------|------|---------------------------------------------|
| db        | 5432 | PostgreSQL 16                               |
| api       | 8000 | FastAPI backend + Alembic migrations        |
| scheduler | —    | Background check runner (polls every 5 s)   |
| frontend  | 3000 | Next.js dashboard                           |

Open [http://localhost:3000](http://localhost:3000).

> **Note**: The API runs database migrations automatically at startup via Alembic. No manual `alembic upgrade` is required.

---

## Local Development (without Docker)

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 running on `localhost:5432`

### 1 — Backend

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit env
cp .env.example .env
# Edit DATABASE_URL in .env if your Postgres credentials differ

# Apply migrations
PYTHONPATH=backend .venv/bin/alembic -c backend/alembic.ini upgrade head

# Start the API
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --reload

# In a second terminal, start the scheduler
PYTHONPATH=backend .venv/bin/python backend/scripts/run_scheduler.py --poll-interval 5
```

API is available at [http://127.0.0.1:8000](http://127.0.0.1:8000).  
Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 2 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Running Tests

```bash
# From the project root
PYTHONPATH=backend .venv/bin/pytest backend/tests/ -v
```

Tests run against an **in-memory SQLite** database — no PostgreSQL is required.

---

## API Reference

All endpoints are prefixed with `/api/monitors`.

| Method | Path                                 | Description                             |
|--------|--------------------------------------|-----------------------------------------|
| POST   | `/api/monitors`                      | Create a monitor (returns 201)          |
| GET    | `/api/monitors`                      | List all monitors                       |
| GET    | `/api/monitors/{id}`                 | Get one monitor (404 if missing)        |
| PATCH  | `/api/monitors/{id}/pause`           | Pause a monitor                         |
| DELETE | `/api/monitors/{id}`                 | Delete monitor + history (returns 204)  |
| GET    | `/api/monitors/{id}/results`         | Paginated result history                |
| GET    | `/api/monitors/{id}/summary`         | 24 h uptime/latency summary             |
| GET    | `/health`                            | API health check                        |

### Pagination (`/results`)

Query params:

- `limit` (default 50, max 100) — results per page.
- `before` — ISO-8601 UTC timestamp cursor from `next_before` in a previous response.

---

## Environment Variables

| Variable                    | Default                                             | Description                                      |
|-----------------------------|-----------------------------------------------------|--------------------------------------------------|
| `POSTGRES_DB`               | `pulsewatch`                                        | PostgreSQL database name                         |
| `POSTGRES_USER`             | `pulsewatch`                                        | PostgreSQL user                                  |
| `POSTGRES_PASSWORD`         | `pulsewatch`                                        | PostgreSQL password                              |
| `DATABASE_URL`              | `postgresql+psycopg://pulsewatch:...@localhost/...` | Full SQLAlchemy connection string                |
| `NEXT_PUBLIC_API_BASE_URL`  | `http://127.0.0.1:8000`                             | Backend URL visible to the **browser** (not Docker hostname) |

---

## Architecture

```
┌───────────────────────────────────────────────┐
│  Browser                                      │
│  Next.js frontend  ──── NEXT_PUBLIC_API_BASE  │
└───────────────────────────┬───────────────────┘
                            │ HTTP
┌───────────────────────────▼───────────────────┐
│  FastAPI API  (port 8000)                     │
│  • Monitor CRUD                               │
│  • Result history + summary                   │
└───────────────────────────┬───────────────────┘
                            │ SQLAlchemy
┌───────────────────────────▼───────────────────┐
│  PostgreSQL  (port 5432)                      │
│  • monitors table                             │
│  • check_results table                        │
└───────────────────────────▲───────────────────┘
                            │ SQLAlchemy
┌───────────────────────────┴───────────────────┐
│  Scheduler process                            │
│  • Polls DB every N seconds                   │
│  • Runs HTTP checks via httpx                 │
│  • Writes CheckResult rows                    │
└───────────────────────────────────────────────┘
```

---

## Out of Scope (v0)

Authentication, alerting, retries, queues, Redis, multi-region probes, Kubernetes, and public deployment belong to later versions.