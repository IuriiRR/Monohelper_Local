from fastapi.testclient import TestClient
from sqlmodel import Session

from models import Account, Transaction, User


def _seed_user(session: Session, user_id: str) -> None:
    session.add(User(user_id=user_id, mono_token="tok"))
    session.commit()


def _seed_account(session: Session, account_id: str, user_id: str) -> None:
    session.add(Account(id=account_id, user_id=user_id))
    session.commit()


def _seed_tx(session: Session, tx_id: str, account_id: str, user_id: str, time: int = 0) -> None:
    session.add(Transaction(id=tx_id, account_id=account_id, user_id=user_id, time=time, amount=100, balance=1000))
    session.commit()


def test_list_transactions_empty(client: TestClient) -> None:
    resp = client.get("/transactions/")
    assert resp.status_code == 200
    assert resp.json() == {"transactions": []}


def test_list_transactions_filter_user_id(client: TestClient, session: Session) -> None:
    _seed_user(session, "ua")
    _seed_user(session, "ub")
    _seed_account(session, "acc-a", "ua")
    _seed_account(session, "acc-b", "ub")
    _seed_tx(session, "tx1", "acc-a", "ua")
    _seed_tx(session, "tx2", "acc-b", "ub")

    resp = client.get("/transactions/", params={"user_id": "ua"})
    txs = resp.json()["transactions"]
    assert len(txs) == 1
    assert txs[0]["id"] == "tx1"


def test_list_transactions_filter_account_id(client: TestClient, session: Session) -> None:
    _seed_user(session, "uc")
    _seed_account(session, "acc-c1", "uc")
    _seed_account(session, "acc-c2", "uc")
    _seed_tx(session, "tx3", "acc-c1", "uc")
    _seed_tx(session, "tx4", "acc-c2", "uc")

    resp = client.get("/transactions/", params={"account_id": "acc-c1"})
    txs = resp.json()["transactions"]
    assert len(txs) == 1
    assert txs[0]["id"] == "tx3"


def test_list_transactions_limit(client: TestClient, session: Session) -> None:
    _seed_user(session, "ud")
    _seed_account(session, "acc-d", "ud")
    for i in range(5):
        _seed_tx(session, f"txL{i}", "acc-d", "ud", time=i)

    resp = client.get("/transactions/", params={"limit": 2})
    assert len(resp.json()["transactions"]) == 2
