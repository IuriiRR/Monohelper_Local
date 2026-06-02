"""Scheduled task enqueuer.

Called from the worker poll loop. For each configured job, enqueues
the task once per day when the scheduled time has been reached.

Idempotency: skips if a non-error task of the same type was created at or
after today's scheduled time. Manual runs earlier in the day do NOT block
the scheduled run.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from models import Task, TaskStatus
from services.tasks import enqueue

logger = logging.getLogger(__name__)


@dataclass
class ScheduledJob:
    task_type: str
    scheduled_time: time  # naive time; compared in the configured TZ


def check_and_enqueue(session: Session, jobs: list[ScheduledJob], tz: ZoneInfo) -> None:
    """Enqueue any jobs whose scheduled time has arrived and haven't run since."""
    if not jobs:
        return
    now = datetime.now(tz)
    for job in jobs:
        if now.time() < job.scheduled_time:
            continue
        # Naive UTC cutoff: today at the scheduled time.
        # Only tasks created at/after this point count — manual earlier runs don't block.
        scheduled_since = now.replace(
            hour=job.scheduled_time.hour,
            minute=job.scheduled_time.minute,
            second=0, microsecond=0,
        ).astimezone(timezone.utc).replace(tzinfo=None)
        existing = session.exec(
            select(Task).where(
                Task.type == job.task_type,
                Task.status != TaskStatus.error.value,
                Task.created_at >= scheduled_since,
            )
        ).first()
        if existing:
            continue
        enqueue(session, job.task_type)
        logger.info("scheduler: enqueued %s", job.task_type)
