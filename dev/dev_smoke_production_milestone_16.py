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
    assert any(action.get("navigation_detected") is True and "#device-characteristics" in str(action.get("resulting_url", "")) for action in anchor_clicks), anchor_clicks
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
    assert any(entry.get("action") == "TypeSecret" and entry.get("status") == "ok" and entry.get("secret_ref") for entry in run_log), run_log
    missing_secret_run = result.get("missing_secret_run")
    assert isinstance(missing_secret_run, dict) and missing_secret_run.get("status") == "fail", missing_secret_run
    failed_step = missing_secret_run.get("failed_step")
    assert isinstance(failed_step, dict) and "Missing secret value for" in str(failed_step.get("error", "")), missing_secret_run
    assert "PM16 replay secret" not in json.dumps(result), result

    highlight = result.get("highlight")
    assert isinstance(highlight, dict) and highlight.get("status") == "highlighted", highlight

    lifecycle = result.get("lifecycle")
    assert isinstance(lifecycle, dict), result
    no_page = lifecycle.get("no_page_reattach")
    assert isinstance(no_page, dict) and no_page.get("status") == "fail", lifecycle
    assert "No active browser page" in str(no_page.get("message", "")), no_page
    assert no_page.get("recording_state") == "stopped", no_page
    resumed = lifecycle.get("resumed_reattach")
    assert isinstance(resumed, dict) and resumed.get("status") == "recording active", lifecycle
    assert resumed.get("recording_state") == "recording", resumed
    assert "Recorder reattached and recording resumed" in str(resumed.get("message", "")), resumed
    after_reload = lifecycle.get("after_reload_reattach")
    assert isinstance(after_reload, dict) and after_reload.get("status") == "recording active", lifecycle
    assert after_reload.get("recording_state") == "recording", after_reload
    active = lifecycle.get("active_reattach")
    assert isinstance(active, dict) and active.get("status") == "recording active", lifecycle
    assert active.get("recording_state") == "recording", active

    first_recording_actions = result.get("first_recording_actions")
    assert isinstance(first_recording_actions, list) and first_recording_actions, result
    first_recording_navigates = [action for action in first_recording_actions if action.get("type") == "Navigate"]
    assert len(first_recording_navigates) == 1, first_recording_actions
    first_recording_anchor_clicks = [action for action in first_recording_actions if action.get("type") == "Click" and action.get("selector") == "#anch_49"]
    assert first_recording_anchor_clicks and first_recording_anchor_clicks[0].get("navigation_detected") is True, first_recording_actions
    assert "#device-characteristics" in str(first_recording_anchor_clicks[0].get("resulting_url", "")), first_recording_anchor_clicks

    lifecycle_logs = result.get("lifecycle_logs")
    assert isinstance(lifecycle_logs, list) and lifecycle_logs, result
    lifecycle_messages = {str(entry.get("message")) for entry in lifecycle_logs if isinstance(entry, dict)}
    for expected in {
        "reattach requested",
        "recorder injected",
        "recording started",
        "recording stopped",
        "recording resumed",
        "injection failed",
        "recorder injected and recording active",
    }:
        assert expected in lifecycle_messages, lifecycle_logs

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
            "Secrets for Replay",
            "/api/set-secret",
            "Missing secret value for",
            "TypeSecret applied for secret_ref",
            "secret set for replay",
            "Secret values stay in memory for this local Studio session only",
            "coalesced duplicate Navigate",
            "isClickableCandidate",
            "run-pm16-smoke",
            "reattach requested",
            "recorder injected",
            "No active browser page. Start Recording or open a browser first.",
            "Recording state:",
            "Reattach / Resume Recording",
            "Use Reattach / Resume Recording after page navigation or reload if capture stops.",
            "Recorder reattached and recording resumed",
            "Recorder reattached; recording remains active.",
            "recording resumed",
            "recorder injected and recording active",
            "navigation_detected",
            "resulting_url",
            "annotated click navigation",
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
            "in-memory secret",
            "Missing secret value",
            "default readiness wait",
            "clickable ancestors",
            "deduped",
            "Injection is not the same as active recording",
            "Reattach / Resume Recording",
            "auto-injects the recorder",
            "click-driven URL changes are stored as metadata",
            "Generated artifacts remain under ignored",
        ],
    )

    result = _run_pm16_helper()
    _assert_pm16_result(result)
    _assert_git_status_clean_or_only_allowed()


if __name__ == "__main__":
    dev_smoke()
    print("DEV_SMOKE_OK: production_milestone_16")
