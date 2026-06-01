from typing import Any, Dict

from config import Settings
from database import Session, engine
from routers.sync import sync_accounts as _do_sync_accounts


def run(settings: Settings) -> Dict[str, Any]:
    with Session(engine) as session:
        return _do_sync_accounts(session=session)
