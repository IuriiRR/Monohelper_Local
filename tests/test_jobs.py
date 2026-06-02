"""Job dispatch registry tests.

Handlers open ``Session(database.engine)``; the ``session`` fixture points that
engine at the in-memory test DB, so we only need to monkeypatch Monobank HTTP.
"""

from jobs import JOB_REGISTRY


class _Resp:
    def __init__(self, payload, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code
        self.text = ""

    def json(self):
        return self._payload


def test_registry_has_expected_types():
    assert set(JOB_REGISTRY) == {"sync_accounts", "sync_transactions"}


def test_sync_accounts_handler(session, monkeypatch):
    from models import User

    session.add(User(user_id="u1", mono_token="tok", active=True))
    session.commit()

    def fake_get(url, headers=None, timeout=None):
        return _Resp({"accounts": [{"id": "acc1", "currencyCode": 980, "balance": 100, "sendId": "s"}], "jars": []})

    monkeypatch.setattr("services.sync_service.requests.get", fake_get)

    result = JOB_REGISTRY["sync_accounts"]({})
    assert result["status"] == "success"
    assert result["processed_users"] == 1
    assert result["total_accounts_synced"] == 1


def test_sync_transactions_handler(session, monkeypatch):
    from models import Account, User

    session.add(User(user_id="u1", mono_token="tok", active=True))
    session.add(Account(id="acc1", user_id="u1", type="card", balance=0))
    session.commit()

    def fake_get(url, headers=None, timeout=None):
        return _Resp([{"id": "tx1", "time": 1700000000, "amount": -500, "balance": 9500}])

    monkeypatch.setattr("services.sync_service.requests.get", fake_get)
    monkeypatch.setattr("services.sync_service.time.sleep", lambda *_: None)

    result = JOB_REGISTRY["sync_transactions"]({"days": 7})
    assert result["status"] == "success"
    assert result["total_transactions_synced"] == 1
