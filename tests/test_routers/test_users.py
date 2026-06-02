from fastapi.testclient import TestClient


def test_create_user(client: TestClient) -> None:
    resp = client.post("/users/", json={"user_id": "u1", "username": "Alice", "mono_token": "tok1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == "u1"
    assert body["username"] == "Alice"


def test_create_user_no_username(client: TestClient) -> None:
    resp = client.post("/users/", json={"user_id": "u2", "mono_token": "tok2"})
    assert resp.status_code == 200
    assert resp.json()["username"] is None


def test_create_user_conflict(client: TestClient) -> None:
    client.post("/users/", json={"user_id": "u3", "mono_token": "tok3"})
    resp = client.post("/users/", json={"user_id": "u3", "mono_token": "tok3"})
    assert resp.status_code == 409
    assert "u3" in resp.json()["detail"]
