"""Worker dispatch / retry tests. Drives ``run_one`` directly (no poll loop)."""

from pydantic import BaseModel

import worker
from models import TaskStatus
from services.tasks import claim_next, enqueue


def _noop_sleep(_seconds):
    pass


def _claimed(session, type="sync_accounts", payload=None):
    enqueue(session, type, payload or {})
    return claim_next(session)


def test_run_one_success(session, monkeypatch):
    monkeypatch.setitem(worker.JOB_REGISTRY, "sync_accounts", lambda p: {"ok": 1})
    task = _claimed(session)

    worker.run_one(session, task, sleep=_noop_sleep)
    session.refresh(task)
    assert task.status == TaskStatus.success.value
    assert task.result == {"ok": 1}
    assert task.attempts == 1


def test_run_one_retries_then_succeeds(session, monkeypatch):
    calls = {"n": 0}

    def flaky(_payload):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return {"ok": True}

    monkeypatch.setitem(worker.JOB_REGISTRY, "sync_accounts", flaky)
    task = _claimed(session)

    worker.run_one(session, task, max_attempts=5, backoff_sec=0, sleep=_noop_sleep)
    session.refresh(task)
    assert task.status == TaskStatus.success.value
    assert task.attempts == 3


def test_run_one_dead_letters_after_max_attempts(session, monkeypatch):
    def always_fail(_payload):
        raise RuntimeError("nope")

    monkeypatch.setitem(worker.JOB_REGISTRY, "sync_accounts", always_fail)
    task = _claimed(session)

    worker.run_one(session, task, max_attempts=3, backoff_sec=0, sleep=_noop_sleep)
    session.refresh(task)
    assert task.status == TaskStatus.error.value
    assert task.attempts == 3
    assert "RuntimeError" in (task.error or "")


def test_run_one_unknown_type_terminal(session):
    task = _claimed(session, type="does_not_exist")
    worker.run_one(session, task, sleep=_noop_sleep)
    session.refresh(task)
    assert task.status == TaskStatus.error.value
    assert "unknown task type" in (task.error or "")


def test_run_one_validation_error_terminal(session, monkeypatch):
    class _M(BaseModel):
        x: int

    def bad(_payload):
        _M.model_validate({"x": "not-an-int"})  # raises ValidationError

    monkeypatch.setitem(worker.JOB_REGISTRY, "sync_accounts", bad)
    task = _claimed(session)

    worker.run_one(session, task, max_attempts=5, backoff_sec=0, sleep=_noop_sleep)
    session.refresh(task)
    assert task.status == TaskStatus.error.value
    assert task.attempts == 1  # terminal, no retry
