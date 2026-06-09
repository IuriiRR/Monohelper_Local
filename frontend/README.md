# Monohelper Frontend (React SPA)

Vite + React 18 + TypeScript single-page app for Monohelper_Local. It owns the
**dashboards and read views** and is served by the FastAPI backend at **`/app`**.
sqladmin (`/admin`) is kept for raw-data CRUD.

- **UI:** Mantine (`@mantine/core`, `hooks`, `form`, `dates`, `charts`)
- **Server state:** TanStack Query (incl. live polling for sync tasks)
- **Routing:** React Router (runtime `basename`)
- **API types:** generated from the backend OpenAPI schema via `openapi-typescript`,
  consumed through an `openapi-fetch` client
- **Tests:** Vitest + React Testing Library

## Commands

```bash
npm install            # or: make frontend-install (npm ci)
npm run dev            # Vite dev server on :5173 (proxies /accounts,/sync,... to :8088)
npm run build          # type-check + production build -> dist/
npm run typecheck      # tsc -b (strict)
npm run lint           # eslint
npm test               # vitest run
npm run format         # prettier --write
npm run gen-types      # regenerate src/api/schema.d.ts from http://127.0.0.1:8088/openapi.json
```

From the repo root, the same are available as `make frontend-*` targets, plus
`make quality-all` (backend + frontend gates).

## Dev over SSH

The Pi is headless; develop over SSH and forward the Vite port:

```bash
ssh -L 5173:localhost:5173 <pi>
make server          # backend on :8088 (first terminal)
make frontend-dev    # Vite + HMR on :5173 (second terminal)
```

No browser extensions required: **TanStack Query Devtools render in-page**, and Vite's
error overlay surfaces build/runtime errors.

## Dual-mode (gateway vs direct) — important

The app is reached two ways and the same bundle must work in both:

| Mode    | URL                                      | `X-Forwarded-Prefix` |
|---------|------------------------------------------|----------------------|
| Gateway | `http://<host>:8888/cloudapi/app/`       | `/cloudapi`          |
| Direct  | `http://localhost:8088/app/`             | _(none)_             |

Vite builds with `base: '/__APP_BASE__/'` (a placeholder). The backend (`src/web.py`)
rewrites that placeholder and injects `window.__API_BASE__` / `window.__APP_BASE__` per
request. The app reads those in `src/config.ts`. **Never hardcode `/cloudapi`.**
After changing any router/model, run `npm run gen-types`.

## Layout

```
src/
  main.tsx              providers (Mantine, Query, Router) + Mantine CSS
  App.tsx               routes
  config.ts             apiBase / routerBase from injected window globals
  api/client.ts         openapi-fetch client
  api/schema.d.ts        generated types (do not edit; committed)
  hooks/                TanStack Query hooks (useMonthlyReport, useSync, ...)
  pages/                Dashboard, Sync, Transactions, Accounts
  components/Layout.tsx  AppShell + nav
  lib/format.ts         currency / date formatting
  test/                 Vitest setup + render helper
```
