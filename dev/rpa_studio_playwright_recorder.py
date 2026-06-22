from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER = REPO_ROOT / "dev" / "rpa_studio_playwright_recorder_server.mjs"
SETUP_MESSAGE = (
    "Playwright runtime unavailable. Install Node.js and Playwright locally or "
    "set RPA_STUDIO_NODE_EXE / RPA_STUDIO_NODE_PATH."
)
CODEX_NODE_ROOT = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node"
CODEX_NODE_EXE = CODEX_NODE_ROOT / "bin" / ("node.exe" if os.name == "nt" else "node")
CODEX_NODE_MODULES = CODEX_NODE_ROOT / "node_modules"
CODEX_PNPM_NODE_MODULES = CODEX_NODE_MODULES / ".pnpm" / "node_modules"


def _resolve_node_exe() -> Path:
    configured = os.environ.get("RPA_STUDIO_NODE_EXE", "").strip()
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.exists():
            return candidate
        raise SystemExit(f"{SETUP_MESSAGE} Missing RPA_STUDIO_NODE_EXE: {candidate}")

    from_path = shutil.which("node")
    if from_path:
        return Path(from_path)

    if CODEX_NODE_EXE.exists():
        return CODEX_NODE_EXE

    raise SystemExit(SETUP_MESSAGE)


def _module_paths() -> list[str]:
    configured = os.environ.get("RPA_STUDIO_NODE_PATH", "").strip()
    if configured:
        return [part for part in configured.split(os.pathsep) if part.strip()]

    paths: list[str] = []
    if CODEX_NODE_MODULES.exists():
        paths.append(str(CODEX_NODE_MODULES))
    if CODEX_PNPM_NODE_MODULES.exists():
        paths.append(str(CODEX_PNPM_NODE_MODULES))
    return paths


def _playwright_probe(node_exe: Path, env: dict[str, str]) -> None:
    probe = (
        "try { require('playwright'); process.exit(0); } "
        "catch (e) { console.error(e && e.message ? e.message : String(e)); process.exit(1); }"
    )
    cp = subprocess.run(
        [str(node_exe), "-e", probe],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if cp.returncode != 0:
        detail = (cp.stderr or cp.stdout or "").strip()
        suffix = f" Details: {detail}" if detail else ""
        raise SystemExit(f"{SETUP_MESSAGE}{suffix}")


def _runtime() -> tuple[list[str], dict[str, str]]:
    node_exe = _resolve_node_exe()
    env = os.environ.copy()
    module_paths = _module_paths()
    if module_paths:
        existing = env.get("NODE_PATH", "").strip()
        all_paths = module_paths + ([existing] if existing else [])
        env["NODE_PATH"] = os.pathsep.join(all_paths)
    _playwright_probe(node_exe, env)
    return [str(node_exe), str(SERVER)], env


def main() -> int:
    cmd, env = _runtime()
    cmd += sys.argv[1:]
    return subprocess.call(cmd, cwd=REPO_ROOT, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
