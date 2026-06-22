# Production Milestone 15: Playwright Controlled Browser Recorder

## What PM15 Adds

Production Milestone 15 adds an experimental Playwright-powered controlled
browser recorder for RPA Studio. It launches a real headed Edge or Chromium
browser, captures Click and Type actions, keeps the browser open after stopping
recording, replays recorded steps, supports replay from a selected step, allows
recording continuation after replay, saves workflow JSON, and can highlight the
element for a selected recorded step.

This is not production-ready. It is a controlled browser recorder spike.

## How To Launch

```powershell
python dev/rpa_studio_playwright_recorder.py serve
```

Then open:

```text
http://127.0.0.1:8879/
```

## Local Setup Notes

Node.js is required for the PM15 Playwright recorder. Playwright must be
available to the Node process through normal local Node module resolution or
through an explicit `RPA_STUDIO_NODE_PATH`.

Lookup order:

1. `RPA_STUDIO_NODE_EXE`, if set.
2. `node` from `PATH`.
3. Codex runtime Node, only if present.

Module path behavior:

1. `RPA_STUDIO_NODE_PATH`, if set.
2. Normal Node module resolution.
3. Codex runtime `node_modules`, only if present.

The Codex runtime fallback is a development fallback, not a stable user
dependency. Local users should install Node.js and Playwright locally or set
`RPA_STUDIO_NODE_EXE` / `RPA_STUDIO_NODE_PATH` explicitly.

## Manual Demo Steps

1. Launch `python dev/rpa_studio_playwright_recorder.py serve`.
2. Open the Studio URL.
3. Click `Start Recording`; Studio opens a headed Edge/Chromium browser if needed.
4. Navigate or use the prefilled local demo page.
5. Type and click in the controlled browser.
6. Click `Stop Recording`; the browser remains open.
7. Click `Run All` to replay recorded steps.
8. Select a recorded step and click `Run From Selected Step`.
9. Click a recorded step to highlight the target element in the browser.
10. Click `Start Recording` again and add more steps.
11. Click `Save Workflow JSON`.

## What Is Visibly Demoable Now

- Real headed Edge/Chromium browser launch through Playwright.
- Navigate, Click, Type, and TypeSecret/redacted capture.
- Type capture collapsed to one final Type action per field interaction.
- Browser remains open after Stop Recording and replay.
- Run all steps.
- Run from selected step.
- Append more recording after replay.
- Highlight selected step target element.
- Workflow JSON preview and saved workflow artifacts.

## What Remains Deferred

- Production readiness.
- Universal external website support.
- CAPTCHA, anti-bot, login challenge, or security restriction bypass.
- Credential vault.
- Downloads.
- Retry/resume orchestration.
- Scheduling.
- Multi-agent execution.
- Production RUN/PIPE/ACT execution of recorded Playwright actions.

## Safety

PM15 does not capture cookies, tokens, localStorage, sessionStorage, hidden input
values, raw page HTML, or raw password values. Password fields are recorded as
`TypeSecret` actions with a placeholder `secret_ref`.

## Artifacts

Generated artifacts are written under ignored directories:

```text
dev/_smoke_artifacts/rpa_studio_playwright_recorder/run_<time_ns>_<pid>/
```

Artifacts include:

- `workflow/recorded_workflow.json`
- `logs/run.jsonl`
