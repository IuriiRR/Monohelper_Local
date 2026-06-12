"""Smoke test for app wiring: lifespan, middleware, and /healthz (deploy.app)."""

from fastapi.testclient import TestClient
from sqlmodel import create_engine
from sqlmodel.pool import StaticPool

from deploy import db as deploy_db
from deploy.app import app


def test_lifespan_health_and_gateway_prefix(monkeypatch):
    # Point the lifespan's create_db_and_tables / recover_orphans at an isolated DB.
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    monkeypatch.setattr(deploy_db, "engine", eng)

    # Entering the context manager runs the lifespan startup.
    with TestClient(app) as client:
        health = client.get("/healthz")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        # Gateway mode: X-Forwarded-Prefix flows through ForwardedPrefixMiddleware
        # into the injected app base.
        page = client.get("/app", headers={"X-Forwarded-Prefix": "/cloudapi-deploy"})
        assert page.status_code == 200
        # The dashboard has no /__APP_BASE__/ asset refs (inline JS/CSS); the prefix
        # surfaces in the injected runtime base instead.
        assert 'window.__APP_BASE__="/cloudapi-deploy/app"' in page.text
