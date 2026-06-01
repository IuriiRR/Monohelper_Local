# Monohelper Local (Raspberry Pi)

FastAPI monolith server for Monohelper running on a Raspberry Pi. Hosts the SQLite database, syncs accounts and transactions directly from Monobank, and exposes a web admin UI.

## What It Does

- **FastAPI server** (`cloudapi-local.service`) on port 8088:
  - `/admin` — SQLAdmin web UI (jars, cards, transactions, monthly report, sync panel)
  - `/users`, `/accounts`, `/transactions`, `/reports` — REST API
  - `/sync/accounts`, `/sync/transactions` — trigger Monobank sync
  - `/healthz` — health check
- **SQLite** — local database at `secrets/cloudapi_local.db`

## Prerequisites

- Raspberry Pi OS 64-bit (recommended)
- Either Docker + Docker Compose plugin, or bare-metal **systemd + pyenv**
- Environment file with credentials (see `.env.example`)

## Credentials

Store secrets at `/etc/cloudapi/local_server.env` (chmod `600`):

```
INTERNAL_API_KEY=your-secret-key
REPORT_TIMEZONE=Europe/Kyiv
```

See `.env.example` for all available settings.

## Run (Docker)

```bash
cp .env.example .env
# Fill in INTERNAL_API_KEY
docker compose up -d --build
curl -fsS http://127.0.0.1:8088/healthz
```

## Run (local dev)

```bash
cp .env.example .env
make install   # creates .venv and installs deps
make server    # starts uvicorn on port 8088
make worker    # in a second terminal: starts the background worker
```

## Background Worker

Sync no longer runs inside the HTTP request. The `POST /sync/*` endpoints (and the
admin Sync panel) **enqueue a task** into a table on the existing SQLite DB and
return `202 {"task_id": N, "status": "queued"}` immediately. A separate **worker
process** (`src/worker.py`) polls that table, runs the Monobank sync, and records
the result. No Redis/Celery — a single sequential worker is enough (Monobank's
1-minute rate-limit cooldown forces serialization anyway).

```
POST /sync/*  ──enqueue──▶  task table  ◀──claim──  worker (poll loop)
GET /tasks, /tasks/{id}  ── read task status / result
```

- **Task types:** `sync_accounts`, `sync_transactions` (payload `{"days": N, "user_id": ...}`).
- **Dedupe:** enqueuing a task identical to one already pending returns the existing id.
- **Retries:** a failed task is retried with a 60s backoff (Monobank cooldown), capped
  at `WORKER_MAX_ATTEMPTS` (default 15) and `WORKER_TASK_DEADLINE_SEC` (default 900s).
  After that it is dead-lettered (`status=error`). Validation / unknown-type errors are
  terminal immediately.
- **Crash recovery:** tasks left `running` after a crash are requeued on worker startup
  (sync is idempotent via `session.merge`).
- **Config (env):** `LOG_LEVEL`, `WORKER_POLL_INTERVAL`, `WORKER_RETRY_BACKOFF_SEC`,
  `WORKER_MAX_ATTEMPTS`, `WORKER_TASK_DEADLINE_SEC` — see `.env.example`.

Trigger and inspect:

```bash
curl -XPOST http://127.0.0.1:8088/sync/accounts      # → {"task_id": 1, "status": "queued"}
curl http://127.0.0.1:8088/tasks/                    # recent tasks + status
curl http://127.0.0.1:8088/tasks/1                   # one task with result/error
```

The admin Sync panel (`/admin/sync-panel`) enqueues the same tasks and shows a
recent-tasks table; refresh to see status change.

## Run (bare-metal Raspberry Pi, systemd + pyenv)

