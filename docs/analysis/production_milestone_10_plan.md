# Production Milestone 10 Plan

## 1. Milestone Definition

Production Milestone 10 should polish the static proof artifact viewer introduced in Milestone 9 and plan run operations summary improvements without changing runtime behavior.

The milestone should make the existing fixture-bound proof artifacts easier for an operator to read:

- success and controlled failure runs remain side by side
- raw failure JSON is replaced with a formatted failure detail card
- step outcomes show the best available result/evidence fields
- run duration is displayed when timestamps are present
- a Run Operations Summary section clearly distinguishes captured values from values not captured yet

Milestone 10 should remain a viewer and planning milestone. It should not add new workflow execution behavior or fake operational telemetry.

## 2. Non-Goals

- Do not add external website support.
- Do not add downloads.
- Do not add credentials.
- Do not add arbitrary workflow execution.
- Do not make `REGISTRY/action_registry.json` authoritative.
- Do not broaden action coverage.
- Do not replace the CLI proof runner.
- Do not add Streamlit or any new dependency.
- Do not create a full app/dashboard.
- Do not claim production readiness.
- Do not change runtime behavior.
- Do not change validation semantics.
- Do not implement real multi-agent orchestration.
- Do not implement retry orchestration.
- Do not implement resume/continuation behavior.
- Do not implement record-level manifest processing.

## 3. Files/Modules To Inspect

Files inspected for this plan:

- `docs/analysis/production_milestone_9_plan.md`
- `docs/analysis/production_proof_status.md`
- `dev/production_proof_demo_viewer.py`
- `dev/dev_smoke_production_milestone_9.py`
- `dev/production_proof_local_browser.py`
- `dev/production_failure_proof_local_browser.py`
- `CLI/cli_production_proof_1a.py`
- `REPORT/report_1a_run_report.py`
- `REPORT/report_1b_run_report_markdown.py`
- `REPORT/report_1d_generate_reports.py`
- `HISTORY/history_1a_run_manifest.py`
- `HISTORY/history_1b_step_outcomes.py`
- `LOG/log_1a_structured_logging.py`
- `dev/_smoke_artifacts/` structure, inspected only for artifact layout

## 4. Current Viewer Behavior

`dev/production_proof_demo_viewer.py` currently renders a static HTML proof viewer from existing success and controlled failure artifact directories.

Current behavior:

- reads `history/run_manifest.json`
- reads `history/step_outcomes.jsonl`
- reads `bundle/deploy_bundle_fingerprint.json`
- reads `report/run_report.json`
- summarizes `logs/run.jsonl`
- renders controlled success and controlled failure sections
- displays a prominent not-production-ready warning
- displays run status, workflow name, run id, scenario, bundle fingerprint, total steps, status counts, log event counts, step outcomes, and artifact paths
- displays controlled failure detail by dumping failure outcome JSON in a `<pre>` block

The viewer is already artifact-only. The Milestone 9 smoke guards against importing or referencing proof execution helpers and core execution modules inside `dev/production_proof_demo_viewer.py`.

## 5. Current Artifact Fields Available

Artifacts currently capture enough data for a more readable viewer:

- run status from `report/run_report.json`
- workflow name from `history/run_manifest.json`
- run id from `history/run_manifest.json`
- step outcomes from `history/step_outcomes.jsonl`
- status counts from `report/run_report.json`
- artifact paths from the viewer's known artifact map
- logs/report/history file paths
- bundle fingerprint SHA-256 from `bundle/deploy_bundle_fingerprint.json`
- start and finish timestamps from `history/run_manifest.json` and `report/run_report.json`, when present
- basic error class/message from step outcomes
- redacted step action data, including `action`, `url`, `selector_ref`, and selector data if present in the recorded step
- log event counts and error counts from `logs/run.jsonl`

## 6. Gap Analysis: Captured Versus Not Captured

Already captured today:

- run status
- workflow name
- run id
- step outcomes
- status counts
- artifact paths
- logs/report/history files
- some timestamps if present in artifacts

Not proven or captured yet:

- real manifest record counts
- retries or attempt history
- continuation/resume behavior
- multiple agents/workers
- per-agent throughput
- record-level completed/failed/skipped counts

