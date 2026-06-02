"""DB-backed task queue helpers.

A single worker consumes the ``task`` table. The web process enqueues; the
worker claims/updates. SQLite WAL + busy_timeout (see ``database.py``) make the
two-writer setup safe. All helpers take a ``Session`` and commit immediately to
keep transactions short.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import update
from sqlmodel import Session, select

from models import Task, TaskStatus

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def enqueue(session: Session, type: str, payload: dict | None = None) -> Task:
    """Insert a pending task. Dedupe: if an identical pending task (same type +
    payload) already exists, return it instead of stacking a backlog."""
    payload = payload or {}

    pending = session.exec(
        select(Task).where(
            Task.status == TaskStatus.pending.value,
            Task.type == type,
        )
    ).all()
    for existing in pending:
        if existing.payload == payload:
            logger.info("Dedupe: reusing pending task #%s (%s)", existing.id, type)
            return existing

    task = Task(type=type, payload=payload, status=TaskStatus.pending.value)
    session.add(task)
    session.commit()
    session.refresh(task)
    logger.info("Enqueued task #%s (%s)", task.id, type)
    return task


def claim_next(session: Session) -> Task | None:
    """Atomically claim the oldest pending task: flip it to running and return
    it. Single statement (UPDATE ... RETURNING) so it is race-free."""
    oldest_pending = (
        select(Task.id)
        .where(Task.status == TaskStatus.pending.value)
        .order_by(Task.created_at, Task.id)  # type: ignore[arg-type]
        .limit(1)
        .scalar_subquery()
    )
    stmt = (
        update(Task)
        .where(Task.id.in_(oldest_pending))  # type: ignore[union-attr]
        .values(status=TaskStatus.running.value, started_at=_now())
        .returning(Task.id)  # type: ignore[call-overload]
    )
    row = session.execute(stmt).first()
    session.commit()
    if row is None:
        return None
    return session.get(Task, row[0])


def mark_running_attempt(session: Session, task_id: int) -> int:
    """Increment the attempt counter for a task. Returns the new count."""
    task = session.get(Task, task_id)
    assert task is not None, f"task #{task_id} not found"
    task.attempts += 1
    session.add(task)
    session.commit()
    return task.attempts


def complete(session: Session, task_id: int, result: dict) -> None:
    task = session.get(Task, task_id)
    assert task is not None, f"task #{task_id} not found"
    task.status = TaskStatus.success.value
    task.result = result
    task.finished_at = _now()
    session.add(task)
    session.commit()


def fail(session: Session, task_id: int, error: str) -> None:
    task = session.get(Task, task_id)
    assert task is not None, f"task #{task_id} not found"
    task.status = TaskStatus.error.value
    task.error = error
    task.finished_at = _now()
    session.add(task)
    session.commit()


def requeue_orphans(session: Session) -> int:
    """Reset stale ``running`` tasks back to ``pending`` on worker startup.

    With a single worker, any task still ``running`` at startup was orphaned by
    a crash/restart. Sync is idempotent (``session.merge``), so re-running is
    safe. Returns the number requeued."""
    stmt = (
        update(Task)
        .where(Task.status == TaskStatus.running.value)  # type: ignore[arg-type]
        .values(status=TaskStatus.pending.value, started_at=None)
    )
    result = session.execute(stmt)
    session.commit()
    return result.rowcount or 0  # type: ignore[attr-defined]


def recent(session: Session, status: str | None = None, limit: int = 50) -> list[Task]:
    q = select(Task).order_by(Task.created_at.desc()).limit(limit)  # type: ignore[attr-defined]
    if status:
        q = q.where(Task.status == status)
    return list(session.exec(q).all())
