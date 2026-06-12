"""Fixtures for the deploy-service tests.

Mirrors the root ``tests/conftest.py`` pattern: an in-memory SQLite engine, a ``session``
fixture that points ``deploy.db.engine`` at it (so the runner's own sessions hit the test
DB), and a ``client`` fixture that overrides the FastAPI session dependency.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from deploy import db as deploy_db
from deploy.app import app
from deploy.db import get_session

_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)


@pytest.fixture(name="session")
def session_fixture(monkeypatch):
    SQLModel.metadata.create_all(_engine)
    # Runner code opens Session(deploy_db.engine); point it at the test DB.
    monkeypatch.setattr(deploy_db, "engine", _engine)
    with Session(_engine) as session:
        yield session
    SQLModel.metadata.drop_all(_engine)


@pytest.fixture(name="client")
def client_fixture(session: Session, monkeypatch):
    monkeypatch.setenv("DEPLOY_TOKEN", "test-token")

    def _override():
        return session

    app.dependency_overrides[get_session] = _override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
