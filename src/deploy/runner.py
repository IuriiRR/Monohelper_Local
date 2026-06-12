"""Deploy executor: runs one deployment at a time in a background thread.

Mirrors the spirit of the main app's worker (a single in-flight unit of work, durable
status in SQLite, orphan recovery on startup) but without a second process: deploys are
infrequent and serialized, so a module-level lock + a daemon thread is enough.

Each deploy walks an ordered list of shell steps (pull, install, build, restart) and a
final HTTP health check, appending per-step results and combined output to the
``DeployRun`` row so the UI can poll progress. Stops at the first failing step.

Security: every command is a fixed argv list (never ``shell=True``, no string
interpolation of untrusted input). ``sudo`` is limited by a narrow sudoers rule to the
two ``systemctl restart`` commands (see ``systemd/cloudapi-deploy.sudoers``).
"""

import logging
import os

# Fixed argv commands, no shell, no untrusted input (see module docstring).
import subprocess  # nosec B404
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime

import requests
from sqlmodel import Session, col, select

from deploy import db
from deploy.config import load_settings
from deploy.models import DeployRun, DeployStatus

logger = logging.getLogger(__name__)

COMMAND_TIMEOUT_SEC = 600  # per-step hard cap (npm ci is the slow one on a Pi)
HEALTHCHECK_RETRIES = 20
HEALTHCHECK_INTERVAL_SEC = 3.0
HEALTHCHECK_TIMEOUT_SEC = 5.0

# Only ever one deploy at a time. Held for the lifetime of the executor thread.
_deploy_lock = threading.Lock()


@dataclass(frozen=True)
class Step:
    name: str
    argv: list[str]
    subdir: str = ""  # relative to app_dir; "" means app_dir itself


def _steps() -> list[Step]:
    """Ordered deploy steps. Restarts target the app + worker, never this service."""
    return [
        Step("git pull", ["git", "pull", "--ff-only"]),
        Step("install python deps", ["uv", "pip", "install", "-e", ".[test]", "--python", ".venv/bin/python"]),
        Step("npm ci", ["npm", "ci"], subdir="frontend"),
        Step("npm build", ["npm", "run", "build"], subdir="frontend"),
        Step("restart server", ["sudo", "systemctl", "restart", "cloudapi-local.service"]),
        Step("restart worker", ["sudo", "systemctl", "restart", "cloudapi-worker.service"]),
    ]


