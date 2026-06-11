from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev import production_failure_proof_local_browser as proof  # noqa: E402


def dev_smoke() -> bool:
    return proof.dev_smoke()


if __name__ == "__main__":
    try:
        if dev_smoke():
            print("DEV_SMOKE_OK: production_milestone_8")
    except proof.BrowserUnavailable as exc:
        print(f"SKIP: production_milestone_8 real browser unavailable: {exc}")
