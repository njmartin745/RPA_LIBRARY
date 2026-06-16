# Production Milestone 15: External Browser Recording Spike

## What PM15 Adds

Production Milestone 15 adds an experimental external browser recording mode for
RPA Studio. A user can launch a real Selenium/WebDriver-controlled browser,
navigate to a URL, inject a recorder script when the page allows it, capture
Click and Type actions, view the recorded workflow JSON in Studio, and save that
workflow JSON to an ignored artifact directory.

This is not production-ready. PM15 is an external browser recording spike, not a
general external automation system.

## How To Launch

From the repository root:

```powershell
python dev/rpa_studio_external_recorder.py serve
```

Then open:

```text
http://127.0.0.1:8879/
```

If the port is occupied:

```powershell
python dev/rpa_studio_external_recorder.py serve --port 8880
```

## Manual Demo Steps

1. Launch `python dev/rpa_studio_external_recorder.py serve`.
2. Open the Studio URL shown in the terminal.
3. Use the prefilled controlled local demo URL or enter another URL.
4. Click `Launch Controlled Browser`.
5. Click `Start Recording`.
6. Interact with the real browser page by typing into a text field and clicking a button.
7. Confirm Click and Type actions appear in the Studio action list.
8. Click `Stop Recording`.
9. Click `Save workflow JSON`.
10. Confirm the saved workflow path is shown.

Optional manual public URL testing is allowed only for harmless pages where
script injection is permitted. Do not use login, account, checkout, payment,
credential, CAPTCHA, anti-bot, download, or private-data flows. Public-site
recording may fail if navigation or script injection is blocked; that is an
expected limitation of this spike.

## What Is Visibly Demoable Now

- A dev-only Studio page titled `RPA Studio External Recorder`.
- URL entry for a controlled browser session.
- Real Selenium/WebDriver browser launch.
- Start/Stop recording controls.
- Recorder script injection through WebDriver script execution.
- Click and Type action capture from the active controlled browser page.
- Type capture collapsed to one final Type action per field interaction.
- Workflow/action list and JSON preview updates.
- Saved workflow JSON path.
- Clear experimental scope and safety messaging.

## What Is Still Not Proven

- Production readiness.
- External replay.
- Universal website support.
- Production external website automation.
- Login, checkout, payment, account, CAPTCHA, or anti-bot flows.
- Credential handling.
- Download handling.
- Retry, resume, scheduling, or multi-agent execution.
- REGISTRY/action_registry.json authority.
- Production RUN/PIPE/ACT execution of recorded external actions.

## Recorder Injection

PM15 injects a small recorder script into the active WebDriver-controlled page
using Selenium `execute_script`. The script creates an in-page event buffer at
`window.__rpaRecorderEvents` and records Click and Type actions when the page
permits script execution.

The Studio server polls that in-page buffer through WebDriver. If injection is
blocked, navigation fails, or the browser session is unavailable, Studio shows a
clear failure message rather than pretending recording succeeded.

PM15 does not inject recorder code into arbitrary external websites when the
browser or site blocks script execution. Those cases remain unsupported and
unproven.

## Selector Strategy

The injected recorder chooses selectors in this order:

1. `id`
2. `name`
3. `data-testid`
4. `aria-label`
5. `placeholder`
6. simple CSS selector fallback

Text labels may be captured as metadata only. Absolute XPath is intentionally
avoided for PM15.

## Privacy And Secret Handling

PM15 does not capture cookies, tokens, localStorage, sessionStorage, hidden
field values, raw page HTML, credentials, or downloaded contents. If an input is
`type="password"`, the recorder skips the field value and records only redacted
metadata when needed.

## Artifacts

Saved workflows are written under ignored directories:

```text
dev/_smoke_artifacts/rpa_studio_external_recorder/run_<time_ns>_<pid>/
```

Artifacts include:

- `workflow/recorded_workflow.json`
- `logs/run.jsonl`

PM15 does not write `run_metrics.json` and does not add runtime telemetry
writers.

## Relationship To PM14

PM14 proved recording and replay inside a controlled same-origin embedded local
page. PM15 moves the recording mechanism into a real WebDriver-controlled
browser and uses script injection plus polling to capture actions from the
active page. Replay remains deferred.
