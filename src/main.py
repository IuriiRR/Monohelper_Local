import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from admin import setup_admin
from database import create_db_and_tables, engine
from routers import accounts, reports, sync, transactions, users

logger = logging.getLogger(__name__)

_health: dict = {"last_heartbeat_at": None, "last_error": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    setup_admin(app, engine)
    yield


app = FastAPI(title="Monohelper Local Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(sync.router, prefix="/sync", tags=["sync"])
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