The viewer should not infer or invent the missing data. Missing operational fields should be displayed as `Not captured yet` or `Not applicable for this fixture-bound proof`.

## 7. Proposed Viewer Polish

Milestone 10 should keep the viewer static HTML and dev-only, but improve readability:

- replace raw failure JSON with a formatted failure detail card
- add a `Result / Evidence` column to the step outcomes table
- display run duration near the run status when timestamps are available
- add a Run Operations Summary section below each run card
- use consistent empty-state labels for unavailable operational metrics
- keep the not-production-ready warning prominent
- preserve the existing artifact-only source guard in the PM9 smoke or add a PM10 smoke guard with the same intent

No viewer control should execute workflows, invoke proof helpers, or accept arbitrary workflow paths.

## 8. Proposed Formatted Failure Detail Card

The failure card should be rendered from existing failure artifacts only.

For the Milestone 8 controlled missing-selector failure, show where available:

- expected failure type: `missing_selector`
- failed action: `wait_for_selector`
- selector_ref: `pm8.missing_element`
- resolved selector: `#pm8-never-appears`
- condition, if present in the step
- timeout, if present in the step
- error class and message
- interpretation: `Controlled expected failure: the local/static page intentionally omits this selector.`

Unknown fields should render as `Not captured yet`, not as blank cells or fabricated values.

## 9. Proposed Step-Level Result/Evidence Display

Add a `Result / Evidence` column derived from existing step outcome and step data.

Suggested display rules:

- `open`: show page/current URL if captured; otherwise show the requested `url`
- `wait_for_selector`: show `selector_ref`, resolved selector if present, condition if present, and found/not found if captured
- `click_selector`: show `selector_ref`, resolved selector if present, and click dispatched status if captured
- failed steps: show error class/message, `selector_ref`, selector, condition, and timeout where present
- unknown/missing values: show `Not captured yet`

Do not change `HISTORY.history_1b_step_outcomes` in Milestone 10 just to create evidence fields. This milestone should render the evidence that exists today and document gaps.

## 10. Proposed Run Duration Display

The viewer should compute duration only when both `started_at_utc` and `finished_at_utc` are present and parseable.

Sources:

- `history/run_manifest.json` timestamps
- `report/run_report.json` run timestamps
- log first/last timestamps as a fallback display, not as authoritative duration

Display rules:

- show duration in seconds with a conservative precision, such as `1.24s`
- show start and finish timestamps as supporting details
- show `Not captured yet` if either endpoint is missing
- do not infer duration from filesystem modification times

## 11. Proposed Run Operations Summary Section

Add a Run Operations Summary section to each run card.

Planned fields:

- run status
- started time
- finished time
- duration
- manifest records total/completed/failed/skipped
- total attempts
- retry attempts
- max attempts
- continued after failure
- agent/worker count
- per-agent attempted/completed/failed/retried/duration

For Milestone 10, this section should mostly display real current values plus explicit gap labels. It should make the absence of operational telemetry visible without pretending those capabilities exist.

## 12. Treatment Of Manifest Record Counts

Current proof artifacts include a run manifest, but they do not prove record-level manifest processing.

Milestone 10 display rule:

- if a future artifact provides record counts, display the real totals
- for current fixture-bound proof artifacts, show `Not captured yet`
- do not derive record counts from step counts
- do not treat `step_outcomes` count as manifest record count

Record-level manifest count support should be deferred until the framework has an actual record manifest contract.

## 13. Treatment Of Retries And Attempt History

Current proof artifacts do not prove retry orchestration or attempt history.

Milestone 10 display rule:

- show `Not captured yet` for retry attempts and total attempts unless a real artifact provides those fields
- show `Not applicable for this fixture-bound proof` when describing the current success/failure fixtures
- do not count repeated PM8 smoke runs as runtime retry attempts
- do not infer retry behavior from multiple ignored run directories

Retry orchestration should remain a future milestone after controlled retry semantics are designed.

## 14. Treatment Of Continuation/Resume After Failed Attempts

Current proof artifacts do not prove continuation or resume behavior.

Milestone 10 display rule:

