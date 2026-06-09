from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from database import get_session
from models import Account

router = APIRouter()


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    type: str
    send_id: str | None
    currency_code: int
    balance: int
    is_active: bool
    title: str | None
    goal: int | None
    is_budget: bool
    invested: int
    created_at: datetime
    updated_at: datetime
    owner_username: str | None = None


class AccountsResponse(BaseModel):
    accounts: list[AccountOut]


@router.get("/", response_model=AccountsResponse)
def list_accounts(
    user_id: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> AccountsResponse:
    q = select(Account).options(selectinload(Account.user))  # type: ignore[arg-type]
    if user_id:
        q = q.where(Account.user_id == user_id)
    accounts = session.exec(q).all()
    account_outs = [AccountOut(**a.model_dump(), owner_username=a.user.username if a.user else None) for a in accounts]
    return AccountsResponse(accounts=account_outs)
