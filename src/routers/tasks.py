"""Read-only task status endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session

from database import get_session
from models import Task
from services.tasks import recent

router = APIRouter()


class TasksResponse(BaseModel):
    tasks: list[Task]


@router.get("/", response_model=TasksResponse)
def list_tasks(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> TasksResponse:
    return TasksResponse(tasks=list(recent(session, status=status, limit=limit)))


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: int, session: Session = Depends(get_session)) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task
