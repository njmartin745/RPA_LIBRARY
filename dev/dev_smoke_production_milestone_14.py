from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RECORDER_PATH = REPO_ROOT / "dev" / "rpa_studio_recorder.py"
FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "rpa_studio_recorder_demo"
PAGE_PATH = FIXTURE_DIR / "index.html"
BRIDGE_PATH = FIXTURE_DIR / "recorder_bridge.js"
README_PATH = FIXTURE_DIR / "README.md"
DOC_PATH = REPO_ROOT / "docs" / "analysis" / "production_milestone_14_embedded_recorder.md"
ALLOWED_DIRTY = {
    "dev/rpa_studio_recorder.py",
    "dev/dev_smoke_production_milestone_14.py",
    "dev/fixtures/rpa_studio_recorder_demo/index.html",
    "dev/fixtures/rpa_studio_recorder_demo/recorder_bridge.js",
    "dev/fixtures/rpa_studio_recorder_demo/README.md",
    "docs/analysis/production_milestone_14_embedded_recorder.md",
}


def _assert_file_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding="utf-8").lower()
    for needle in needles:
        assert needle.lower() in text, f"missing {needle!r} in {path}"


def _assert_action_shape(action: Mapping[str, Any]) -> None:
    assert action.get("type") in {"Navigate", "Click", "Type", "Wait for Selector", "Wait Seconds"}, action
    if action.get("type") in {"Click", "Type", "Wait for Selector"}:
        selector = action.get("selector")
        assert isinstance(selector, str) and selector.strip(), action
        assert not selector.startswith("/html"), action
    if action.get("type") == "Type":
        assert "password" not in json.dumps(action).lower(), action
        assert isinstance(action.get("text"), str) and action["text"], action


def _assert_artifacts(result: Mapping[str, Any]) -> None:
    assert result.get("status") == "pass", result
    assert result.get("scenario") == "rpa-studio-recorder-local-demo", result
    assert result.get("replay_adapter") == "PM14-local iframe replay adapter", result
    artifacts = result.get("artifacts")
    assert isinstance(artifacts, list) and len(artifacts) >= 5, result
    required_suffixes = {
        "logs/run.jsonl",
        "history/run_manifest.json",
        "history/step_outcomes.jsonl",
        "workflow/recorded_workflow.json",
        "report/run_report.md",
    }
    normalized = {Path(str(path)).as_posix().split("rpa_studio_recorder/")[-1] for path in artifacts}
    for suffix in required_suffixes:
        assert any(item.endswith(suffix) for item in normalized), (suffix, normalized)
    for path in artifacts:
        artifact = Path(str(path))
        assert artifact.exists() and artifact.is_file() and artifact.stat().st_size > 0, artifact
    workflow = json.loads(Path(str(result["workflow_json"])).read_text(encoding="utf-8"))
    assert workflow["schema_id"] == "RPA_STUDIO_RECORDER_WORKFLOW_1A"
    assert len(workflow["actions"]) >= 4


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
        if path not in ALLOWED_DIRTY and not path.startswith("dev/fixtures/rpa_studio_recorder_demo/"):
            dirty.append(line)
    assert not dirty, cp.stdout


def dev_smoke() -> None:
    for path in (RECORDER_PATH, PAGE_PATH, BRIDGE_PATH, README_PATH, DOC_PATH):
        assert path.exists(), path

    _assert_file_contains(
        RECORDER_PATH,
        [
            "RPA Studio Recorder MVP",
            "Start Recording",
            "Stop Recording",
            "Clear Actions",
            "Run Steps",
            "Workflow JSON Preview / Export",
            "Live Execution Log",
            "Run Evidence",
            "PM14-local iframe replay adapter",
        ],
    )
    _assert_file_contains(PAGE_PATH, ["recorder-input", "recorder-submit", "recorder-result", "recorder_bridge.js"])
    _assert_file_contains(BRIDGE_PATH, ["password", "redacted", "selectorFor", "postMessage"])
    _assert_file_contains(
        DOC_PATH,
        [
            "not production-ready",
            "external website automation is not proven",
            "PM14-local iframe replay adapter",
            "existing RUN/PIPE/ACT",
            "manual demo steps",
        ],
    )

    from dev.rpa_studio_recorder import replay_recorded_actions, sample_recorded_actions, workflow_from_actions

    actions = sample_recorded_actions()
    assert any(action.get("type") == "Click" for action in actions), actions
    assert any(action.get("type") == "Type" for action in actions), actions
    for action in actions:
        _assert_action_shape(action)
    workflow = workflow_from_actions(actions)
    assert workflow["schema_id"] == "RPA_STUDIO_RECORDER_WORKFLOW_1A"
    assert workflow["runtime_scope"] == "controlled_local_fixture_only"
    result = replay_recorded_actions(actions)
    _assert_artifacts(result)
    _assert_git_status_clean_or_only_allowed()


if __name__ == "__main__":
    dev_smoke()
    print("DEV_SMOKE_OK: production_milestone_14")
