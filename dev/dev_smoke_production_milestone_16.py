from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORDER_PY = REPO_ROOT / "dev" / "rpa_studio_playwright_recorder.py"
RECORDER_JS = REPO_ROOT / "dev" / "rpa_studio_playwright_recorder_server.mjs"
DOC_PATH = REPO_ROOT / "docs" / "analysis" / "production_milestone_16_recorder_step_editing.md"

ALLOWED_DIRTY = {
    "dev/rpa_studio_playwright_recorder_server.mjs",
    "dev/dev_smoke_production_milestone_16.py",
    "docs/analysis/production_milestone_16_recorder_step_editing.md",
}


def _assert_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding="utf-8").lower()
    for needle in needles:
        assert needle.lower() in text, f"missing {needle!r} in {path}"


def _run_pm16_helper() -> dict[str, object]:
    cp = subprocess.run(
        [sys.executable, str(RECORDER_PY), "run-pm16-smoke", "--json"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=140,
    )
    assert cp.returncode == 0, f"PM16 step editing smoke failed\nSTDOUT:\n{cp.stdout}\nSTDERR:\n{cp.stderr}"
    start = cp.stdout.find("{")
    assert start >= 0, cp.stdout
    result = json.loads(cp.stdout[start:])
    assert isinstance(result, dict), result
    return result


def _assert_pm16_result(result: dict[str, object]) -> None:
    assert result.get("status") == "pass", result
    workflow_path = Path(str(result.get("workflow_json")))
    assert workflow_path.exists() and workflow_path.stat().st_size > 0, workflow_path
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    assert workflow["schema_id"] == "RPA_STUDIO_PLAYWRIGHT_RECORDER_WORKFLOW_1A"
    actions = workflow["actions"]
    assert isinstance(actions, list) and actions, workflow

    assert not any(action.get("selector") == "#pm15-reference" for action in actions), actions
    assert any(action.get("type") == "Wait for Selector" and action.get("selector") == "#pm15-message" and action.get("timeout") == 10 and action.get("enabled") is True for action in actions), actions
    assert any(action.get("type") == "Wait Seconds" and action.get("seconds") == 1 and action.get("enabled") is True for action in actions), actions
    assert any(action.get("enabled") is False for action in actions), actions
    assert any(action.get("type") == "TypeSecret" and action.get("secret_ref") for action in actions), actions
    anchor_clicks = [action for action in actions if action.get("type") == "Click" and action.get("selector") == "#anch_49"]
    assert anchor_clicks and anchor_clicks[0].get("selector_quality") == "strong", actions
    assert "#anch_49 > h3:nth-of-type" not in json.dumps(workflow), workflow
    assert not any(
        action.get("type") == "Navigate"
        and index > 0
        and actions[index - 1].get("type") == "Navigate"
        and actions[index - 1].get("url") == action.get("url")
        for index, action in enumerate(actions)
    ), actions
    assert "PM16 text that must be removed" not in json.dumps(workflow), workflow

    type_secret_index = next(index for index, action in enumerate(actions) if action.get("type") == "TypeSecret")
    wait_seconds_index = next(index for index, action in enumerate(actions) if action.get("type") == "Wait Seconds")
    assert type_secret_index < wait_seconds_index, actions

    run_log = result.get("run_log")
    assert isinstance(run_log, list) and run_log, result
    assert any(entry.get("action") == "Click" and entry.get("wait_before", {}).get("selector") for entry in run_log), run_log
    assert any(entry.get("status") == "skipped" and entry.get("message") == "Step disabled in edited workflow." for entry in run_log), run_log
    assert any(entry.get("action") == "TypeSecret" and entry.get("status") == "skipped" and "credential vault" in entry.get("message", "") for entry in run_log), run_log

    highlight = result.get("highlight")
    assert isinstance(highlight, dict) and highlight.get("status") == "highlighted", highlight

    artifacts = result.get("artifacts")
    assert isinstance(artifacts, list) and artifacts, result
    for artifact in artifacts:
        path = Path(str(artifact))
        assert path.exists() and path.stat().st_size > 0, path
        assert "_smoke_artifacts" in path.parts, path


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
        if path not in ALLOWED_DIRTY:
            dirty.append(line)
    assert not dirty, cp.stdout


def dev_smoke() -> None:
    assert RECORDER_PY.exists(), RECORDER_PY
    assert RECORDER_JS.exists(), RECORDER_JS
    assert DOC_PATH.exists(), DOC_PATH

    _assert_contains(
        RECORDER_JS,
        [
            "RPA Studio Step Editor &mdash; PM16",
            "PM16 &middot; Recorder Step Editing MVP",
            "Delete Step",
            "Replay automatically waits for each action's target element before interacting",
            "Add Explicit Wait for Selected Element",
            "Add Wait Seconds",
            "Mark Type as Secret / Password",
            "Enable / Disable Step",
            "Move Up",
            "Move Down",
            "/api/edit-step",
            "Step disabled in edited workflow",
            "Secret value unavailable; no credential vault configured.",
            "coalesced duplicate Navigate",
            "isClickableCandidate",
            "run-pm16-smoke",
        ],
    )
    _assert_contains(
        DOC_PATH,
        [
            "not production-ready",
            "delete selected step",
            "Wait for Selector",
            "Wait Seconds",
            "TypeSecret",
            "credential vault",
            "default readiness wait",
            "clickable ancestors",
            "deduped",
            "Generated artifacts remain under ignored",
        ],
    )

    result = _run_pm16_helper()
    _assert_pm16_result(result)
    _assert_git_status_clean_or_only_allowed()


if __name__ == "__main__":
    dev_smoke()
    print("DEV_SMOKE_OK: production_milestone_16")
