from typing import Any

from sqlmodel import Session

import database
from services.sync_service import SyncTransactionsRequest
from services.sync_service import sync_transactions as _sync_transactions


def run(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    req = SyncTransactionsRequest.model_validate(payload or {})
    # database.engine read at call time so tests can monkeypatch the engine.
    with Session(database.engine) as session:
        return _sync_transactions(body=req, session=session)
