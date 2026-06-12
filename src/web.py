"""Serve the built React SPA (``frontend/dist``) under ``/app`` with dual-mode prefix support.

Vite builds the SPA with a placeholder asset base of ``/__APP_BASE__/`` (see
``frontend/vite.config.ts``). At request time this module rewrites that placeholder to the
effective mount path and injects the runtime API/app base, so a single immutable bundle
works under both access modes:

    - Gateway (``X-Forwarded-Prefix: /cloudapi``): assets at ``/cloudapi/app/``, API at ``/cloudapi``
    - Direct (no header):                          assets at ``/app/``,          API at ``""``

Asset files are served from ``/app/assets`` by ``StaticFiles``. Any other ``/app/*`` path
returns ``index.html`` so React Router can resolve client-side deep links.

NEVER add ``--root-path`` to uvicorn for this; the prefix is per-request (see
``.claude/rules/gateway-local-support.md``).
"""

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import load_settings

DIST = Path(__file__).parent.parent / "frontend" / "dist"
PLACEHOLDER = "/__APP_BASE__/"


def _effective_prefix(request: Request) -> str:
    """Return the gateway prefix (e.g. ``/cloudapi``) or ``""`` for direct access.

    ``ForwardedPrefixMiddleware`` mirrors ``X-Forwarded-Prefix`` into ``app_root_path``;
    we read the header first and fall back to the scope, then strip any trailing slash.
    """
    prefix = request.headers.get("x-forwarded-prefix") or request.scope.get("app_root_path", "")
    return prefix.rstrip("/")


def _render_index(template: str, request: Request, api_key: str = "") -> str:
    """Rewrite the placeholder base and inject runtime bases into index.html."""
    prefix = _effective_prefix(request)
    app_base = f"{prefix}/app"
    html = template.replace(PLACEHOLDER, f"{app_base}/")
    inject = (
        f"<script>window.__API_BASE__={json.dumps(prefix)};"
        f"window.__APP_BASE__={json.dumps(app_base)};"
        f"window.__API_KEY__={json.dumps(api_key)};</script>"
    )
    return html.replace("</head>", f"{inject}</head>", 1)


def setup_web(app: FastAPI) -> None:
    """Mount the SPA under ``/app``. No-op-safe when the frontend has not been built."""
    index_file = DIST / "index.html"

    if not index_file.exists():

        @app.get("/app", include_in_schema=False)
        @app.get("/app/{full_path:path}", include_in_schema=False)
        async def spa_not_built() -> HTMLResponse:
            return HTMLResponse(
                "<h1>Frontend not built</h1><p>Run <code>make frontend-build</code>.</p>",
                status_code=503,
            )

        return

    index_template = index_file.read_text(encoding="utf-8")
    api_key = load_settings().internal_api_key
    app.mount("/app/assets", StaticFiles(directory=DIST / "assets"), name="spa-assets")

    @app.get("/app", include_in_schema=False)
    @app.get("/app/{full_path:path}", include_in_schema=False)
    async def spa(request: Request) -> HTMLResponse:
        return HTMLResponse(_render_index(index_template, request, api_key))
