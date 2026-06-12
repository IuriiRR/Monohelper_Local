import pytest

from config import load_settings


def test_load_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("REPORT_TIMEZONE", raising=False)
    s = load_settings()
    assert s.internal_api_key == ""
    assert s.admin_password == ""
    assert s.report_timezone == "Europe/Kyiv"


def test_load_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_API_KEY", "  secret  ")
    monkeypatch.setenv("ADMIN_PASSWORD", "  adminpass  ")
    monkeypatch.setenv("REPORT_TIMEZONE", "UTC")
    s = load_settings()
    assert s.internal_api_key == "secret"
    assert s.admin_password == "adminpass"
    assert s.report_timezone == "UTC"