- show `Not captured yet` for continued-after-failure when no artifact exists
- show `Not applicable for this fixture-bound proof` for the current controlled local/static proof
- do not claim resume capability because PM8 can run the same failure fixture twice
- do not add resume behavior in the viewer

Continuation/resume should be deferred until runtime support and artifact semantics are intentionally designed.

## 15. Treatment Of Multiple Agents/Workers

Current proof artifacts do not prove multiple agents, workers, or per-agent throughput.

Milestone 10 display rule:

- show `Not captured yet` for agent/worker count and per-agent metrics
- do not infer one worker from the local process unless an artifact records it
- do not add synthetic agent identifiers to reports
- do not claim multi-agent support

Worker/agent telemetry belongs in a future run metrics artifact once the execution model requires it.

## 16. Proposed "Not Captured Yet" / "Not Applicable" Display Rules

Use two distinct labels:

- `Not captured yet`: the framework may need this field for production operations, but no current artifact records it.
- `Not applicable for this fixture-bound proof`: the field does not apply to the current controlled local/static proof scenario.

Examples:

- manifest record counts: `Not captured yet`
- retries: `Not captured yet`
- continuation/resume: `Not captured yet`
- multiple agents/workers: `Not captured yet`
- downloads: `Not applicable for this fixture-bound proof`
- credentials: `Not applicable for this fixture-bound proof`

These labels should help operators understand proof boundaries without overstating readiness.

## 17. Proposed Future `run_metrics.json` Schema

Milestone 10 should document, but not necessarily implement, a future metrics artifact such as:

```json
{
  "schema": "RUN-METRICS-1A",
  "run_id": "string",
  "scenario": "string",
  "status": "ok|error|skip",
  "timestamps": {
    "started_at_utc": "string|null",
    "finished_at_utc": "string|null",
    "duration_ms": "number|null"
  },
  "manifest_records": {
    "total": "number|null",
    "completed": "number|null",
    "failed": "number|null",
    "skipped": "number|null"
  },
  "attempts": {
    "total": "number|null",
    "retry_attempts": "number|null",
    "max_attempts": "number|null",
    "continued_after_failure": "boolean|null"
  },
  "agents": {
    "worker_count": "number|null",
    "workers": [
      {
        "worker_id": "string",
        "attempted": "number|null",
        "completed": "number|null",
        "failed": "number|null",
        "retried": "number|null",
        "duration_ms": "number|null"
      }
    ]
  }
}
```

All nullable fields should remain nullable until runtime components produce real values.

## 18. Whether `run_metrics.json` Should Be Implemented In Milestone 10

Recommendation: defer `run_metrics.json` implementation.

Milestone 10 should document the schema and optionally shape the viewer so it can read `run_metrics.json` later if present. It should not write this artifact now because the most important fields are not currently generated by the runtime.

If any code support is added, keep it read-only:

- viewer checks for optional `metrics/run_metrics.json`
- viewer displays real values when present
- viewer displays `Not captured yet` when absent

Do not introduce a writer for fake or derived operational metrics in Milestone 10.

## 19. How To Avoid Faking Operational Metrics

Implementation should follow these rules:

- only display values loaded from existing artifacts
- derive duration only from artifact timestamps
- derive status counts only from `report/run_report.json` or step outcomes
- never derive manifest records from steps
- never derive retry attempts from repeated smoke runs
- never derive worker count from the local process
- never derive continuation/resume from rerunning a fixture
- mark absent operational data as `Not captured yet`
- keep the not-production-ready notice visible

## 20. Positive Test Strategy

Add or extend a focused PM10 smoke, for example `dev/dev_smoke_production_milestone_10.py`, if Milestone 10 is implemented.

Positive assertions:

- generate or locate controlled success and failure artifacts using existing fixture-bound proof helpers
- generate `proof_demo.html` under `dev/_smoke_artifacts/production_milestone_10/run_<time_ns>_<pid>/`
- assert the viewer remains artifact-only
- assert the HTML is non-empty
- assert formatted failure card exists
- assert raw JSON failure dump is removed from the primary failure detail section
- assert `Result / Evidence` column exists
- assert run duration label exists
- assert Run Operations Summary exists
- assert `Not captured yet` appears for record counts, retries, continuation, and agents/workers
- assert not-production-ready notice remains
- assert git status remains clean

