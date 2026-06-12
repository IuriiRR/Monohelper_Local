"""Standalone FastAPI CI/CD deploy service for Monohelper_Local.

A separate process (``python -m deploy``, uvicorn on 127.0.0.1:8089) that pulls the
latest code, reinstalls deps, rebuilds the SPA, and restarts the two systemd units,
exposing a small dashboard + REST API to trigger and track deployments. Kept separate
from the main app so it stays up while it restarts the app and worker.
"""
