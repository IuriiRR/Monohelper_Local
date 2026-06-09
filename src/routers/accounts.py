from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models import Account

router = APIRouter()


class AccountsResponse(BaseModel):
    accounts: list[Account]


@router.get("/", response_model=AccountsResponse)
def list_accounts(
    user_id: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> AccountsResponse:
    q = select(Account)
    if user_id:
        q = q.where(Account.user_id == user_id)
    accounts = session.exec(q).all()
    return AccountsResponse(accounts=list(accounts))
