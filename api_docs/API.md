# Monohelper Local API

Base URL (gateway): `http://192.168.0.69:8888/cloudapi`  
Base URL (direct): `http://localhost:8088`

---

## Authentication

All data endpoints require an API key in the request header:

```
X-API-Key: <INTERNAL_API_KEY>
```

The backend reads the key from the `INTERNAL_API_KEY` environment variable.  
The SPA receives the key at page load via `window.__API_KEY__` (injected by the server into `index.html`).  
In Vite dev mode, set `VITE_API_KEY=<key>` in `frontend/.env.local` as a fallback.

### Responses

| Status | Meaning |
|--------|---------|
| `401` | Key missing or wrong |
| `503` | `INTERNAL_API_KEY` not configured on server |

### Exempt endpoints (no key required)

- `GET /` — status
- `GET /healthz` — health check
- `GET /app*` — SPA HTML and assets
- `GET /admin*` — SQLAdmin UI (uses its own session-based password auth, see below)

---

## Admin Panel (`/admin`)

Protected separately with a password login form when `ADMIN_PASSWORD` is set.  
If `ADMIN_PASSWORD` is unset, admin is open (only suitable for local/dev).

```
ADMIN_PASSWORD=<password>
```

Session cookie is signed with `INTERNAL_API_KEY` (falls back to `ADMIN_PASSWORD`).

---

## Endpoints

### Status

#### `GET /`
Returns server status.

**Response**
```json
{ "message": "CloudApi Local Server is running" }
```

#### `GET /healthz`
Returns health check data.

**Response**
```json
{ "status": "ok", "last_heartbeat_at": null, "last_error": null }
```

---

### Users

#### `GET /users/`
List all users.

**Headers:** `X-API-Key: <key>`

**Response**
```json
{
  "users": [
    { "user_id": "abc123", "username": "Alice", "active": true, "created_at": "2025-01-01T00:00:00" }
  ]
}
```

#### `POST /users/`
Create a user.

**Headers:** `X-API-Key: <key>`  
**Body**
```json
{ "user_id": "abc123", "username": "Alice", "mono_token": "<monobank-token>" }
```

**Response** `200` — created user object  
**Response** `409` — user_id already exists

---

### Accounts

#### `GET /accounts/`
List all accounts.

**Headers:** `X-API-Key: <key>`

**Response**
```json
{
  "accounts": [
    { "id": "...", "title": "Jar 1", "type": "jar", "balance": 100000, "is_budget": true, "is_active": true }
  ]
}
```

---

### Transactions

#### `GET /transactions/`
List transactions with optional filters.

**Headers:** `X-API-Key: <key>`  
**Query params:** `account_id`, `from_time` (unix), `to_time` (unix), `limit`, `offset`

**Response**
```json
{
  "transactions": [
    { "id": "...", "account_id": "...", "amount": -5000, "balance": 95000, "time": 1700000000, "comment": "Coffee" }
  ]
}
```

---

### Reports

#### `GET /reports/monthly`
Monthly budget report with per-jar balance chart data.

**Headers:** `X-API-Key: <key>`  
**Query params:** `year` (int), `month` (int, 1-12)

**Response**
```json
{
  "year": 2025,
  "month": 6,
  "jars": [
    {
      "id": "...",
      "title": "Food",
      "is_budget": true,
      "total_spent": 120000,
      "balance": 80000,
      "chart": [{ "time": 1700000000, "balance": 200000 }]
    }
  ]
}
```

---

### Sync

#### `POST /sync/accounts`
Enqueue an accounts sync task.

**Headers:** `X-API-Key: <key>`

**Response** `202`
```json
{ "task_id": 1, "status": "queued" }
```

#### `POST /sync/transactions`
Enqueue a transactions sync task.

**Headers:** `X-API-Key: <key>`  
**Body** (optional)
```json
{ "days": 7 }
```

**Response** `202`
```json
{ "task_id": 2, "status": "queued" }
```

---

### Tasks

#### `GET /tasks/`
List recent tasks.

**Headers:** `X-API-Key: <key>`  
**Query params:** `status` (`pending` | `running` | `done` | `failed`), `limit` (default 20)

**Response**
```json
{
  "tasks": [
    { "id": 1, "type": "sync_accounts", "status": "done", "created_at": "...", "payload": {} }
  ]
}
```

#### `GET /tasks/{id}`
Single task status and result.

**Headers:** `X-API-Key: <key>`

**Response** `200` — task object  
**Response** `404` — not found

---

## Dev Setup Notes

```bash
# backend
INTERNAL_API_KEY=dev-key make server

# frontend (Vite dev, :5173)
echo "VITE_API_KEY=dev-key" >> frontend/.env.local
make frontend-dev
```

The Vite proxy forwards API calls to :8088, so the same key works for both.
