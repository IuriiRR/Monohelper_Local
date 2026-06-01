from config import Settings
from jobs import sync_accounts


def _settings() -> Settings:
    return Settings(internal_api_key="k")


def test_sync_accounts_job_calls_function_directly(monkeypatch):
    mock_result = {
        "status": "success",
        "processed_users": 1,
        "total_accounts_synced": 2,
        "errors": [],
    }
    monkeypatch.setattr("jobs.sync_accounts._do_sync_accounts", lambda session: mock_result)

    result = sync_accounts.run(_settings())
    assert result["status"] == "success"
    assert result["processed_users"] == 1
