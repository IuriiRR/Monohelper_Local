"""Entrypoint: ``python -m deploy`` runs the deploy service on 127.0.0.1:8089.

Bound to loopback; reachable directly over an SSH tunnel or via the nginx gateway.
"""

import uvicorn

from deploy.app import app

HOST = "127.0.0.1"
PORT = 8089


def main() -> None:
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
