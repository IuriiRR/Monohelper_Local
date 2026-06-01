from typing import Any, Dict, Optional

from sqlmodel import Session

import database
from services.sync_service import sync_accounts as _sync_accounts


def run(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # database.engine read at call time so tests can monkeypatch the engine.
    with Session(database.engine) as session:
        return _sync_accounts(session=session)
