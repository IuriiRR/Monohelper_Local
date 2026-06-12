"""Unit tests for deploy.config.load_settings."""

from deploy.config import DEFAULT_HEALTHCHECK_URL, load_settings

_VARS = ["DEPLOY_TOKEN", "GITHUB_WEBHOOK_SECRET", "APP_DIR", "DEPLOY_BRANCH", "HEALTHCHECK_URL"]


def test_defaults_when_unset(monkeypatch):
    for var in _VARS:
        monkeypatch.delenv(var, raising=False)
    s = load_settings()
    assert s.deploy_token == ""
    assert s.github_webhook_secret == ""
    assert s.deploy_branch == "main"
    assert s.healthcheck_url == DEFAULT_HEALTHCHECK_URL
    assert s.app_dir  # repo root, non-empty


def test_env_override_and_strip(monkeypatch):
    monkeypatch.setenv("DEPLOY_TOKEN", "  tok  ")
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cr3t")
    monkeypatch.setenv("DEPLOY_BRANCH", "release")
    monkeypatch.setenv("HEALTHCHECK_URL", "http://example/health")
    s = load_settings()
    assert s.deploy_token == "tok"
    assert s.github_webhook_secret == "s3cr3t"
    assert s.deploy_branch == "release"
    assert s.healthcheck_url == "http://example/health"
