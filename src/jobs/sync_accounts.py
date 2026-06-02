from typing import Any

from sqlmodel import Session

import database
from services.sync_service import sync_accounts as _sync_accounts


def run(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    # database.engine read at call time so tests can monkeypatch the engine.
    with Session(database.engine) as session:
        return _sync_accounts(session=session)
