# CLAUDE.md

This file provides guidance to Claude Code when working with Monohelper_Local.

## Overview

Monohelper_Local is the Raspberry Pi local FastAPI monolith for Monohelper.
It syncs accounts and transactions directly from Monobank into a local SQLite database and exposes a web admin UI.

## Structure

- `src/` — flat package (imports rely on `PYTHONPATH=src`)
  - `main.py` — FastAPI app + lifespan
  - `routers/` — HTTP endpoints (`sync.py` enqueues tasks; `tasks.py` exposes status)
  - `services/` — `sync_service.py` (Monobank logic), `tasks.py` (task queue helpers)
  - `jobs/` — task-type → handler `JOB_REGISTRY` consumed by the worker
  - `worker.py` — background worker process (poll loop + bounded retries + daily scheduler)
  - `scheduler.py` — daily task scheduler (`check_and_enqueue`); called by worker on each idle tick
  - `logging_config.py` — central stdlib logging (server + worker)
  - `web.py` — serves the React SPA (`frontend/dist`) at `/app` with dual-mode base injection
  - `admin.py` (sqladmin CRUD at `/admin`), `models.py`, `database.py`, `config.py`
- `frontend/` — React + TS (Vite) SPA: dashboards + read views, served at `/app` (see `frontend/README.md`)
- `systemd/` — Raspberry Pi units: `cloudapi-local.service`, `cloudapi-worker.service`
- `tests/` — pytest unit tests
- `secrets/` — gitignored: local_server.env, cloudapi_local.db

## Quick Start

```bash
make install        # Install deps with uv into .venv (test + dev extras)
make server         # FastAPI dev server on port 8088
make worker         # Background task worker (separate process)
make test           # Run tests
make docker-run     # Run via Docker Compose
```

## Code Quality

```bash
make lint           # ruff check — lint errors
make format         # ruff format — auto-format in place
make format-check   # ruff format --check — CI-safe format gate
make typecheck      # mypy strict — static type checking
make coverage       # pytest + coverage (HTML report in htmlcov/)
make security       # bandit — security vulnerability scan
make deadcode       # vulture — unused code detection
make pyright        # pyright — additional type checking
make quality        # all gates: lint + format-check + typecheck + coverage + security + deadcode
```

Frontend gates (run from repo root):

```bash
make frontend-lint        # eslint
make frontend-typecheck   # tsc -b (strict)
make frontend-test        # vitest
make gen-types            # regenerate frontend/src/api/schema.d.ts (needs server on :8088)
make quality-all          # backend quality + frontend lint/typecheck/test
```

## Tests

```bash
.venv/bin/pytest tests/ -v
```

## Service Map

| Service             | Port | Source                                    |
|---------------------|------|-------------------------------------------|
| `local_server`      | 8088 | `src/main.py`                             |
| `worker`            | —    | `src/worker.py` (`cloudapi-worker.service`) |

## API Endpoints

- `GET /` — status
- `GET /healthz` — health check
- `GET /users/` — list users
- `POST /users/` — create user
- `GET /accounts/` — list accounts
- `GET /transactions/` — list transactions
- `GET /reports/monthly` — monthly budget report (jars incl. per-tx `{time, balance}` points for the chart)
- `POST /sync/accounts` — **enqueue** an accounts sync task (202 `{task_id, status}`)
- `POST /sync/transactions` — **enqueue** a transactions sync task (202)
- `GET /tasks/` — list recent tasks (optional `?status=&limit=`)
- `GET /tasks/{id}` — single task status / result
- `GET /admin/` — SQLAdmin web UI (raw-data CRUD only)
- `GET /app` — React SPA (dashboards + read views); deep links served via SPA fallback

> Endpoints consumed by the SPA (`/accounts/`, `/transactions/`, `/tasks/`, `/reports/monthly`)
> declare a `response_model` so `make gen-types` produces precise TypeScript types.

> Sync runs in the **worker** process, not the HTTP request. Endpoints only enqueue;
> the worker (`make worker` / `cloudapi-worker.service`) consumes the task queue.

## Frontend (React SPA)

The dashboards (Monthly Report) and read/sync views live in `frontend/` (Vite + React +
TypeScript + Mantine + TanStack Query). The backend serves the built bundle at `/app`
via `src/web.py`; sqladmin (`/admin`) is kept for raw-data CRUD. Architectural boundary:
**React (`/app`) owns dashboards + read views; sqladmin (`/admin`) owns raw CRUD.**

Dual-mode: a single build works behind the gateway (`/cloudapi/app`) and direct (`/app`).
Vite builds with a `/__APP_BASE__/` placeholder that `src/web.py` rewrites per request from
`X-Forwarded-Prefix`, injecting `window.__API_BASE__`/`window.__APP_BASE__`. Never hardcode
`/cloudapi`. See `.claude/rules/frontend.md` and `.claude/rules/gateway-local-support.md`.

Types are generated from the OpenAPI schema (`make gen-types` → `frontend/src/api/schema.d.ts`);
regenerate after any router/model change. Dev: `make frontend-dev` (Vite `:5173`, proxies to
`:8088`); over SSH forward `5173`. See `frontend/README.md`.

## Scheduled Sync

Worker auto-enqueues daily syncs when env vars are set:

| Var | Default | Purpose |
|-----|---------|---------|
| `SCHEDULE_ACCOUNTS_TIME` | _(disabled)_ | Daily accounts sync time (`HH:MM`) |
| `SCHEDULE_TRANSACTIONS_TIME` | _(disabled)_ | Daily transactions sync time (`HH:MM`) |
| `SCHEDULE_TZ` | `Europe/Kyiv` | IANA timezone for schedule times |

Pre-configured in `systemd/cloudapi-worker.service` (22:00 accounts, 23:00 transactions). Omit a var to disable that job.

## Raspberry Pi Deployment

See README.md → "Run (bare-metal Raspberry Pi, systemd + pyenv)"

Key paths on Pi:
- App dir: `/home/ironcow/Projects/Monohelper_Local`
- Env file: `/etc/cloudapi/local_server.env`
- Systemd unit: copy `systemd/cloudapi-local.service` → `/etc/systemd/system/`

Update after `git pull`:
```bash
uv pip install -e ".[test,dev]" --python .venv/bin/python
cd frontend && npm ci && npm run build && cd ..   # rebuild the SPA served at /app
sudo systemctl restart cloudapi-local.service cloudapi-worker.service
```
