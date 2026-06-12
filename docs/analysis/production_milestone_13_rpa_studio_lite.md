# Production Milestone 13: RPA Studio Lite Build-and-Run Demo

## Purpose

Production Milestone 13 adds a small, local, demoable RPA Studio Lite
experience. It lets a user build a simple automation shape, view and save the
workflow JSON, run a bundled local/static sample workflow, and inspect the run
artifacts produced by the existing proof path.

This is not production-ready. It is a controlled local proof for showing the
current framework behavior to a non-technical user without adding external
website, credential, download, retry, resume, multi-agent, or arbitrary workflow
execution support.

## How To Launch

From the repository root:

```powershell
python dev/rpa_studio_lite.py serve
```

Then open:

```text
http://127.0.0.1:8765/
```

The sample can also be run without the UI:

```powershell
python dev/rpa_studio_lite.py run-sample --json
```

## What The Demo Does

- Shows a local browser-based UI titled `RPA Studio Lite`.
- Shows a `Build Automation` section.
- Allows manual addition of a small supported action set.
- Displays the current workflow JSON.
- Saves the workflow JSON into an ignored demo artifact directory.
- Runs the bundled local/static sample workflow.
- Shows run status, message, browser, scenario, run directory, and artifact paths.
- Shows paths to `run_report.md` and `step_outcomes.jsonl` when the sample run passes.

## Supported Actions

The Studio Lite builder supports these local-demo actions:

- `Navigate`
- `Wait for Selector`
- `Type`
- `Click`
- `Wait Seconds`

The bundled sample workflow uses a controlled local/static page. The visible
`Type` action is converted into an existing `exec_js` runtime step for this
milestone so the framework does not add a new generic text-entry action contract.

## What This Proves

- A user can build and save a simple workflow/action list as JSON.
- A bundled local workflow can be converted into a deploy bundle.
- The generated deploy bundle can pass existing production validation gates.
- The existing WORKFLOWS/RUN/PIPE/ACT path can run the local sample in a real browser.
- Existing history, report, log, and fingerprint artifacts are produced for the run.
- A non-technical user can see run evidence without reading internal modules.

## What This Does Not Prove

- Production readiness.
- Arbitrary workflow execution.
- External website support.
- Credential handling.
- Download handling.
- Retry orchestration.
- Resume or continuation behavior.
- Multi-agent execution.
- Registry authority.
- Runtime telemetry writers such as `run_metrics.json`.
- Broad action coverage.

## Demo Fixtures

The controlled local/static page lives under:

```text
dev/fixtures/rpa_studio_lite_demo/index.html
```

The bundled sample workflow lives under:

```text
dev/fixtures/rpa_studio_lite_demo/sample_workflow.json
```

The page includes stable selectors for:

- input field
- submit button
- visible result/status area

## Artifact Output

Generated demo artifacts are written under ignored run directories:

```text
dev/_smoke_artifacts/rpa_studio_lite/run_<time_ns>_<pid>/
```

Passing runs include:

- `logs/run.jsonl`
- `history/run_manifest.json`
- `history/step_outcomes.jsonl`
- `bundle/deploy_bundle_fingerprint.json`
- `report/run_report.md`

The milestone does not generate fake metrics and does not claim
`metrics/run_metrics.json` exists.

## Relationship To PM5-PM12

- PM5 proved real browser execution against a controlled local/static page.
- PM6 added a fixture-bound single-command proof runner.
- PM8 proved controlled runtime failure artifacts.
- PM9 and PM10 added a static proof artifact viewer and polish.
- PM11 and PM12 documented future operational telemetry contracts.
- PM13 adds a visible Studio Lite build-and-run demo on top of the local proof foundation.

## Deferred Features

- Running arbitrary user-provided workflows.
- Promoting the Studio JSON format to a production workflow contract.
- Generic selector capture.
- Real text-entry action contract alignment.
- Runtime telemetry writers.
- Record/worklist manifest execution.
- Retry, resume, and multi-agent behavior.
- Packaging this as a production application.
