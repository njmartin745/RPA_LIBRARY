# Production Milestone 14: Embedded Browser Recorder MVP

## What PM14 Adds

Production Milestone 14 adds a visible local RPA Studio Recorder MVP inspired by workflow-builder tools such as Power Automate and Automation Anywhere. It provides a local Studio UI with an embedded browser-like iframe, recorder controls, a workflow/action sidebar, workflow JSON preview/export, a live execution log, and run evidence artifacts.

This is not production-ready. It is a controlled local/static proof.

Recording is enabled only on the bundled local demo page in PM14. External URLs may load visually if the embedded browser allows them, but action recording and replay are not supported or proven there. PM14 does not inject the recorder bridge into arbitrary external websites; external website automation is future work.

## How To Launch

From the repository root:

```powershell
python dev/rpa_studio_recorder.py serve
```

Then open:

```text
http://127.0.0.1:8877/
```

If that port is occupied, use another local port:

```powershell
python dev/rpa_studio_recorder.py serve --port 8878
```

## Manual Demo Steps

1. Launch `python dev/rpa_studio_recorder.py serve`.
2. Open the Studio URL shown in the terminal.
3. Click `Home / Load Demo` if the embedded browser is not already on the local demo page.
4. Click `Start Recording`.
5. Type into the demo page message input.
6. Click the demo page submit button.
7. Confirm `Type` and `Click` actions appear in the recorded actions list.
8. Click `Stop Recording`.
9. Click `Run Steps`.
10. Confirm the UI shows pass/fail, live log lines, run evidence, artifact paths, saved workflow JSON, `run_report.md`, and `step_outcomes.jsonl`.

## What Is Visibly Demoable Now

- Local Studio UI.
- Larger embedded browser-like iframe panel for a more comfortable local demo.
- URL bar with Go, Home / Load Demo, and Reload controls, with Home / Load Demo returning to the bundled local demo page.
- Start/Stop recording controls.
- Clear Actions.
- Run Steps.
- Immediate click/type capture from the controlled local/static demo page.
- Stable selector display for captured actions.
- Workflow JSON preview and export.
- Live execution log.
- Run evidence artifact paths.

## What Is Still Not Proven

- Production readiness.
- External website automation is not proven. External sites may load visually, but recording/replay remains local-demo only.
- Credential handling.
- Downloads.
- Retry orchestration.
- Resume/continuation behavior.
- Multi-agent execution.
- Scheduling.
- Credential vault behavior.
- REGISTRY/action_registry.json authority.
- Production RUN/PIPE/ACT replay of arbitrary recorded UI actions.

## Selector Strategy

The recorder bridge chooses selectors in this order:

1. `id`
2. `name`
3. `data-testid`
4. `aria-label`
5. simple CSS tag selector fallback

Absolute XPath is intentionally avoided for PM14.

## Privacy And Secret Handling

The recorder bridge does not capture password field values. If an input has `type="password"`, the action is marked redacted and no value is stored. The demo must not capture cookies, tokens, session ids, hidden values, credentials, raw payloads, or downloaded content.

## Replay Behavior

PM14 uses a PM14-local iframe replay adapter for the controlled demo actions. Replay is intentionally limited to the bundled local demo page. It replays Navigate, Wait for Selector, Type, Click, and Wait Seconds against the embedded local/static page. This is a real local replay of the captured actions in the Studio UI, but it is not yet the production runtime replay path.

The existing RUN/PIPE/ACT framework remains unchanged. PM14 relates to it as an operator-facing recorder proof that can later be mapped into production deploy bundles and runtime execution.

## Artifacts And Logs

Generated artifacts are written under ignored directories:

```text
dev/_smoke_artifacts/rpa_studio_recorder/run_<time_ns>_<pid>/
```

Artifacts include:

- `logs/run.jsonl`
- `history/run_manifest.json`
- `history/step_outcomes.jsonl`
- `workflow/recorded_workflow.json`
- `report/run_report.md`

No `run_metrics.json` writer is added in PM14.

## Relationship To PM13 And Existing Framework

PM13 introduced a Studio Lite build-and-run demo for a bundled local sample. PM14 adds the first embedded recorder experience: users can record interactions in a controlled local page, see actions appear immediately, replay them, save JSON, and inspect evidence.

PM14 does not replace PM13 and does not rewrite the framework. It preserves PM5-PM13 proof smokes and keeps replay scoped to a dev-only PM14-local adapter until a future milestone maps recorded actions into the production RUN/PIPE/ACT path.
