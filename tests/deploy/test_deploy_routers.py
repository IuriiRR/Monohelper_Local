"""Integration tests for the deploy HTTP API (deploy.routers)."""

import hashlib
import hmac

from deploy import runner
from deploy.models import DeployRun


def _sig(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


# --- POST /deploy ---


def test_deploy_requires_token(client):
    res = client.post("/deploy")
    assert res.status_code == 401


def test_deploy_wrong_token(client):
    res = client.post("/deploy", headers={"X-Deploy-Token": "nope"})
    assert res.status_code == 401


def test_deploy_accepted(client, monkeypatch):
    monkeypatch.setattr(runner, "start_deploy", lambda trigger: 7)
    res = client.post("/deploy", headers={"X-Deploy-Token": "test-token"})
    assert res.status_code == 202
    assert res.json() == {"run_id": 7, "status": "queued"}


def test_deploy_conflict_when_running(client, monkeypatch):
    monkeypatch.setattr(runner, "start_deploy", lambda trigger: None)
    res = client.post("/deploy", headers={"X-Deploy-Token": "test-token"})
    assert res.status_code == 409


def test_deploy_token_not_configured(client, monkeypatch):
    monkeypatch.setenv("DEPLOY_TOKEN", "")
    res = client.post("/deploy", headers={"X-Deploy-Token": "anything"})
    assert res.status_code == 503


# --- GET /deploys, /deploys/{id} ---


def test_list_and_get_deploy(client, session):
    run = DeployRun(trigger="manual", status="success")
    session.add(run)
    session.commit()
    session.refresh(run)

    listed = client.get("/deploys")
    assert listed.status_code == 200
    assert any(d["id"] == run.id for d in listed.json()["deploys"])

    single = client.get(f"/deploys/{run.id}")
    assert single.status_code == 200
    assert single.json()["status"] == "success"


def test_get_deploy_404(client):
    assert client.get("/deploys/999999").status_code == 404


# --- POST /webhook/github ---


def test_webhook_disabled_without_secret(client, monkeypatch):
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET", raising=False)
    res = client.post("/webhook/github", content=b"{}", headers={"X-GitHub-Event": "push"})
    assert res.status_code == 404


def test_webhook_bad_signature(client, monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cr3t")
    res = client.post(
        "/webhook/github",
        content=b"{}",
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": "sha256=bad"},
    )
    assert res.status_code == 401


def test_webhook_ping(client, monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cr3t")
    body = b"{}"
    res = client.post(
        "/webhook/github",
        content=body,
        headers={"X-GitHub-Event": "ping", "X-Hub-Signature-256": _sig("s3cr3t", body)},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "pong"


def test_webhook_push_on_branch_triggers(client, monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cr3t")
    monkeypatch.setenv("DEPLOY_BRANCH", "main")
    monkeypatch.setattr(runner, "start_deploy", lambda trigger: 11)
    body = b'{"ref":"refs/heads/main"}'
    res = client.post(
        "/webhook/github",
        content=body,
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": _sig("s3cr3t", body)},
    )
    assert res.status_code == 200
    assert res.json() == {"status": "queued", "run_id": 11}


def test_webhook_push_other_branch_ignored(client, monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cr3t")
    monkeypatch.setenv("DEPLOY_BRANCH", "main")
    body = b'{"ref":"refs/heads/dev"}'
    res = client.post(
        "/webhook/github",
        content=body,
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": _sig("s3cr3t", body)},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ignored"


def test_webhook_non_push_event_ignored(client, monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cr3t")
    body = b"{}"
    res = client.post(
        "/webhook/github",
        content=body,
        headers={"X-GitHub-Event": "issues", "X-Hub-Signature-256": _sig("s3cr3t", body)},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ignored"


def test_webhook_invalid_json(client, monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cr3t")
    body = b"not-json"
    res = client.post(
        "/webhook/github",
        content=body,
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": _sig("s3cr3t", body)},
    )
    assert res.status_code == 400
