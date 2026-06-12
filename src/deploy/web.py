"""Serve the single-page deploy dashboard with dual-mode prefix support.

Same approach as ``src/web.py`` but for a single self-contained HTML file (no Vite build):
the page carries a ``/__APP_BASE__/`` placeholder and reads ``window.__API_BASE__`` /
``window.__APP_BASE__``, both injected per request from ``X-Forwarded-Prefix`` so one file
works behind the gateway (``/cloudapi-deploy/app``) and on direct access (``/app``).

The page is intentionally dependency-free (inline CSS/JS) so the deploy UI stays usable
while the main app it deploys is being rebuilt/restarted.
"""

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

STATIC = Path(__file__).parent / "static"
PLACEHOLDER = "/__APP_BASE__/"


def _effective_prefix(request: Request) -> str:
    """Return the gateway prefix (e.g. ``/cloudapi-deploy``) or ``""`` for direct access."""
    prefix = request.headers.get("x-forwarded-prefix") or request.scope.get("app_root_path", "")
    return prefix.rstrip("/")


def _render_index(template: str, request: Request) -> str:
    """Rewrite the placeholder base and inject runtime bases into index.html."""
    prefix = _effective_prefix(request)
    app_base = f"{prefix}/app"
    html = template.replace(PLACEHOLDER, f"{app_base}/")
    inject = f"<script>window.__API_BASE__={json.dumps(prefix)};window.__APP_BASE__={json.dumps(app_base)};</script>"
    return html.replace("</head>", f"{inject}</head>", 1)


def setup_web(app: FastAPI) -> None:
    """Mount the dashboard under ``/app`` (and serve it for any ``/app/*`` deep link)."""
    template = (STATIC / "index.html").read_text(encoding="utf-8")

    @app.get("/app", include_in_schema=False)
    @app.get("/app/{full_path:path}", include_in_schema=False)
    async def spa(request: Request) -> HTMLResponse:
        return HTMLResponse(_render_index(template, request))
