"""Tests for X-API-Key authentication on all protected endpoints."""
import pytest
from fastapi.testclient import TestClient

from conftest import TEST_API_KEY

PROTECTED_GET = ["/users/", "/accounts/", "/transactions/", "/tasks/", "/reports/monthly"]
PROTECTED_POST = ["/sync/accounts", "/sync/transactions"]


def test_no_key_returns_401(unauthed_client: TestClient) -> None:
    for path in PROTECTED_GET:
        assert unauthed_client.get(path).status_code == 401, f"GET {path}"
    for path in PROTECTED_POST:
        assert unauthed_client.post(path).status_code == 401, f"POST {path}"


def test_wrong_key_returns_401(unauthed_client: TestClient) -> None:
    headers = {"X-API-Key": "wrong-key"}
    for path in PROTECTED_GET:
        assert unauthed_client.get(path, headers=headers).status_code == 401, f"GET {path}"


def test_correct_key_allows_access(client: TestClient) -> None:
    assert client.get("/users/").status_code == 200
    assert client.get("/accounts/").status_code == 200
    assert client.get("/tasks/").status_code == 200


def test_public_endpoints_require_no_auth(unauthed_client: TestClient) -> None:
    assert unauthed_client.get("/").status_code == 200
    assert unauthed_client.get("/healthz").status_code == 200


def test_unconfigured_key_returns_503(
    monkeypatch: pytest.MonkeyPatch, unauthed_client: TestClient
) -> None:
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)
    resp = unauthed_client.get("/users/", headers={"X-API-Key": TEST_API_KEY})
    assert resp.status_code == 503
    assert "INTERNAL_API_KEY" in resp.json()["detail"]
