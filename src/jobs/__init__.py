"""Task-type → handler registry consumed by the worker.

Each handler has the signature ``run(payload: dict) -> dict``. Task ``type``
strings stored in the queue must match these registry keys.
"""

from jobs import sync_accounts, sync_transactions

JOB_REGISTRY = {
    "sync_accounts": sync_accounts.run,
    "sync_transactions": sync_transactions.run,
}

__all__ = ["JOB_REGISTRY"]
