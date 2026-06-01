# secrets/

Runtime secrets — never committed to git.

Required files:
- `sa.json` (chmod 600) — GCP service account key with Cloud Scheduler permissions
- `cloudapi_local.db` — SQLite database (auto-created on first run)

Mounted into Docker containers at `/etc/cloudapi/`.
For bare-metal systemd, symlink or copy to `/etc/cloudapi/` instead.

See `.env.example` for environment variable reference.
