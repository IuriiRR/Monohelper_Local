import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from admin import setup_admin
from database import create_db_and_tables, engine
from logging_config import setup_logging
from routers import accounts, reports, sync, tasks, transactions, users
from web import setup_web

logger = logging.getLogger(__name__)


class ForwardedPrefixMiddleware:
    """Sets ASGI root_path from X-Forwarded-Prefix (sent by nginx gateway only)."""

    def __init__(self, inner: ASGIApp) -> None:
        self._inner = inner

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            prefix = headers.get(b"x-forwarded-prefix", b"").decode().strip()
            if prefix:
                scope = {**scope, "app_root_path": prefix}
        await self._inner(scope, receive, send)


_health: dict = {"last_heartbeat_at": None, "last_error": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    setup_logging()
    create_db_and_tables()
    setup_admin(app, engine)
    setup_web(app)
    yield


app = FastAPI(title="Monohelper Local Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Added after CORS so it is the outermost middleware (runs first, before routing),
# matching the previous manual wrap. Keeps `app` a FastAPI instance so `main:app`
# and tests' dependency_overrides work.
app.add_middleware(ForwardedPrefixMiddleware)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(sync.router, prefix="/sync", tags=["sync"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])


@app.get("/")
async def root():
    return {"message": "CloudApi Local Server is running"}


@app.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "last_heartbeat_at": _health["last_heartbeat_at"],
        "last_error": _health["last_error"],
    }
