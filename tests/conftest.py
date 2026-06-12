import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

for p in (str(SRC), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import database
from database import get_session
from main import app

TEST_API_KEY = "test-api-key"

# In-memory SQLite for testing
sqlite_url = "sqlite://"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)


@pytest.fixture(name="session")
def session_fixture(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", TEST_API_KEY)
    SQLModel.metadata.create_all(engine)
    # Point worker/job code (which opens Session(database.engine)) at the test DB.
    monkeypatch.setattr(database, "engine", engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app, headers={"X-API-Key": TEST_API_KEY})
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="unauthed_client")
def unauthed_client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
