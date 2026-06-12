"""Environment-driven settings for the deploy service.

Mirrors the shape of ``src/config.py``: a plain ``BaseModel`` plus a ``load_settings``
reader so callers always see the current environment (test-friendly, no frozen cache).
"""

import os
from pathlib import Path

from pydantic import BaseModel

# Repository root: src/deploy/config.py -> parents[2] == repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_HEALTHCHECK_URL = "http://127.0.0.1:8088/healthz"


class DeploySettings(BaseModel):
    deploy_token: str = ""  # required header value to trigger a manual deploy
    github_webhook_secret: str = ""  # empty => webhook endpoint disabled
    app_dir: str = str(_REPO_ROOT)  # working dir for git/uv/npm steps
    deploy_branch: str = "main"  # branch a webhook push must target
    healthcheck_url: str = DEFAULT_HEALTHCHECK_URL  # probed after restart


def load_settings() -> DeploySettings:
    return DeploySettings(
        deploy_token=(os.getenv("DEPLOY_TOKEN") or "").strip(),
        github_webhook_secret=(os.getenv("GITHUB_WEBHOOK_SECRET") or "").strip(),
        app_dir=(os.getenv("APP_DIR") or str(_REPO_ROOT)).strip(),
        deploy_branch=(os.getenv("DEPLOY_BRANCH") or "main").strip(),
        healthcheck_url=(os.getenv("HEALTHCHECK_URL") or DEFAULT_HEALTHCHECK_URL).strip(),
    )
