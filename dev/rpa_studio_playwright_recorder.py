from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NODE_EXE = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "bin" / "node.exe"
NODE_MODULES = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "node_modules"
PNPM_NODE_MODULES = NODE_MODULES / ".pnpm" / "node_modules"
SERVER = REPO_ROOT / "dev" / "rpa_studio_playwright_recorder_server.mjs"


def _node_command() -> list[str]:
    if not NODE_EXE.exists():
        raise SystemExit(f"Playwright Node runtime unavailable: missing {NODE_EXE}")
    if not NODE_MODULES.exists():
        raise SystemExit(f"Playwright Node modules unavailable: missing {NODE_MODULES}")
    if not PNPM_NODE_MODULES.exists():
        raise SystemExit(f"Playwright pnpm modules unavailable: missing {PNPM_NODE_MODULES}")
    return [str(NODE_EXE), str(SERVER)]


def main() -> int:
    env = os.environ.copy()
    env["NODE_PATH"] = os.pathsep.join([str(NODE_MODULES), str(PNPM_NODE_MODULES)])
    cmd = _node_command() + sys.argv[1:]
    return subprocess.call(cmd, cwd=REPO_ROOT, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
