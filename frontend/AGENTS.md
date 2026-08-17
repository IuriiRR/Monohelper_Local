# Frontend (React SPA) — Monohelper_Local

The `frontend/` directory is a Vite + React 18 + TypeScript SPA served by FastAPI at
`/app`. It owns the **dashboards and read views** (Monthly Report, Sync control,
transaction/account browsing). sqladmin at `/admin` is kept only for raw-data CRUD.

## Before committing frontend changes

Run from `frontend/` (or via Makefile from repo root):

- `make frontend-lint` — eslint (no errors)
- `make frontend-typecheck` — `tsc -b`, strict mode (no errors)
- `make frontend-test` — Vitest (all pass)
- `npm run format:check` — Prettier (no unformatted files)

`make quality-all` runs the Python `quality` gates plus the three frontend gates.

## Stack conventions

- **Mantine** for all UI (`@mantine/core`, `@mantine/hooks`, `@mantine/form`,
  `@mantine/dates`, `@mantine/charts`). No Tailwind. Theme once in `src/main.tsx`.
- **TanStack Query** for ALL server state. Do not fetch with bare `fetch`/`useEffect`.
  Each endpoint gets a hook in `src/hooks/` returning a query/mutation. Live status
  (e.g. sync tasks) uses `refetchInterval`, not manual polling.
- **React Router** with a runtime `basename` (see dual-mode rule). Routes live in
  `src/App.tsx`; navigation in `src/components/Layout.tsx`.
- **openapi-fetch** typed client in `src/api/client.ts`. Always go through `api.GET/POST`.

## Dual-mode base rule (CRITICAL — never break this)

The same built bundle must work behind the gateway (`/cloudapi/app`) and on direct
access (`/app`). See [.agents/rules/gateway-local-support.md](../.agents/rules/gateway-local-support.md).

- NEVER hardcode `/cloudapi` or `/app` anywhere. Read bases from `src/config.ts`
  (`apiBase` = `window.__API_BASE__`, `routerBase` = `window.__APP_BASE__`).
- Vite builds with `base: '/__APP_BASE__/'` (a placeholder). `src/web.py` rewrites that
  placeholder and injects `window.__API_BASE__` / `window.__APP_BASE__` per request from
  `X-Forwarded-Prefix`. Do not change the placeholder string without updating `src/web.py`.
- `openapi-fetch` baseUrl = `apiBase`; React Router `basename` = `routerBase`.

## Type-sync rule

`src/api/schema.d.ts` is **generated** from the backend OpenAPI schema. After ANY change
to a router or Pydantic/SQLModel response model:

1. Run the backend (`make server`, port 8088).
2. Run `make gen-types` (regenerates `frontend/src/api/schema.d.ts`).

Never hand-edit `schema.d.ts` (it is in `.prettierignore` and committed). Endpoints the
SPA consumes MUST declare a `response_model` so the type is not `unknown`/`{}`.

## Quality bars

- Strict TS — no `any`, no non-null `!` except the documented `getElementById('root')!`.
- No `console.log` / debug statements.
- No secrets in frontend code. The SPA is unauthenticated (so is the API today); never
  embed tokens or keys.
- Money is integer minor units (kopecks) — format via `src/lib/format.ts`, never inline.

## Dev over SSH (no browser extensions)

- `make frontend-dev` runs Vite on `:5173` (proxies API to `:8088`). Port-forward with
  `ssh -L 5173:localhost:5173 <pi>`.
- React Query Devtools render **in-page** (bottom panel) — no browser extension needed.
- Vite's error overlay + the in-page devtools are the primary debugging surface.
