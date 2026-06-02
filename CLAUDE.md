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
  - `admin.py`, `models.py`, `database.py`, `config.py`, `templates/`
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
- `GET /reports/monthly` — monthly budget report
- `POST /sync/accounts` — **enqueue** an accounts sync task (202 `{task_id, status}`)
- `POST /sync/transactions` — **enqueue** a transactions sync task (202)
- `GET /tasks/` — list recent tasks (optional `?status=&limit=`)
- `GET /tasks/{id}` — single task status / result
- `GET /admin/` — SQLAdmin web UI

> Sync runs in the **worker** process, not the HTTP request. Endpoints only enqueue;
> the worker (`make worker` / `cloudapi-worker.service`) consumes the task queue.

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
sudo systemctl restart cloudapi-local.service cloudapi-worker.service
```