For long-running production-style deploys without Docker. Tested on Raspberry Pi OS Bookworm 64-bit. Assumes [pyenv](https://github.com/pyenv/pyenv) is already installed under your normal Linux user. The service runs as that same user — pyenv is per-user, so we don't introduce a separate system user.

These docs assume the repo lives under **`ironcow`** at **`/home/ironcow/Projects/Monohelper_Local`** (adjust `DEPLOY_*` if your layout differs). Export once per shell (or add to `~/.bashrc`):

```bash
export DEPLOY_USER="ironcow"
export DEPLOY_HOME="/home/ironcow"
export APP_DIR="${DEPLOY_HOME}/Projects/Monohelper_Local"
export PY_VERSION="3.11.10"
```

Every command below uses `$APP_DIR`, `$DEPLOY_USER`, and `$PY_VERSION`.

### 1. System prep

```bash
sudo apt update
sudo apt install -y git
sudo mkdir -p /etc/cloudapi
sudo chown root:${DEPLOY_USER} /etc/cloudapi
sudo chmod 750 /etc/cloudapi
```

Pyenv supplies Python (including `venv`); no `apt install python3-venv` is required for this path.

### 2. Make sure pyenv has the right Python

Run as **`${DEPLOY_USER}`** (SSH as `ironcow`, not root):

```bash
pyenv --version                  # sanity check; pyenv must be on PATH
pyenv install -s "${PY_VERSION}" # idempotent: skip if already installed
```

### 3. Clone or sync the repo into `$APP_DIR`

First-time clone:

```bash
mkdir -p "$(dirname "${APP_DIR}")"
git clone https://github.com/<you>/Monohelper_Local.git "${APP_DIR}"
cd "${APP_DIR}"
pyenv local "${PY_VERSION}"    # writes ${APP_DIR}/.python-version
```

If you already keep the tree elsewhere, sync the repo so it sits directly under `${APP_DIR}` (same layout as this Git repo).

After `pyenv local`, `python` and `python -m venv` inside `"${APP_DIR}"` resolve to the pyenv-managed interpreter via shims.

### 4. Create the virtual environment and install deps using `uv`

Using `uv` is recommended for extremely fast dependency installation and virtualenv management.

```bash
cd "${APP_DIR}"
uv venv .venv
uv pip install -e ".[test]" --python .venv/bin/python
```

The venv records an absolute path to the pyenv interpreter, so systemd can call `"${APP_DIR}/.venv/bin/python"` directly without pyenv shims at runtime.

`pyproject.toml` pins every dependency (`fastapi`, `loguru`, `requests`, `sqlmodel`, ...), so this single install line is enough.

### 5. Drop credentials into `/etc/cloudapi/`

From `"${APP_DIR}"`, run with `sudo`:

```bash
cd "${APP_DIR}"
sudo install -o root -g ${DEPLOY_USER} -m 640 ./local_server.env /etc/cloudapi/local_server.env
sudo install -o root -g ${DEPLOY_USER} -m 640 ./sa.json          /etc/cloudapi/sa.json
```

Use real filenames if yours differ (e.g. copy from `.env.example`).

### 6. Install the systemd units

The shipped unit in `systemd/` is aligned with **`ironcow`** and **`/home/ironcow/Projects/Monohelper_Local`**. If you changed `DEPLOY_USER` / `APP_DIR`, edit `User=`, `Group=`, `WorkingDirectory=`, `Environment=PYTHONPATH=`, and `ExecStart=` paths in the unit file before copying.

```bash
# 1) Copy both units: the admin server and the background worker
sudo cp "${APP_DIR}/systemd/cloudapi-local.service" /etc/systemd/system/
sudo cp "${APP_DIR}/systemd/cloudapi-worker.service" /etc/systemd/system/

sudo systemctl daemon-reload

# 2) Enable + start
sudo systemctl enable --now cloudapi-local.service
sudo systemctl enable --now cloudapi-worker.service
```

### 7. Verify

```bash
# Admin server (cloudapi-local.service) health + admin panel:
curl -fsS http://127.0.0.1:8088/healthz
curl -fsI http://127.0.0.1:8088/admin   # should return 200 or redirect to /admin/
journalctl -u cloudapi-local.service -f

# Worker: queue a task and watch it run
curl -fsS -XPOST http://127.0.0.1:8088/sync/accounts   # → {"task_id": N, "status": "queued"}
curl -fsS http://127.0.0.1:8088/tasks/                 # task should move pending → success
journalctl -u cloudapi-worker.service -f
```

### 8. Update service after code changes on the Pi

Run these steps any time you `git push` new code (e.g. changes to `admin.py`, routers, models):

```bash
cd "${APP_DIR}"

# 1. Pull latest code
git pull

# 2. Sync Python dependencies (fast, only installs what changed)
uv pip install -e ".[test]" --python .venv/bin/python

# 3. Restart the admin server (port 8088) and the worker
sudo cp "${APP_DIR}/systemd/cloudapi-local.service" /etc/systemd/system/
sudo cp "${APP_DIR}/systemd/cloudapi-worker.service" /etc/systemd/system/
sudo systemctl daemon-reload          # only needed if a .service file itself changed
sudo systemctl restart cloudapi-local.service
sudo systemctl restart cloudapi-worker.service

# 4. Verify
sudo systemctl status cloudapi-local.service cloudapi-worker.service
curl -fsS http://127.0.0.1:8088/healthz
curl -fsI http://127.0.0.1:8088/admin
```

If you bump Python: `pyenv install -s 3.11.<new>`, edit `.python-version`, then `rm -rf .venv && uv venv .venv && uv pip install -e ".[test]" --python .venv/bin/python`, then restart the target above.

## Verify

```bash
curl http://localhost:8088/healthz
curl -fsI http://localhost:8088/admin
```
