from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "rpa_studio_lite_demo"
DOC_PATH = REPO_ROOT / "docs" / "analysis" / "production_milestone_13_rpa_studio_lite.md"
UI_PATH = REPO_ROOT / "dev" / "rpa_studio_lite.py"
SAMPLE_PATH = FIXTURE_DIR / "sample_workflow.json"
PAGE_PATH = FIXTURE_DIR / "index.html"
SUPPORTED_ACTIONS = {"Navigate", "Wait for Selector", "Type", "Click", "Wait Seconds"}
FORBIDDEN_DOC_MARKERS = (
    "external website support",
    "credential handling",
    "download handling",
    "retry orchestration",
    "resume or continuation",
    "multi-agent execution",
)
ALLOWED_DIRTY = {
    "dev/rpa_studio_lite.py",
    "dev/dev_smoke_production_milestone_13.py",
    "dev/fixtures/rpa_studio_lite_demo/index.html",
    "dev/fixtures/rpa_studio_lite_demo/README.md",
    "dev/fixtures/rpa_studio_lite_demo/sample_workflow.json",
    "docs/analysis/production_milestone_13_rpa_studio_lite.md",
}


def _read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(obj, dict), f"expected JSON object: {path}"
    return obj


def _assert_sample_workflow_safe(sample: Mapping[str, Any]) -> None:
    assert sample.get("schema_id") == "RPA_STUDIO_LITE_WORKFLOW_1A"
    assert sample.get("runtime_scope") == "controlled_local_fixture_only"
    actions = sample.get("actions")
    selectors = sample.get("selectors")
    assert isinstance(actions, list) and actions, "sample workflow must have actions"
    assert isinstance(selectors, dict) and selectors, "sample workflow must have selectors"

    for action in actions:
        assert isinstance(action, dict), action
        assert action.get("type") in SUPPORTED_ACTIONS, action
        if action.get("type") == "Navigate":
            assert action.get("url") == "__STUDIO_DEMO_SITE_URL__", action
        if action.get("type") in {"Wait for Selector", "Type", "Click"}:
            ref = action.get("selector_ref")
            assert isinstance(ref, str) and ref in selectors, action

    serialized = json.dumps(sample, sort_keys=True).lower()
    assert "http://" not in serialized.replace("__studio_demo_site_url__", "")
    assert "https://" not in serialized
    assert "password" not in serialized
    assert "credential" not in serialized
    assert "download" not in serialized
    assert "retry" not in serialized
    assert "resume" not in serialized
    assert "multi-agent" not in serialized


def _assert_docs_scope() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    assert "not production-ready" in text or "not production ready" in text
    for marker in FORBIDDEN_DOC_MARKERS:
        assert marker in text, f"doc should explicitly defer {marker!r}"
    assert "controlled local sample" in text
    assert "custom workflow replay is deferred" in text
    assert "edited json replay" in text or "edited workflow json" in text


def _assert_viewer_file_scope() -> None:
    text = UI_PATH.read_text(encoding="utf-8")
    assert "production_proof_local_browser" in text, "Studio Lite should reuse existing local proof helper"
    assert "run_metrics.json" not in text, "Studio Lite must not generate fake run metrics"
    assert "REGISTRY/action_registry.json" not in text
    assert "_smoke_artifacts" in text and "DEFAULT_OUTPUT_ROOT" in text
    lowered_ui = text.lower()
    assert "run controlled local sample" in lowered_ui
    assert "edited workflow json can be saved but is not executed" in lowered_ui
    assert "current pm13 behavior" in lowered_ui
    assert "run edited/custom workflow: deferred" in lowered_ui
    forbidden_execution_surfaces = ("requests.", "urllib.request", "paramiko", "boto3", "playwright", "run_metrics.json")
    lowered = text.lower()
    for marker in forbidden_execution_surfaces:
        assert marker not in lowered, f"UI helper should not introduce {marker}"


def _assert_artifacts(result: Mapping[str, Any]) -> None:
    assert result.get("status") == "pass", result
    assert result.get("scenario") == "rpa-studio-lite-local-demo", result
    assert result.get("browser") in {"chrome", "edge"}, result
    run_dir = Path(str(result.get("run_dir")))
    assert run_dir.exists(), run_dir
    assert "dev" in run_dir.parts and "_smoke_artifacts" in run_dir.parts, run_dir
    artifacts = result.get("artifacts")
    assert isinstance(artifacts, list) and artifacts, result
    required_suffixes = {
        "logs/run.jsonl",
        "history/run_manifest.json",
        "history/step_outcomes.jsonl",
        "bundle/deploy_bundle_fingerprint.json",
        "report/run_report.md",
    }
    normalized = {Path(str(path)).as_posix().split("rpa_studio_lite/")[-1] for path in artifacts}
    for suffix in required_suffixes:
        assert any(item.endswith(suffix) for item in normalized), (suffix, normalized)
    for path in artifacts:
        artifact = Path(str(path))
        assert artifact.exists() and artifact.is_file() and artifact.stat().st_size > 0, artifact
    assert Path(str(result.get("run_report"))).name == "run_report.md"
    assert Path(str(result.get("step_outcomes"))).name == "step_outcomes.jsonl"


def _assert_git_status_clean_or_only_allowed() -> None:
    cp = subprocess.run(
        ["git", "status", "--short", "--branch"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert cp.returncode == 0, cp.stderr
    dirty: list[str] = []
    for line in cp.stdout.splitlines()[1:]:
        if not line.strip():
            continue
        path = line[3:].replace("\\", "/")
        if path not in ALLOWED_DIRTY and not path.startswith("dev/fixtures/rpa_studio_lite_demo/"):
            dirty.append(line)
    assert not dirty, cp.stdout


def dev_smoke() -> None:
    assert UI_PATH.exists(), UI_PATH
    assert PAGE_PATH.exists(), PAGE_PATH
    assert SAMPLE_PATH.exists(), SAMPLE_PATH
    assert DOC_PATH.exists(), DOC_PATH

    sample = _read_json(SAMPLE_PATH)
    _assert_sample_workflow_safe(sample)
    _assert_docs_scope()
    _assert_viewer_file_scope()

    from dev.rpa_studio_lite import run_sample_workflow

    old_log_path = os.environ.get("LOG_PATH")
    old_log_jsonl_path = os.environ.get("LOG_JSONL_PATH")
    stale_log_path = REPO_ROOT / "dev" / "_smoke_artifacts" / "rpa_studio_lite" / "stale_env" / "run.jsonl"
    os.environ["LOG_PATH"] = str(stale_log_path)
    os.environ["LOG_JSONL_PATH"] = str(stale_log_path)
    try:
        result = run_sample_workflow()
    finally:
        if old_log_path is None:
            os.environ.pop("LOG_PATH", None)
        else:
            os.environ["LOG_PATH"] = old_log_path
        if old_log_jsonl_path is None:
            os.environ.pop("LOG_JSONL_PATH", None)
        else:
            os.environ["LOG_JSONL_PATH"] = old_log_jsonl_path
    if result.get("status") == "skip":
        raise AssertionError(f"Studio Lite smoke requires local browser execution, got skip: {result!r}")
    _assert_artifacts(result)
    _assert_git_status_clean_or_only_allowed()


if __name__ == "__main__":
    dev_smoke()
    print("DEV_SMOKE_OK: production_milestone_13")









