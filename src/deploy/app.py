"""FastAPI application for the deploy service.

Reuses the main app's dual-mode gateway support (``ForwardedPrefixMiddleware``, copied
verbatim from ``src/main.py``) and central logging, so the same bundle/UI works behind
the nginx gateway (``X-Forwarded-Prefix``) and on direct access.
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from deploy.db import create_db_and_tables
from deploy.routers import router
from deploy.runner import recover_orphans
from deploy.web import setup_web
from logging_config import setup_logging

logger = logging.getLogger(__name__)


class ForwardedPrefixMiddleware:
    """Sets ASGI app_root_path from X-Forwarded-Prefix (sent by the nginx gateway only)."""

    def __init__(self, inner: ASGIApp) -> None:
        self._inner = inner

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            prefix = headers.get(b"x-forwarded-prefix", b"").decode().strip()
            if prefix:
                scope = {**scope, "app_root_path": prefix}
        await self._inner(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    setup_logging()
    create_db_and_tables()
    recover_orphans()
    setup_web(app)
    yield


app = FastAPI(title="Monohelper Deploy Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ForwardedPrefixMiddleware)

app.include_router(router, tags=["deploy"])


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
