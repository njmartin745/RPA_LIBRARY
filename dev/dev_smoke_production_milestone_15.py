from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORDER_PY = REPO_ROOT / "dev" / "rpa_studio_playwright_recorder.py"
RECORDER_JS = REPO_ROOT / "dev" / "rpa_studio_playwright_recorder_server.mjs"
FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "rpa_studio_playwright_demo"
PAGE_PATH = FIXTURE_DIR / "index.html"
README_PATH = FIXTURE_DIR / "README.md"
DOC_PATH = REPO_ROOT / "docs" / "analysis" / "production_milestone_15_playwright_controlled_recorder.md"
ALLOWED_DIRTY = {
    "dev/rpa_studio_playwright_recorder.py",
    "dev/rpa_studio_playwright_recorder_server.mjs",
    "dev/dev_smoke_production_milestone_15.py",
    "dev/fixtures/rpa_studio_playwright_demo/index.html",
    "dev/fixtures/rpa_studio_playwright_demo/README.md",
    "docs/analysis/production_milestone_15_playwright_controlled_recorder.md",
}


def _assert_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding="utf-8").lower()
    for needle in needles:
        assert needle.lower() in text, f"missing {needle!r} in {path}"


def _run_smoke_helper() -> dict[str, object]:
    cp = subprocess.run(
        [sys.executable, str(RECORDER_PY), "run-smoke", "--json"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert cp.returncode == 0, f"PM15 Playwright smoke failed\nSTDOUT:\n{cp.stdout}\nSTDERR:\n{cp.stderr}"
    start = cp.stdout.find("{")
    assert start >= 0, cp.stdout
    result = json.loads(cp.stdout[start:])
    assert isinstance(result, dict), result
    return result


def _assert_workflow(result: dict[str, object]) -> None:
    assert result.get("status") == "pass", result
    assert result.get("headed") is True, result
    assert result.get("browser_open") is True, result
    assert result.get("injection_status") in {"injected", "recording active"}, result
    workflow_path = Path(str(result.get("workflow_json")))
    assert workflow_path.exists() and workflow_path.stat().st_size > 0, workflow_path
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    assert workflow["schema_id"] == "RPA_STUDIO_PLAYWRIGHT_RECORDER_WORKFLOW_1A"
    actions = workflow["actions"]
    assert any(action.get("type") == "Navigate" for action in actions), actions
    assert any(action.get("type") == "Click" for action in actions), actions
    bare_generic = [
        action
        for action in actions
        if str(action.get("selector", "")).lower() in {"input", "button", "div", "span"}
    ]
    assert not bare_generic, bare_generic
    message_click_actions = [
        action
        for action in actions
        if action.get("type") == "Click" and action.get("selector") == "#pm15-message"
    ]
    assert message_click_actions, actions
    assert message_click_actions[0].get("selector_quality") == "strong", message_click_actions
    type_actions = [action for action in actions if action.get("type") == "Type" and action.get("selector") == "#pm15-message"]
    assert len(type_actions) >= 2, actions
    assert type_actions[0].get("text") == "Hello from PM15", actions
    assert type_actions[-1].get("text") == "Hello again", actions
    assert type_actions[0].get("selector_quality") == "strong", type_actions
    assert isinstance(type_actions[0].get("selector_candidates"), list) and type_actions[0]["selector_candidates"], type_actions
    anchor_clicks = [action for action in actions if action.get("type") == "Click" and action.get("selector") == "#anch_49"]
    assert anchor_clicks and anchor_clicks[0].get("selector_quality") == "strong", actions
    assert "Device Characteristics" in anchor_clicks[0].get("label", ""), anchor_clicks
    assert any(action.get("navigation_detected") is True and "#device-characteristics" in str(action.get("resulting_url", "")) for action in anchor_clicks), anchor_clicks
    assert "#anch_49 > h3:nth-of-type" not in json.dumps(workflow), workflow
    assert not any(
        action.get("type") == "Navigate"
        and index > 0
        and actions[index - 1].get("type") == "Navigate"
        and actions[index - 1].get("url") == action.get("url")
        for index, action in enumerate(actions)
    ), actions
    assert any(action.get("wait_before", {}).get("selector") == "#pm15-message" for action in type_actions), type_actions
    secret_actions = [action for action in actions if action.get("type") == "TypeSecret"]
    assert secret_actions, actions
    assert all(action.get("secret_ref") for action in secret_actions), actions
    serialized = json.dumps(workflow, sort_keys=True).lower()
    assert "neverstoreme" not in serialized, serialized
    assert "raw page html" not in serialized
    assert "cookie" not in serialized
    assert "localstorage" not in serialized
    assert "sessionstorage" not in serialized
    artifacts = result.get("artifacts")
    assert isinstance(artifacts, list) and artifacts, result
    for artifact in artifacts:
        path = Path(str(artifact))
        assert path.exists() and path.stat().st_size > 0, path
        assert "_smoke_artifacts" in path.parts, path

    initial_actions = result.get("initial_actions")
    assert isinstance(initial_actions, list) and initial_actions, result
    initial_navigates = [action for action in initial_actions if action.get("type") == "Navigate"]
    assert len(initial_navigates) == 1, initial_actions
    initial_anchor_clicks = [action for action in initial_actions if action.get("type") == "Click" and action.get("selector") == "#anch_49"]
    assert initial_anchor_clicks and initial_anchor_clicks[0].get("navigation_detected") is True, initial_actions
    assert "#device-characteristics" in str(initial_anchor_clicks[0].get("resulting_url", "")), initial_anchor_clicks


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
        if path not in ALLOWED_DIRTY and not path.startswith("dev/fixtures/rpa_studio_playwright_demo/"):
            dirty.append(line)
    assert not dirty, cp.stdout


def dev_smoke() -> None:
    for path in (RECORDER_PY, RECORDER_JS, PAGE_PATH, README_PATH, DOC_PATH):
        assert path.exists(), path
    _assert_contains(
        RECORDER_PY,
        [
            "RPA_STUDIO_NODE_EXE",
            "RPA_STUDIO_NODE_PATH",
            "shutil.which(\"node\")",
            "Playwright runtime unavailable",
            "Install Node.js and Playwright locally",
        ],
    )
    _assert_contains(
        RECORDER_JS,
        [
            "RPA Studio Playwright Recorder",
            "RPA Studio Playwright Recorder — PM15",
            "PM15 · Playwright Controlled Browser Recorder",
            "Recorder mode: Playwright controlled browser",
            "Replay mode: Playwright recorder replay",
            "Status: experimental / not production-ready",
            "Start Recording",
            "Run All",
            "Run From Selected Step",
            "Save Workflow JSON",
            "highlightStep",
            "injectionStatus",
            "Reattach / Resume Recording",
            "page changed, reinjection needed",
            "injection failed",
            "Browser loaded an error page",
            "recording active",
            "Recorder injection failed",
            "Selector is ambiguous; refine selector before replay",
            "Replay automatically waits for each action's target element before interacting",
            "coalesced duplicate Navigate",
            "annotated click navigation",
            "navigation_detected",
            "resulting_url",
            "isClickableCandidate",
            "selector_quality",
            "selector_candidates",
            "selector-warning",
            "TypeSecret",
            "secret_ref",
            "headless: !headed",
        ],
    )
    _assert_contains(PAGE_PATH, ["pm15-message", "pm15-reference", "pm15-secret", "pm15-submit", "anch_49", "Device Characteristics", "type=\"password\""])
    _assert_contains(
        DOC_PATH,
        [
            "not production-ready",
            "headed Edge or Chromium",
            "Run From Selected Step",
            "TypeSecret",
            "secret_ref",
            "script injection",
            "GameStop",
            "GUDID",
            "Universal external website support",
            "CAPTCHA",
            "anti-bot",
            "Node.js is required",
            "Codex runtime fallback",
        ],
    )
    result = _run_smoke_helper()
    _assert_workflow(result)
    _assert_git_status_clean_or_only_allowed()


if __name__ == "__main__":
    dev_smoke()
    print("DEV_SMOKE_OK: production_milestone_15")
