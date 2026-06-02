"""Central logging setup, shared by the web app and the worker.

Logs to stdout so systemd's journal (StandardOutput=journal) captures them.
"""

import logging
import sys

_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%dT%H:%M:%S%z"


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger. Idempotent: safe under uvicorn reload."""
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
        root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
