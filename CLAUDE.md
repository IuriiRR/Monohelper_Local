# CLAUDE.md

This file provides guidance to Claude Code when working with Monohelper_Local.

## Overview

Monohelper_Local is the Raspberry Pi local FastAPI monolith for Monohelper.
It syncs accounts and transactions directly from Monobank into a local SQLite database and exposes a web admin UI.

## Structure

- `src/local_server/` — FastAPI app, routers, admin panel, SQLite models
- `systemd/` — Raspberry Pi systemd unit file (`cloudapi-local.service`)
- `tests/` — pytest unit tests
- `secrets/` — gitignored: local_server.env, cloudapi_local.db

## Quick Start

```bash
make install        # Install deps with uv into .venv
make server         # FastAPI dev server on port 8088
make test           # Run tests
make docker-run     # Run via Docker Compose
```

## Tests

```bash
.venv/bin/pytest tests/ -v
```

## Service Map

| Service             | Port | Source                                    |
|---------------------|------|-------------------------------------------|
| `local_server`      | 8088 | `src/local_server/main.py`                |

## API Endpoints

- `GET /` — status
- `GET /healthz` — health check
- `GET /users/` — list users
- `POST /users/` — create user
- `GET /accounts/` — list accounts
- `GET /transactions/` — list transactions
- `GET /reports/monthly` — monthly budget report
- `POST /sync/accounts` — sync accounts from Monobank
- `POST /sync/transactions` — sync transactions from Monobank
- `GET /admin/` — SQLAdmin web UI

## Raspberry Pi Deployment

See README.md → "Run (bare-metal Raspberry Pi, systemd + pyenv)"

Key paths on Pi:
- App dir: `/home/ironcow/Projects/Monohelper_Local`
- Env file: `/etc/cloudapi/local_server.env`
- Systemd unit: copy `systemd/cloudapi-local.service` → `/etc/systemd/system/`

Update after `git pull`:
```bash
uv pip install -e ".[test]" --python .venv/bin/python
sudo systemctl restart cloudapi-local.service
```
