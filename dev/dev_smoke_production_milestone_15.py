from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RECORDER_PATH = REPO_ROOT / "dev" / "rpa_studio_external_recorder.py"
FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "rpa_studio_external_recorder_demo"
PAGE_PATH = FIXTURE_DIR / "index.html"
README_PATH = FIXTURE_DIR / "README.md"
DOC_PATH = REPO_ROOT / "docs" / "analysis" / "production_milestone_15_external_browser_recording.md"
ALLOWED_DIRTY = {
    "dev/rpa_studio_external_recorder.py",
    "dev/dev_smoke_production_milestone_15.py",
    "dev/fixtures/rpa_studio_external_recorder_demo/index.html",
    "dev/fixtures/rpa_studio_external_recorder_demo/README.md",
    "docs/analysis/production_milestone_15_external_browser_recording.md",
}


def _assert_file_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding="utf-8").lower()
    for needle in needles:
        assert needle.lower() in text, f"missing {needle!r} in {path}"


def _assert_workflow(result: Mapping[str, Any]) -> None:
    workflow_path = Path(str(result.get("workflow_json")))
    assert workflow_path.exists() and workflow_path.stat().st_size > 0, result
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    assert workflow["schema_id"] == "RPA_STUDIO_EXTERNAL_RECORDER_WORKFLOW_1A"
    assert workflow["scenario"] == "rpa-studio-external-recording-spike"
    assert workflow["replay_supported"] is False
    actions = workflow.get("actions")
    assert isinstance(actions, list) and actions, workflow
    assert any(action.get("type") == "Click" for action in actions), actions
    type_actions = [action for action in actions if action.get("type") == "Type"]
    assert type_actions, actions
    message_actions = [action for action in type_actions if action.get("selector") == "#external-message"]
    assert len(message_actions) == 1, actions
    assert message_actions[0].get("text") == "Hello from PM15", actions
    redacted = [action for action in type_actions if action.get("selector") == "#external-secret"]
    assert redacted, actions
    assert all(action.get("redacted") is True for action in redacted), actions
    serialized = json.dumps(workflow, sort_keys=True).lower()
    assert "donotcapture" not in serialized, serialized
    assert "password value must not be captured" not in serialized, serialized
    assert "cookie" not in serialized
    assert "localstorage" not in serialized
    assert "sessionstorage" not in serialized
    assert "credential" not in serialized


def _assert_artifacts(result: Mapping[str, Any]) -> None:
    artifacts = result.get("artifacts")
    assert isinstance(artifacts, list) and artifacts, result
    for path in artifacts:
        artifact = Path(str(path))
        assert artifact.exists() and artifact.is_file() and artifact.stat().st_size > 0, artifact
        assert "_smoke_artifacts" in artifact.parts, artifact


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
        if path not in ALLOWED_DIRTY and not path.startswith("dev/fixtures/rpa_studio_external_recorder_demo/"):
            dirty.append(line)
    assert not dirty, cp.stdout


def dev_smoke() -> bool:
    for path in (RECORDER_PATH, PAGE_PATH, README_PATH, DOC_PATH):
        assert path.exists(), path

    _assert_file_contains(
        RECORDER_PATH,
        [
            "RPA Studio External Recorder",
            "Launch Controlled Browser",
            "Start Recording",
            "Stop Recording",
            "Save workflow JSON",
            "execute_script",
            "window.__rpaRecorderEvents",
            "pushOrReplaceType",
            "type === \"password\"",
            "External replay is deferred",
        ],
    )
    _assert_file_contains(PAGE_PATH, ["external-message", "external-secret", "external-submit", "type=\"password\""])
    _assert_file_contains(
        DOC_PATH,
        [
            "experimental",
            "external replay",
            "not proven",
            "production external website automation",
            "not production-ready",
            "does not capture cookies",
            "does not inject",
            "CAPTCHA",
            "anti-bot",
        ],
    )

    from dev.rpa_studio_external_recorder import BrowserUnavailable, run_controlled_recording_smoke, workflow_from_actions

    try:
        result = run_controlled_recording_smoke()
    except BrowserUnavailable as exc:
        print(f"SKIP: production_milestone_15 real browser unavailable: {exc}")
        return False

    assert result.get("status") == "saved", result
    assert result.get("browser") in {"edge", "chrome"}, result
    assert result.get("scenario") == "rpa-studio-external-recording-spike", result
    _assert_artifacts(result)
    _assert_workflow(result)

    actions = result.get("actions")
    assert isinstance(actions, list) and actions, result
    workflow = workflow_from_actions(actions)
    assert workflow["runtime_scope"] == "experimental_external_recording_only"
    _assert_git_status_clean_or_only_allowed()
    return True


if __name__ == "__main__":
    if dev_smoke():
        print("DEV_SMOKE_OK: production_milestone_15")
