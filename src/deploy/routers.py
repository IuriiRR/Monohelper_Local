"""HTTP API for the deploy service.

- ``POST /deploy``            trigger a manual deploy (requires ``X-Deploy-Token``)
- ``GET  /deploys``          recent deploy history
- ``GET  /deploys/{id}``     single deploy status + per-step results + log
- ``POST /webhook/github``   optional push-triggered deploy (HMAC-verified; disabled
                             unless ``GITHUB_WEBHOOK_SECRET`` is set)
"""

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import Session, col, select

from deploy import runner
from deploy.config import load_settings
from deploy.db import get_session
from deploy.models import DeployRun

logger = logging.getLogger(__name__)

router = APIRouter()


class DeployAccepted(BaseModel):
    run_id: int
    status: str


class DeploysResponse(BaseModel):
    deploys: list[DeployRun]


def _require_token(provided: str | None) -> None:
    expected = load_settings().deploy_token
    if not expected:
        raise HTTPException(status_code=503, detail="DEPLOY_TOKEN is not configured")
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="invalid or missing deploy token")


@router.post("/deploy", status_code=status.HTTP_202_ACCEPTED, response_model=DeployAccepted)
def trigger_deploy(x_deploy_token: str | None = Header(default=None)) -> DeployAccepted:
    _require_token(x_deploy_token)
    run_id = runner.start_deploy("manual")
    if run_id is None:
        raise HTTPException(status_code=409, detail="a deploy is already running")
    return DeployAccepted(run_id=run_id, status="queued")


@router.get("/deploys", response_model=DeploysResponse)
def list_deploys(limit: int = 20, session: Session = Depends(get_session)) -> DeploysResponse:
    limit = max(1, min(limit, 100))
    rows = session.exec(select(DeployRun).order_by(col(DeployRun.id).desc()).limit(limit)).all()
    return DeploysResponse(deploys=list(rows))


@router.get("/deploys/{run_id}", response_model=DeployRun)
def get_deploy(run_id: int, session: Session = Depends(get_session)) -> DeployRun:
    run = session.get(DeployRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"deploy {run_id} not found")
    return run


@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
) -> dict[str, object]:
    settings = load_settings()
    secret = settings.github_webhook_secret
    if not secret:
        # Endpoint is inert until a secret is configured.
        raise HTTPException(status_code=404, detail="webhook disabled")

    body = await request.body()
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not x_hub_signature_256 or not hmac.compare_digest(x_hub_signature_256, expected):
        raise HTTPException(status_code=401, detail="invalid signature")

    if x_github_event == "ping":
        return {"status": "pong"}
    if x_github_event != "push":
        return {"status": "ignored", "event": x_github_event}

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid JSON payload") from None

    ref = payload.get("ref", "")
    if ref != f"refs/heads/{settings.deploy_branch}":
        return {"status": "ignored", "ref": ref}

    run_id = runner.start_deploy("webhook")
    if run_id is None:
        raise HTTPException(status_code=409, detail="a deploy is already running")
    return {"status": "queued", "run_id": run_id}
