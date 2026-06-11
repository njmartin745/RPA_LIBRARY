from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev import production_failure_proof_local_browser as failure_proof  # noqa: E402
from dev import production_proof_demo_viewer as viewer  # noqa: E402
from dev import production_proof_local_browser as success_proof  # noqa: E402

OUT_ROOT = REPO_ROOT / "dev" / "_smoke_artifacts" / "production_milestone_9"
SELF_STATUS_PATHS = {
    "docs/analysis/production_proof_status.md",
    "dev/production_proof_demo_viewer.py",
    "dev/dev_smoke_production_milestone_9.py",
}
VIEWER_FORBIDDEN_REFERENCES = (
    "production_proof_local_browser",
    "production_failure_proof_local_browser",
    "run_workflow",
    "CLI.cli_production_proof_1a",
    "ACT.",
    "RUN.",
    "PIPE.",
    "WORKFLOWS.",
    "VAL.",
)


class BrowserUnavailable(RuntimeError):
    pass


def _required_artifacts() -> tuple[str, ...]:
    return (
        "logs/run.jsonl",
        "history/run_manifest.json",
        "history/step_outcomes.jsonl",
        "bundle/deploy_bundle_fingerprint.json",
        "report/run_report.json",
        "report/run_report.md",
    )


def _has_required_artifacts(path: Path) -> bool:
    return path.is_dir() and all((path / rel).is_file() and (path / rel).stat().st_size > 0 for rel in _required_artifacts())


def _candidate_artifact_dirs(root: Path, leaf: str) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted((path for path in root.rglob(leaf) if _has_required_artifacts(path)), key=lambda p: p.stat().st_mtime, reverse=True)


def _latest_success_dir() -> Path:
    candidates = list(_candidate_artifact_dirs(success_proof.OUT_ROOT, "positive"))
    if not candidates:
        raise AssertionError("success proof did not produce a positive artifact directory")
    return candidates[0]


def _latest_failure_dir() -> Path:
    candidates = list(_candidate_artifact_dirs(failure_proof.OUT_ROOT, "missing_selector"))
    if not candidates:
        raise AssertionError("failure proof did not produce a missing_selector artifact directory")
    return candidates[0]


def _run_success_artifacts() -> Path:
    if success_proof.dev_smoke():
        return _latest_success_dir()
    raise BrowserUnavailable("success proof real browser unavailable")


def _run_failure_artifacts() -> Path:
    try:
        failure_proof.OUT_ROOT.mkdir(parents=True, exist_ok=True)
        base = time.time_ns()
        run_dirs = [failure_proof.OUT_ROOT / f"run_{base}_{os.getpid()}_{idx}" for idx in range(2)]
        for run_dir in run_dirs:
            run_dir.mkdir(parents=True, exist_ok=False)

        httpd = None
        thread = None
        try:
            httpd, thread, site_url = failure_proof._start_static_server()
            browser, unavailable = failure_proof._select_available_browser(run_dirs[0])
            if browser is None:
                reason = "; ".join(unavailable) if unavailable else "no compatible browser candidate succeeded"
                raise BrowserUnavailable(f"failure proof real browser unavailable: {reason}")
            classifications = [
                failure_proof._run_failure_proof_once(run_dir=run_dir, site_url=site_url, browser=browser)
                for run_dir in run_dirs
            ]
            assert classifications == ["missing_selector_runtime_failure", "missing_selector_runtime_failure"], classifications
            return _latest_failure_dir()
        finally:
            if httpd is not None:
                httpd.shutdown()
                httpd.server_close()
            if thread is not None:
                thread.join(timeout=5)
    except failure_proof.BrowserUnavailable as exc:
        raise BrowserUnavailable(f"failure proof real browser unavailable: {exc}") from exc


def _assert_git_status_clean() -> None:
    import subprocess

    cp = subprocess.run(
        ["git", "status", "--short", "--branch"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if cp.returncode != 0:
        raise AssertionError(f"git status failed\nstdout={cp.stdout}\nstderr={cp.stderr}")
    dirty: list[str] = []
    for line in cp.stdout.splitlines()[1:]:
        if not line.strip():
            continue
        path = line[3:].replace("\\", "/")
        if path in SELF_STATUS_PATHS:
            continue
        dirty.append(line)
    assert not dirty, cp.stdout


def _assert_viewer_is_artifact_only() -> None:
    source = (REPO_ROOT / "dev" / "production_proof_demo_viewer.py").read_text(encoding="utf-8")
    found = [needle for needle in VIEWER_FORBIDDEN_REFERENCES if needle in source]
    assert not found, f"viewer must remain artifact-only; forbidden references found: {found}"


def dev_smoke() -> Path | None:
    _assert_viewer_is_artifact_only()

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    run_dir = OUT_ROOT / f"run_{time.time_ns()}_{os.getpid()}"
    run_dir.mkdir(parents=True, exist_ok=False)

    success_dir = _run_success_artifacts()
    failure_dir = _run_failure_artifacts()
    output_path = run_dir / "proof_demo.html"
    viewer.write_proof_demo_html(
        success_run_dir=success_dir,
        failure_run_dir=failure_dir,
        output_path=output_path,
    )

    assert output_path.exists(), output_path
    assert output_path.stat().st_size > 0, output_path
    assert str(output_path.resolve()).startswith(str((REPO_ROOT / "dev" / "_smoke_artifacts").resolve())), output_path

    html = output_path.read_text(encoding="utf-8")
    assert "Production Proof Demo" in html, html
    assert "Not production-ready" in html, html
    assert "Controlled Success" in html, html
    assert "Controlled Failure" in html, html
    assert "Bundle Fingerprint SHA-256" in html, html
    assert html.count("Bundle Fingerprint SHA-256") >= 2, html
    assert "pm8.missing_element" in html or "wait_for_selector failed" in html, html
    assert "#pm8-never-appears" in html or "missing selector" in html.lower(), html

    _assert_git_status_clean()
    return output_path


if __name__ == "__main__":
    try:
        demo_path = dev_smoke()
    except BrowserUnavailable as exc:
        print(f"SKIP: production_milestone_9 real browser unavailable: {exc}")
    else:
        print(f"PROOF_DEMO: {demo_path}")
        print("DEV_SMOKE_OK: production_milestone_9")