def _git_sha(app_dir: str) -> str | None:
    try:
        proc = subprocess.run(  # nosec B603 B607
            ["git", "rev-parse", "HEAD"],
            cwd=app_dir,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return proc.stdout.strip() or None if proc.returncode == 0 else None


def _run_command(step: Step, app_dir: str) -> tuple[int, str]:
    """Run one step, returning (exit_code, log_chunk). Never raises."""
    cwd = os.path.join(app_dir, step.subdir) if step.subdir else app_dir
    header = f"$ {' '.join(step.argv)}  (cwd={cwd})\n"
    try:
        proc = subprocess.run(  # nosec B603 B607
            step.argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        return 124, f"{header}[timed out after {COMMAND_TIMEOUT_SEC}s]\n"
    except (subprocess.SubprocessError, OSError) as exc:
        return 1, f"{header}[failed to launch: {exc}]\n"
    return proc.returncode, header + proc.stdout + proc.stderr


def _run_healthcheck(url: str) -> tuple[bool, str]:
    """Poll the app health endpoint until it returns 200 or retries are exhausted."""
    last = ""
    for attempt in range(1, HEALTHCHECK_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=HEALTHCHECK_TIMEOUT_SEC)
            if resp.status_code == 200:
                return True, f"GET {url} -> 200 (attempt {attempt})\n"
            last = f"GET {url} -> {resp.status_code} (attempt {attempt})\n"
        except requests.RequestException as exc:
            last = f"GET {url} -> error: {exc} (attempt {attempt})\n"
        time.sleep(HEALTHCHECK_INTERVAL_SEC)
    return False, last


def _append_step(run_id: int, name: str, exit_code: int, log_chunk: str) -> None:
    status = DeployStatus.success.value if exit_code == 0 else DeployStatus.error.value
    with Session(db.engine) as session:
        run = session.get(DeployRun, run_id)
        if run is None:
            return
        run.steps = [*run.steps, {"name": name, "status": status, "exit_code": exit_code}]
        run.log = run.log + log_chunk
        session.add(run)
        session.commit()


def _finish(
    run_id: int,
    status: DeployStatus,
    *,
    error: str | None = None,
    git_after: str | None = None,
) -> None:
    with Session(db.engine) as session:
        run = session.get(DeployRun, run_id)
        if run is None:
            return
        run.status = status.value
        run.error = error
        run.finished_at = datetime.now(UTC)
        if git_after is not None:
            run.git_after = git_after
        session.add(run)
        session.commit()


def run_deploy(run_id: int) -> None:
    """Execute the deploy steps for ``run_id``, persisting progress as it goes."""
    settings = load_settings()
    app_dir = settings.app_dir

    with Session(db.engine) as session:
        run = session.get(DeployRun, run_id)
        if run is None:
            logger.error("deploy run %s not found", run_id)
            return
        run.status = DeployStatus.running.value
        run.started_at = datetime.now(UTC)
        run.git_before = _git_sha(app_dir)
        session.add(run)
        session.commit()

    logger.info("deploy %s started (app_dir=%s)", run_id, app_dir)

    for step in _steps():
        exit_code, log_chunk = _run_command(step, app_dir)
        _append_step(run_id, step.name, exit_code, log_chunk)
        if exit_code != 0:
            _finish(
                run_id,
                DeployStatus.error,
                error=f"step '{step.name}' exited {exit_code}",
                git_after=_git_sha(app_dir),
            )
            logger.warning("deploy %s failed at step '%s' (exit %s)", run_id, step.name, exit_code)
            return

    ok, hc_log = _run_healthcheck(settings.healthcheck_url)
    _append_step(run_id, "healthcheck", 0 if ok else 1, hc_log)
    git_after = _git_sha(app_dir)
    if ok:
        _finish(run_id, DeployStatus.success, git_after=git_after)
        logger.info("deploy %s succeeded", run_id)
    else:
        _finish(run_id, DeployStatus.error, error="healthcheck failed", git_after=git_after)
        logger.warning("deploy %s: healthcheck failed", run_id)


def _run_and_release(run_id: int) -> None:
    try:
        run_deploy(run_id)
    finally:
        _deploy_lock.release()


def start_deploy(trigger: str) -> int | None:
    """Create a deploy run and launch it in a background thread.

    Returns the new run id, or ``None`` if a deploy is already in progress.
    """
    if not _deploy_lock.acquire(blocking=False):
        return None
    try:
        with Session(db.engine) as session:
            run = DeployRun(trigger=trigger, status=DeployStatus.pending.value)
            session.add(run)
            session.commit()
            session.refresh(run)
            run_id = run.id
    except Exception:
        _deploy_lock.release()
        raise

    assert run_id is not None
    thread = threading.Thread(target=_run_and_release, args=(run_id,), daemon=True, name=f"deploy-{run_id}")
    thread.start()
    return run_id


def recover_orphans() -> int:
    """Mark deploys left ``pending``/``running`` by a crash as ``interrupted``.

    Called once at startup. Returns the number of rows reset.
    """
    active = (DeployStatus.pending.value, DeployStatus.running.value)
    now = datetime.now(UTC)
    with Session(db.engine) as session:
        rows = session.exec(select(DeployRun).where(col(DeployRun.status).in_(active))).all()
        for run in rows:
            run.status = DeployStatus.interrupted.value
            run.error = "interrupted: deploy service restarted mid-deploy"
            run.finished_at = now
            session.add(run)
        session.commit()
        return len(rows)
