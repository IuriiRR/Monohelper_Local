"""Deploy-run persistence model.

A ``DeployRun`` row is the durable record of one deployment: its trigger, status,
the commit it moved from/to, per-step results, accumulated log, and timestamps.
Mirrors the conventions of ``Task`` in ``src/models.py`` (JSON columns, UTC timestamps).
"""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class DeployStatus(StrEnum):
    pending = "pending"
    running = "running"
    success = "success"
    error = "error"
    interrupted = "interrupted"  # process died mid-deploy; reset on next startup


class DeployRun(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    trigger: str = Field(default="manual")  # "manual" | "webhook"
    status: str = Field(default=DeployStatus.pending.value, index=True)
    git_before: str | None = None  # HEAD sha before `git pull`
    git_after: str | None = None  # HEAD sha after `git pull`
    # Per-step results: [{"name": str, "status": "success"|"error", "exit_code": int}]
    steps: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    log: str = Field(default="")  # concatenated stdout/stderr of every step
    error: str | None = None  # short failure reason when status == error

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None
