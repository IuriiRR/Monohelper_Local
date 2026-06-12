"""Unit tests for the deploy executor (deploy.runner)."""

import time

from deploy import runner
from deploy.models import DeployRun, DeployStatus
from deploy.runner import Step


def _make_run(session, **kw) -> DeployRun:
    run = DeployRun(**kw)
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def _reload(session, run_id: int) -> DeployRun:
    session.expire_all()
    run = session.get(DeployRun, run_id)
    assert run is not None
    return run


def test_run_deploy_success(session, monkeypatch):
    run = _make_run(session)
    monkeypatch.setattr(runner, "_git_sha", lambda app_dir: "deadbeef")
    monkeypatch.setattr(runner, "_run_command", lambda step, app_dir: (0, f"ran {step.name}\n"))
    monkeypatch.setattr(runner, "_run_healthcheck", lambda url: (True, "200 ok\n"))

    runner.run_deploy(run.id)

    updated = _reload(session, run.id)
    assert updated.status == DeployStatus.success.value
    assert updated.git_after == "deadbeef"
    assert updated.finished_at is not None
    # six command steps + healthcheck
    assert len(updated.steps) == 7
    assert updated.steps[-1]["name"] == "healthcheck"
    assert all(s["status"] == "success" for s in updated.steps)


def test_run_deploy_stops_on_first_failure(session, monkeypatch):
    run = _make_run(session)
    calls = {"n": 0}

    def fake_cmd(step, app_dir):
        calls["n"] += 1
        return (0 if calls["n"] == 1 else 2), f"{step.name}\n"

    def fail_if_called(url):
        raise AssertionError("healthcheck must not run after a failed step")

    monkeypatch.setattr(runner, "_git_sha", lambda app_dir: "x")
    monkeypatch.setattr(runner, "_run_command", fake_cmd)
    monkeypatch.setattr(runner, "_run_healthcheck", fail_if_called)

    runner.run_deploy(run.id)

    updated = _reload(session, run.id)
    assert updated.status == DeployStatus.error.value
    assert len(updated.steps) == 2
    assert updated.steps[1]["status"] == "error"
    assert "exited 2" in (updated.error or "")


def test_run_deploy_healthcheck_failure(session, monkeypatch):
    run = _make_run(session)
    monkeypatch.setattr(runner, "_git_sha", lambda app_dir: "x")
    monkeypatch.setattr(runner, "_run_command", lambda step, app_dir: (0, ""))
    monkeypatch.setattr(runner, "_run_healthcheck", lambda url: (False, "no 200\n"))

    runner.run_deploy(run.id)

    updated = _reload(session, run.id)
    assert updated.status == DeployStatus.error.value
    assert updated.error == "healthcheck failed"
    assert updated.steps[-1]["name"] == "healthcheck"
    assert updated.steps[-1]["status"] == "error"


def test_run_deploy_missing_run_is_noop(session):
    # Should log and return without raising.
    runner.run_deploy(999999)


def test_recover_orphans_resets_active_runs(session):
    r_running = _make_run(session, status=DeployStatus.running.value)
    r_pending = _make_run(session, status=DeployStatus.pending.value)
    r_done = _make_run(session, status=DeployStatus.success.value)

    reset = runner.recover_orphans()

    assert reset == 2
    assert _reload(session, r_running.id).status == DeployStatus.interrupted.value
    assert _reload(session, r_pending.id).status == DeployStatus.interrupted.value
    assert _reload(session, r_done.id).status == DeployStatus.success.value


def test_start_deploy_single_flight(session):
    # Hold the lock => start_deploy should refuse.
    assert runner._deploy_lock.acquire(blocking=False)
    try:
        assert runner.start_deploy("manual") is None
    finally:
        runner._deploy_lock.release()


def test_start_deploy_launches_thread_and_releases_lock(session, monkeypatch):
    ran = {"id": None}

    def fake_run(run_id):
        ran["id"] = run_id

    monkeypatch.setattr(runner, "run_deploy", fake_run)

    run_id = runner.start_deploy("manual")
    assert run_id is not None

    # Wait for the daemon thread to finish and release the lock.
    for _ in range(100):
        if runner._deploy_lock.acquire(blocking=False):
            runner._deploy_lock.release()
            break
        time.sleep(0.02)
    else:
        raise AssertionError("deploy lock was not released")
    assert ran["id"] == run_id


# --- low-level helpers (real subprocess, no mocking) ---


def test_run_command_success(tmp_path):
    code, log = runner._run_command(Step("echo", ["echo", "hello"]), str(tmp_path))
    assert code == 0
    assert "hello" in log


def test_run_command_nonzero_exit(tmp_path):
    code, _ = runner._run_command(Step("false", ["false"]), str(tmp_path))
    assert code != 0


def test_run_command_launch_failure(tmp_path):
    code, log = runner._run_command(Step("missing", ["definitely-not-a-real-binary-xyz"]), str(tmp_path))
    assert code == 1
    assert "failed to launch" in log


def test_git_sha_in_repo():
    sha = runner._git_sha(".")
    assert sha is not None
    assert len(sha) == 40


def test_git_sha_outside_repo(tmp_path):
    assert runner._git_sha(str(tmp_path)) is None


class _Resp:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


def test_healthcheck_success(monkeypatch):
    monkeypatch.setattr(runner.time, "sleep", lambda _s: None)
    monkeypatch.setattr(runner.requests, "get", lambda url, timeout: _Resp(200))
    ok, log = runner._run_healthcheck("http://x/health")
    assert ok
    assert "200" in log


def test_healthcheck_failure(monkeypatch):
    monkeypatch.setattr(runner.time, "sleep", lambda _s: None)

    def boom(url, timeout):
        raise runner.requests.RequestException("connection refused")

    monkeypatch.setattr(runner.requests, "get", boom)
    ok, log = runner._run_healthcheck("http://x/health")
    assert not ok
    assert "error" in log
