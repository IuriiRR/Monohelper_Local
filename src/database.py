import os

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

# Put database inside secrets/ or a persistent local volume folder
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "secrets")
os.makedirs(DB_DIR, exist_ok=True)
sqlite_file_name = os.path.join(DB_DIR, "cloudapi_local.db")

sqlite_url = f"sqlite:///{sqlite_file_name}"

# timeout: seconds to wait for the write lock before raising "database is locked".
# Needed because the web process (enqueue) and the worker (claim/update) both write.
connect_args = {"check_same_thread": False, "timeout": 30}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    # WAL: readers don't block the single writer (better for web + worker).
    # busy_timeout: wait instead of erroring when the file is briefly locked.
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA busy_timeout=30000")
    cur.close()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
