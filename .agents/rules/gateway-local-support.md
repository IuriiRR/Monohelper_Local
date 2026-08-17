# Gateway + Local Dual-Mode Support

This app runs in two access modes. Every change to URL generation or middleware
must keep both working.

## Access Modes

| Mode | Entry point | Header present |
|---|---|---|
| **Gateway** | `http://192.168.0.69:8888/cloudapi/...` via nginx api_gateway | `X-Forwarded-Prefix: /cloudapi` |
| **Direct** | `http://localhost:8088/...` via SSH tunnel or local | _(no prefix header)_ |

## How the Prefix Is Applied

`ForwardedPrefixMiddleware` in `src/main.py` reads `X-Forwarded-Prefix` and sets:
- `scope["root_path"] = prefix` — used by `request.url` (pagination, form actions, etc.)
- `scope["app_root_path"] = prefix` — used by `request.url_for()` (navigation links)

Both keys must be set together. Setting only `app_root_path` breaks pagination.
Setting only `root_path` without `app_root_path` can break `url_for`-based links
depending on how Starlette's Mount initialises `app_root_path`.

When no header is present the middleware is a no-op — direct access is unaffected.

## Do Not Add --root-path to uvicorn

Do NOT add `--root-path /cloudapi` to the uvicorn ExecStart in
`systemd/cloudapi-local.service`. That flag is a static value applied to every
request including direct access, and produces wrong URLs on port 8088.
The middleware already handles this per-request.

## nginx Side (api_gateway repo)

The `/cloudapi/` location in `nginx/conf.d/00-gateway.conf` must:
- Use a trailing slash on `proxy_pass` to strip the prefix
- Send `proxy_set_header X-Forwarded-Prefix /cloudapi`
- Send `proxy_set_header Host $http_host` (preserves port 8888 for asset URLs)
