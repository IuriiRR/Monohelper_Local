"""Sync-enqueue + task status endpoint tests."""

from fastapi.testclient import TestClient


def test_post_sync_accounts_returns_202(client: TestClient):
    resp = client.post("/sync/accounts")
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "queued"
    assert isinstance(body["task_id"], int)

    tasks = client.get("/tasks/").json()["tasks"]
    assert any(t["type"] == "sync_accounts" and t["status"] == "pending" for t in tasks)


def test_post_sync_transactions_enqueues_payload(client: TestClient):
    resp = client.post("/sync/transactions", json={"days": 7})
    assert resp.status_code == 202
    task_id = resp.json()["task_id"]

    task = client.get(f"/tasks/{task_id}").json()
    assert task["type"] == "sync_transactions"
    assert task["payload"]["days"] == 7


def test_list_tasks_filter_and_get(client: TestClient):
    client.post("/sync/accounts")
    client.post("/sync/transactions", json={"days": 1})

    pending = client.get("/tasks/", params={"status": "pending"}).json()["tasks"]
    assert len(pending) == 2

    assert client.get("/tasks/99999").status_code == 404
