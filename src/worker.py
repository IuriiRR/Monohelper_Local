"""Background worker: consumes the DB-backed task queue and runs sync jobs.

Single sequential worker (Monobank's 1-minute cooldown forces serialization).
Run via ``make worker``, ``python -m worker``, or the ``monohelper-worker``
console script. Stops gracefully on SIGTERM/SIGINT, finishing the in-flight
task first.
"""
import logging
import os
import signal
import threading
import traceback
from datetime import datetime, time, timedelta, timezone
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from pydantic import ValidationError
from sqlmodel import Session

import database
from jobs import JOB_REGISTRY
from logging_config import setup_logging
from models import Task
from scheduler import ScheduledJob, check_and_enqueue
from services.tasks import (
    claim_next,
    complete,
    fail,
    mark_running_attempt,
    requeue_orphans,
)

logger = logging.getLogger("worker")

# Set by signal handlers; checked only between tasks and between retries so an
# in-flight Monobank sync is never interrupted mid-run.
_shutdown = threading.Event()


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


POLL_INTERVAL = _env_float("WORKER_POLL_INTERVAL", 2.0)
RETRY_BACKOFF_SEC = _env_float("WORKER_RETRY_BACKOFF_SEC", 60.0)
MAX_ATTEMPTS = _env_int("WORKER_MAX_ATTEMPTS", 15)
TASK_DEADLINE_SEC = _env_float("WORKER_TASK_DEADLINE_SEC", 900.0)


def _parse_schedule(accounts_str: str, transactions_str: str, tz_str: str) -> tuple[list[ScheduledJob], ZoneInfo]:
    tz = ZoneInfo(tz_str)
    jobs: list[ScheduledJob] = []
    for task_type, raw in (("sync_accounts", accounts_str), ("sync_transactions", transactions_str)):
        if not raw:
            continue
        h, m = raw.strip().split(":")
        jobs.append(ScheduledJob(task_type=task_type, scheduled_time=time(int(h), int(m))))
    return jobs, tz


def _default_sleep(seconds: float) -> None:
    # Interruptible: returns early when shutdown is requested.
    _shutdown.wait(seconds)


def run_one(
    session: Session,
    task: Task,
    *,
    max_attempts: int = MAX_ATTEMPTS,
    backoff_sec: float = RETRY_BACKOFF_SEC,
    deadline_sec: float = TASK_DEADLINE_SEC,
    sleep: Optional[Callable[[float], None]] = None,
) -> None:
    """Run a claimed task with bounded retries.

    Retries runtime/HTTP errors with ``backoff_sec`` (Monobank cooldown) until
    ``max_attempts`` or ``deadline_sec`` is hit, then dead-letters (status=error).
    Validation / unknown-type errors are terminal immediately (no retry).
    Shutdown is honored between retries (leaves the task running → requeued)."""
    if sleep is None:
        sleep = _default_sleep

    task_id = task.id
    task_type = task.type
    payload = task.payload

    handler = JOB_REGISTRY.get(task_type)
    if handler is None:
        fail(session, task_id, f"unknown task type: {task_type}")
        logger.error("task #%s: unknown type %r", task_id, task_type)
        return

    deadline = datetime.now(timezone.utc) + timedelta(seconds=deadline_sec)

    while True:
        attempt = mark_running_attempt(session, task_id)
        logger.info("task #%s (%s): attempt %d", task_id, task_type, attempt)
        try:
            result = handler(payload)
            complete(session, task_id, result)
            logger.info("task #%s success", task_id)
            return
        except ValidationError:
            tb = traceback.format_exc()
            logger.error("task #%s invalid payload (terminal):\n%s", task_id, tb)
            fail(session, task_id, tb)
            return
        except Exception:
            tb = traceback.format_exc()
            logger.error("task #%s failed on attempt %d:\n%s", task_id, attempt, tb)
            exhausted = attempt >= max_attempts
            past_deadline = (
                datetime.now(timezone.utc) + timedelta(seconds=backoff_sec) >= deadline
            )
            if exhausted or past_deadline or _shutdown.is_set():
                fail(session, task_id, tb)
                logger.error(
                    "task #%s dead-lettered (attempts=%d, exhausted=%s, "
                    "past_deadline=%s, shutdown=%s)",
                    task_id, attempt, exhausted, past_deadline, _shutdown.is_set(),
                )
                return
            logger.info(
                "task #%s: retrying in %.0fs (Monobank cooldown)", task_id, backoff_sec
            )
            sleep(backoff_sec)


def _install_signal_handlers() -> None:
    def _handle(signum, _frame):
        logger.info("received signal %s, shutting down after current task", signum)
        _shutdown.set()

    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)


def run_loop(
    jobs: Optional[list[ScheduledJob]] = None,
    tz: Optional[ZoneInfo] = None,
) -> None:
    """Poll the queue until shutdown is requested."""
    with Session(database.engine) as session:
        requeued = requeue_orphans(session)
    if requeued:
        logger.info("requeued %d orphaned running task(s)", requeued)

    logger.info(
        "worker started (poll=%.1fs, backoff=%.0fs, max_attempts=%d, deadline=%.0fs)",
        POLL_INTERVAL, RETRY_BACKOFF_SEC, MAX_ATTEMPTS, TASK_DEADLINE_SEC,
    )

    while not _shutdown.is_set():
        with Session(database.engine) as session:
            task = claim_next(session)
            if task is not None:
                run_one(session, task)
            else:
                if jobs and tz:
                    check_and_enqueue(session, jobs, tz)
                _shutdown.wait(POLL_INTERVAL)

    logger.info("worker stopped gracefully")


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))
    database.create_db_and_tables()  # worker may start before the web process
    _install_signal_handlers()
    jobs, tz = _parse_schedule(
        os.getenv("SCHEDULE_ACCOUNTS_TIME", ""),
        os.getenv("SCHEDULE_TRANSACTIONS_TIME", ""),
        os.getenv("SCHEDULE_TZ", "Europe/Kyiv"),
    )
    if jobs:
        logger.info(
            "scheduler: %d job(s) configured (tz=%s): %s",
            len(jobs), tz.key, [(j.task_type, j.scheduled_time.strftime("%H:%M")) for j in jobs],
        )
    run_loop(jobs=jobs, tz=tz)


if __name__ == "__main__":
    main()
