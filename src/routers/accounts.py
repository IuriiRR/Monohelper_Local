from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from database import get_session
from models import Account

router = APIRouter()


@router.get("/")
def list_accounts(
    user_id: str | None = Query(default=None),
    session: Session = Depends(get_session),
):
    q = select(Account)
    if user_id:
        q = q.where(Account.user_id == user_id)
    accounts = session.exec(q).all()
    return {"accounts": accounts}
