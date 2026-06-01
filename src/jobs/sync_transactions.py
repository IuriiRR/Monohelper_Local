from typing import Any, Dict

from config import Settings
from database import Session, engine
from routers.sync import SyncTransactionsRequest
from routers.sync import sync_transactions as _do_sync_transactions


def run_for_user(settings: Settings, payload: Dict[str, Any]) -> dict:
    req = SyncTransactionsRequest.model_validate(payload)
    with Session(engine) as session:
        return _do_sync_transactions(body=req, session=session)
