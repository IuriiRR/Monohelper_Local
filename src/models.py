from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    username: str | None = None
    mono_token: str
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    accounts: list["Account"] = Relationship(back_populates="user")


class Account(SQLModel, table=True):
    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.user_id")
    type: str = Field(default="jar")  # "jar" or "card"
    send_id: str | None = None
    currency_code: int = Field(default=980)  # UAH
    balance: int = Field(default=0)
    is_active: bool = Field(default=True)

    # Jar specific fields
    title: str | None = None
    goal: int | None = None
    is_budget: bool = Field(default=False)
    invested: int = Field(default=0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: User | None = Relationship(back_populates="accounts")
    transactions: list["Transaction"] = Relationship(back_populates="account")


class Transaction(SQLModel, table=True):
    id: str = Field(primary_key=True)
    account_id: str = Field(foreign_key="account.id")
    user_id: str = Field(index=True)  # Redundant for fast querying by user
    time: int = Field(index=True)
    description: str | None = None
    amount: int
    operation_amount: int | None = None
    commission_rate: int | None = None
    cashback_amount: int | None = None
    balance: int
    hold: bool = Field(default=False)
    comment: str | None = None
    mcc_code: int | None = None
    original_mcc: int | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    account: Account | None = Relationship(back_populates="transactions")


class TaskStatus(StrEnum):
    pending = "pending"
    running = "running"
    success = "success"
    error = "error"


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    type: str = Field(index=True)  # "sync_accounts" | "sync_transactions"
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    status: str = Field(default=TaskStatus.pending.value, index=True)
    result: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    error: str | None = None  # traceback text on dead-letter
    attempts: int = Field(default=0)  # handler invocations (incl. retries)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None
