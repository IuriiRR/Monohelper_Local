"""Sync endpoints. These no longer run the sync inline — they enqueue a task
that the background worker picks up, and return 202 immediately.
"""

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from database import get_session
from services.sync_service import SyncTransactionsRequest
from services.tasks import enqueue

router = APIRouter()


@router.post("/accounts", status_code=status.HTTP_202_ACCEPTED)
def enqueue_sync_accounts(session: Session = Depends(get_session)):
    task = enqueue(session, type="sync_accounts", payload={})
    return {"task_id": task.id, "status": "queued"}


@router.post("/transactions", status_code=status.HTTP_202_ACCEPTED)
def enqueue_sync_transactions(
    body: SyncTransactionsRequest = SyncTransactionsRequest(),
    session: Session = Depends(get_session),
):
    task = enqueue(session, type="sync_transactions", payload=body.model_dump())
    return {"task_id": task.id, "status": "queued"}
