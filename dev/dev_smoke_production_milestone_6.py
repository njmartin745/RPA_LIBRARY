from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "CLI.cli_production_proof_1a", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_pass_or_skip(cp: subprocess.CompletedProcess[str]) -> None:
    out = cp.stdout.strip()
    if cp.returncode == 0:
        assert "PASS: production_proof local-browser" in out, out
        assert "SKIP: production_proof local-browser" not in out, out
        return
    if cp.returncode == 2:
        assert "SKIP: production_proof local-browser real browser unavailable:" in out, out
        assert "PASS: production_proof local-browser" not in out, out
        return
    raise AssertionError(f"unexpected exit code {cp.returncode}\nstdout={cp.stdout}\nstderr={cp.stderr}")


def test_command_text_output() -> None:
    cp = _run_command("run-local-browser-proof")
    _assert_pass_or_skip(cp)
    assert not cp.stderr.strip(), cp.stderr


def test_command_json_output() -> None:
    cp = _run_command("run-local-browser-proof", "--json")
    assert cp.returncode in {0, 2}, f"unexpected exit code {cp.returncode}\nstdout={cp.stdout}\nstderr={cp.stderr}"
    assert "PASS: production_proof local-browser" not in cp.stdout or cp.returncode == 0
    payload = json.loads(cp.stdout)
    assert payload["scenario"] == "local-browser-static-site", payload
    assert payload["status"] in {"pass", "skip"}, payload
    assert isinstance(payload["run_dir"], str) and payload["run_dir"], payload
    if cp.returncode == 0:
        assert payload["status"] == "pass", payload
        assert payload["message"] == "PASS: production_proof local-browser", payload
        assert payload["browser"] in {"chrome", "edge"}, payload
        assert isinstance(payload["artifacts"], list) and payload["artifacts"], payload
    else:
        assert payload["status"] == "skip", payload
        assert payload["message"].startswith("SKIP: production_proof local-browser real browser unavailable:"), payload
        assert "PASS: production_proof local-browser" not in payload["message"], payload


def dev_smoke() -> None:
    test_command_text_output()
    test_command_json_output()


if __name__ == "__main__":
    dev_smoke()
    print("DEV_SMOKE_OK: production_milestone_6")
