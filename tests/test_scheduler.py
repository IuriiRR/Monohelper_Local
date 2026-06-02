from datetime import datetime, time
from unittest.mock import patch
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from models import Task, TaskStatus
from scheduler import ScheduledJob, check_and_enqueue

TZ = ZoneInfo("Europe/Kyiv")


def test_check_and_enqueue_noop_empty_jobs(session: Session) -> None:
    check_and_enqueue(session, [], TZ)
    assert session.exec(select(Task)).all() == []


def test_check_and_enqueue_before_scheduled_time(session: Session) -> None:
    job = ScheduledJob(task_type="sync_accounts", scheduled_time=time(23, 59))
    fake_now = datetime(2024, 1, 1, 10, 0, tzinfo=TZ)
    with patch("scheduler.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        check_and_enqueue(session, [job], TZ)
    assert session.exec(select(Task)).all() == []


def test_check_and_enqueue_enqueues_after_scheduled_time(session: Session) -> None:
    job = ScheduledJob(task_type="sync_accounts", scheduled_time=time(8, 0))
    fake_now = datetime(2024, 1, 1, 9, 0, tzinfo=TZ)
    with patch("scheduler.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        check_and_enqueue(session, [job], TZ)
    tasks = session.exec(select(Task)).all()
    assert len(tasks) == 1
    assert tasks[0].type == "sync_accounts"
    assert tasks[0].status == TaskStatus.pending.value


def test_check_and_enqueue_idempotent(session: Session) -> None:
    job = ScheduledJob(task_type="sync_accounts", scheduled_time=time(8, 0))
    fake_now = datetime(2024, 1, 1, 9, 0, tzinfo=TZ)
    with patch("scheduler.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        check_and_enqueue(session, [job], TZ)
        check_and_enqueue(session, [job], TZ)
    tasks = session.exec(select(Task)).all()
    assert len(tasks) == 1