## 21. Negative/Regression Test Strategy

Regression assertions:

- Milestone 9 smoke still passes or is superseded by a PM10 smoke with equivalent artifact-only guard coverage
- viewer source still does not import or reference proof execution helpers or runtime modules
- no new dependency is introduced
- no external website, credential, download, or arbitrary workflow path appears in the viewer
- missing optional metrics artifact does not fail rendering
- malformed optional metrics artifact fails clearly if metrics reading is added
- browser-unavailable behavior remains in proof helpers and is not handled by the artifact-only viewer

Recommended validation commands for implementation:

```powershell
python dev/dev_smoke_production_milestone_10.py
python dev/dev_smoke_production_milestone_9.py
python dev/dev_smoke_production_milestone_8.py
python dev/dev_smoke_production_milestone_7.py
python dev/dev_smoke_production_milestone_6.py
python -m CLI.cli_production_proof_1a run-local-browser-proof
python -m CLI.cli_production_proof_1a run-local-browser-proof --json
python dev/dev_smoke_production_milestone_5.py
python -c "from VAL.val_2a_deploy_bundle_validator import dev_smoke; dev_smoke(); print('DEV_SMOKE_OK: VAL.val_2a_deploy_bundle_validator')"
git status --short --branch
```

## 22. File-By-File Implementation Options

Recommended narrow implementation:

- `dev/production_proof_demo_viewer.py`
  - add duration calculation from artifact timestamps
  - add formatted failure detail card
  - add result/evidence rendering helper
  - add Run Operations Summary rendering helper
  - optionally read `metrics/run_metrics.json` only if present
  - keep artifact-only and static HTML

- `dev/dev_smoke_production_milestone_10.py`
  - generate success/failure artifacts through existing fixture-bound helpers
  - render PM10 viewer output under a unique ignored run directory
  - assert viewer source remains artifact-only
  - assert new sections and gap labels exist
  - assert git status remains clean

- `docs/analysis/production_proof_status.md`
  - optional small status refresh after Milestone 10 lands
  - state viewer polish improved operator readability, not production readiness

Files to avoid touching unless a direct blocker appears:

- `RUN/*`
- `PIPE/*`
- `ACT/*`
- `WORKFLOWS/*`
- `VAL/*`
- `CLI/cli_production_proof_1a.py`
- `REGISTRY/action_registry.json`
- production milestone fixtures from Milestones 1-9

## 23. Risk Assessment

Low risk:

- static HTML presentation changes
- adding viewer helper functions for duration and evidence display
- adding explicit `Not captured yet` labels
- adding a PM10 smoke

Medium risk:

- parsing optional future metrics files, because malformed files need clear handling
- changing existing PM9 viewer output, because smoke assertions may depend on current labels

High risk and out of scope:

- changing runtime artifact writers to produce operational metrics
- adding retry/resume behavior
- adding record manifest processing
- adding worker/agent telemetry

The main product risk is accidental overclaiming. The viewer must make limitations more visible, not hide them behind polished UI.

## 24. Rollback Plan

Milestone 10 should be easy to roll back:

- revert `dev/production_proof_demo_viewer.py` presentation changes
- remove `dev/dev_smoke_production_milestone_10.py` if added
- keep existing Milestone 9 viewer and smokes intact
- no runtime or validation rollback should be needed because those layers should not change

If optional metrics reading creates trouble, remove only the optional read path and keep the display labels.

## 25. Milestone Exit Criteria

Milestone 10 is complete when:

- the static proof viewer displays success and controlled failure artifacts more clearly
- controlled failure details are formatted in a human-readable card
- step outcomes include a result/evidence column where current artifacts support it
- run duration displays when artifact timestamps are present
- Run Operations Summary displays real captured values and clear gap labels
- missing manifest records, retries, continuation/resume, and agent/worker metrics are labeled without fake values
- `run_metrics.json` is documented as a future artifact or read only if already present
- the viewer remains dev-only, static HTML, and artifact-only
- existing Milestone 9 artifact-only guard remains effective
- validation commands pass or skip only for browser-unavailable preflight reasons
- generated outputs remain under ignored `dev/_smoke_artifacts/`
- `git status --short --branch` remains clean after smoke runs

