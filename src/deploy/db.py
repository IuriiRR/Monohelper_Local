"""SQLite engine/session for the deploy service.

Mirrors ``src/database.py`` (WAL + busy_timeout) but uses its own database file
(``secrets/deploy.db``) so it never contends with the main app's two-writer DB.
"""

import os

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "secrets")
os.makedirs(DB_DIR, exist_ok=True)
sqlite_file_name = os.path.join(DB_DIR, "deploy.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Web request (enqueue) and the executor thread both write; wait for the lock.
connect_args = {"check_same_thread": False, "timeout": 30}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA busy_timeout=30000")
    cur.close()


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
