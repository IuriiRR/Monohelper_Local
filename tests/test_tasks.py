"""Task queue helper tests."""
from models import Task, TaskStatus
from services.tasks import (
    claim_next,
    complete,
    enqueue,
    fail,
    mark_running_attempt,
    recent,
    requeue_orphans,
)


def test_enqueue_creates_pending(session):
    task = enqueue(session, "sync_accounts", {})
    assert task.id is not None
    assert task.status == TaskStatus.pending.value
    assert task.payload == {}


def test_enqueue_dedupes_identical_pending(session):
    a = enqueue(session, "sync_accounts", {})
    b = enqueue(session, "sync_accounts", {})
    assert a.id == b.id

    c = enqueue(session, "sync_transactions", {"days": 7})
    d = enqueue(session, "sync_transactions", {"days": 30})
    assert c.id != d.id  # different payload → distinct task


def test_claim_next_oldest_first_and_running(session):
    first = enqueue(session, "sync_accounts", {})
    enqueue(session, "sync_transactions", {"days": 1})

    claimed = claim_next(session)
    assert claimed.id == first.id
    assert claimed.status == TaskStatus.running.value
    assert claimed.started_at is not None


def test_claim_next_empty_returns_none(session):
    assert claim_next(session) is None


def test_mark_attempt_increments(session):
    task = enqueue(session, "sync_accounts", {})
    assert mark_running_attempt(session, task.id) == 1
    assert mark_running_attempt(session, task.id) == 2


def test_complete_and_fail(session):
    t1 = enqueue(session, "sync_accounts", {})
    complete(session, t1.id, {"status": "success"})
    session.refresh(t1)
    assert t1.status == TaskStatus.success.value
    assert t1.result == {"status": "success"}
    assert t1.finished_at is not None

    t2 = enqueue(session, "sync_transactions", {"days": 1})
    fail(session, t2.id, "boom")
    session.refresh(t2)
    assert t2.status == TaskStatus.error.value
    assert t2.error == "boom"
    assert t2.finished_at is not None


def test_requeue_orphans(session):
    task = enqueue(session, "sync_accounts", {})
    claim_next(session)  # → running
    session.refresh(task)
    assert task.status == TaskStatus.running.value

    n = requeue_orphans(session)
    assert n == 1
    session.refresh(task)
    assert task.status == TaskStatus.pending.value
    assert task.started_at is None


def test_recent_filter(session):
    enqueue(session, "sync_accounts", {})
    t2 = enqueue(session, "sync_transactions", {"days": 1})
    fail(session, t2.id, "x")

    assert len(recent(session)) == 2
    errored = recent(session, status=TaskStatus.error.value)
    assert len(errored) == 1
    assert errored[0].id == t2.id
