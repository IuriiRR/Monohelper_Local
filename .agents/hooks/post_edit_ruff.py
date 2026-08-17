#!/usr/bin/env python3
"""Antigravity PostToolUse hook to auto-format and autofix Python files with Ruff."""

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print("{}")
            return

        payload = json.loads(raw_input)
        tool_call = payload.get("toolCall", {})
        args = tool_call.get("args", {})
        target_file = args.get("TargetFile") or args.get("target_file") or args.get("file_path")

        if target_file and str(target_file).endswith(".py"):
            target_path = Path(target_file).resolve()
            if target_path.is_file():
                # Locate ruff binary: check project .venv first, then PATH
                workspace_root = Path(__file__).resolve().parent.parent.parent
                venv_ruff = workspace_root / ".venv" / "bin" / "ruff"
                ruff_cmd = str(venv_ruff) if venv_ruff.is_file() else "ruff"

                subprocess.run(
                    [ruff_cmd, "check", str(target_path), "--fix", "--quiet"],
                    cwd=str(workspace_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
    except Exception:
        pass
    finally:
        print("{}")


if __name__ == "__main__":
    main()
