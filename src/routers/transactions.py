from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models import Transaction

router = APIRouter()


class TransactionsResponse(BaseModel):
    transactions: list[Transaction]


@router.get("/", response_model=TransactionsResponse)
def list_transactions(
    user_id: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    limit: int = Query(default=100, le=1000),
    session: Session = Depends(get_session),
) -> TransactionsResponse:
    q = select(Transaction).order_by(Transaction.time.desc())  # type: ignore[attr-defined]
    if user_id:
        q = q.where(Transaction.user_id == user_id)
    if account_id:
        q = q.where(Transaction.account_id == account_id)
    q = q.limit(limit)
    transactions = session.exec(q).all()
    return TransactionsResponse(transactions=list(transactions))
