# Production Milestone 8 Plan

## 1. Milestone Definition

Production Milestone 8 should prove controlled failure behavior, retry boundaries, and idempotency for the current production golden path without adding broad production features.

The milestone should extend the existing local/static browser proof pattern with one focused failure proof:

deploy bundle fixture
-> VAL-2A production validation
-> WORKFLOWS-1G loader
-> RUN-1E/RUN-1A
-> PIPE-1A
-> ACT-1A
-> controlled runtime failure
-> LOG/HISTORY/REPORT artifacts

The target failure should be production-valid before runtime, then fail deterministically during browser execution. The safest first failure is a selector action whose `selector_ref` exists in the selector pack but resolves to a selector that is absent from the local/static page.

## 2. Non-Goals

- Do not add a broad retry framework.
- Do not add real website support.
- Do not add downloads.
- Do not add credentials.
- Do not make `REGISTRY/action_registry.json` authoritative.
- Do not broaden action coverage.
- Do not change production validation semantics.
- Do not change runtime behavior except for a direct blocker required to observe existing behavior.
- Do not mask runtime failures as browser-unavailable skips.
- Do not prove arbitrary workflow production execution.

## 3. Files/Modules To Inspect

Inspected for this plan:

- `RUN/run_1a_workflow_runner.py`
- `RUN/run_1e_deploy_bundle_runner_adapter.py`
- `PIPE/pipe_1a_run_orchestrator.py`
- `ACT/act_1a_action_engine.py`
- `VAL/val_2a_deploy_bundle_validator.py`
- `HISTORY/history_1a_run_manifest.py`
- `HISTORY/history_1b_step_outcomes.py`
- `REPORT/report_1a_run_report.py`
- `REPORT/report_1b_run_report_markdown.py`
- `REPORT/report_1c_junit_xml.py`
- `REPORT/report_1d_generate_reports.py`
- `CLI/cli_production_proof_1a.py`
- `dev/production_proof_local_browser.py`
- `dev/dev_smoke_production_milestone_6.py`
- `dev/dev_smoke_production_milestone_7.py`
- `dev/fixtures/production_milestone_5/`
- `docs/analysis/production_proof_status.md`
- `docs/analysis/action_contract_alignment_report.md`

Requested but not present on current `main`:

- `LOG/log_1a_event_logger.py`

The current runtime path imports `LOG/log_1a_structured_logging.py`; Milestone 8 should inspect/use that existing LOG-1A module if log behavior must be asserted.

## 4. Current Failure Behavior

ACT-1A records a `StepOutcome` for each attempted step. When an action raises and `fail_fast=True`, ACT-1A raises `ActionEngineError` with the failing outcome included in the exception payload.

Current action failure examples:

- `wait_for_selector` raises when the target selector is not found or does not meet the requested condition before timeout.
- `click_selector` raises when the target is not found, not clickable, intercepted, stale after retry, or otherwise fails through WebDriver.
- unknown actions raise before execution in ACT-1A, but Milestone 7 keeps `log` rejection at VAL-2A production validation before runtime.

PIPE-1A catches `ActionEngineError` at the item level, marks the item failed, captures an error summary, emits structured failure logging, and appends an item record to state/manifest handling. For a single-item proof run, `RUN/run_1a_workflow_runner.py` normalizes the PIPE result into `success=False`, `errors=[...]`, and `step_logs` when available.

`dev/production_proof_local_browser.py` currently asserts positive runtime success. For Milestone 8, a new failure-oriented smoke should expect `runtime_summary["success"] is False` and should not reuse positive-only assertions that require all step logs to succeed.

## 5. Current Retry Behavior, If Any

There is no broad production retry framework proven today.

Existing narrow retry/poll behavior:

- Selenium explicit waits poll until timeout inside `wait_for_selector`, `click_selector`, and related element operations.
- ACT-1A `click` retries once after `StaleElementReferenceException`.
- ACT-1A `click_selector` performs one deterministic stale-element retry, then fails if the retry fails.
- PIPE-1A continues to the next work item after item failure, but the milestone proof currently uses a single item. That is item progression, not retry.

Milestone 8 should not add automatic retries for failed workflow steps. It should prove the current boundary: controlled runtime failures fail once, produce artifacts, and are not silently retried into success.

## 6. Current Idempotency Behavior

Current proof idempotency is mostly environmental and artifact-oriented:

- Milestone 4 established unique ignored run directories under `dev/_smoke_artifacts/.../run_<time_ns>_<pid>/`.
- Milestone 5 and 6 use controlled local/static fixtures and unique output directories.
- The local/static site starts fresh for each smoke invocation through a new local server/browser proof path.
- The runtime itself does not yet expose workflow-level idempotency keys, item claim records, or exactly-once semantics.

Milestone 8 should prove idempotency narrowly as repeatability: running the same controlled failure proof multiple times creates separate ignored output directories, produces the same failure classification, does not contaminate prior outputs, and leaves git status clean.

## 7. Failure Cases To Prove First

Use one production-valid runtime failure first:

- `wait_for_selector` with a valid `selector_ref` whose selector points to a missing element on the local/static page.
- Expected behavior: validation passes; browser starts; workflow opens the local page; missing selector step fails; later steps are not marked successful; runtime summary is failure; artifacts are produced.

Optional second failure if still small:

- `click_selector` against a valid but missing selector after an initial successful `open`.

Do not use invalid registry/action fixtures for Milestone 8 runtime failure. Those are validation failures and already covered by prior milestones.

## 8. Retry Cases To Prove First

The first retry proof should be a boundary proof, not a new retry implementation:

- Assert the missing-selector runtime failure is not converted into a pass.
- Assert the failed step appears once in step outcomes for the single execution.
- Assert the smoke does not re-run the workflow automatically after runtime failure.
- Assert browser-unavailable paths are skips only before meaningful runtime execution begins.

Defer true retry behavior, retry policies, backoff, and retry-safe action classification to a later milestone.

## 9. Idempotency Cases To Prove First

Prove repeatability using local/static fixtures:

- Run the same failure proof twice in one smoke.
- Each run uses a unique ignored output directory.
- Each run produces the same high-level result: validation ok, runtime failure, report status `error`, one failed selector step.
- The two runs do not overwrite each other.
- `git status --short --branch` remains clean after repeated runs.

Do not claim business idempotency or exactly-once execution. This milestone proves controlled, repeatable failure artifacts only.

## 10. Artifact Expectations On Failure

Failure runs should still produce required audit artifacts:

- JSONL log: `logs/run.jsonl`
- Run manifest: `history/run_manifest.json`
- Step outcomes: `history/step_outcomes.jsonl`
- Bundle fingerprint: `bundle/deploy_bundle_fingerprint.json`
- Markdown or JSON report: `report/run_report.md` and preferably `report/run_report.json`

The report should indicate failure:

- REPORT-1A `run.status` should be `error`.
- REPORT-1A summary should include at least one `error` status.
- REPORT-1B markdown should include a failed step section.
- REPORT-1C JUnit should include a failure count if generated.

## 11. Manifest/History Expectations On Failure

The run manifest should exist and include:

- run id
- workflow name
- bundle version/path/hash when available
- run output directory
- runtime summary in `extra` if using the current smoke/proof helper pattern

Step outcomes should exist and include:

- successful prior steps, such as `open`
- the failing step with `status="error"`
- the failing step index
- the redacted step payload
- error class/message if available

Milestone 8 should verify failure artifacts are non-empty and semantically reflect failure, not merely that files exist.

## 12. Browser-Unavailable Skip Behavior

If no compatible Chrome/Edge browser or driver is available, the smoke may skip with a clear message and no false pass.

The skip should be limited to browser/session availability before the proof reaches runtime behavior. Once browser execution starts and a workflow action fails, that failure must be treated as the expected negative scenario for Milestone 8, not as browser unavailable.

## 13. How To Avoid Masking Real Failures As Skips

Milestone 8 should distinguish:

- browser setup/preflight failures: allowed skip
- local HTTP server startup failure: fail
- validation failure for the runtime-failure fixture: fail
- loader failure: fail
- runtime selector failure: expected negative result, not skip
- missing failure artifacts: fail
- successful execution of the failure fixture: fail

Do not broaden `_looks_browser_unavailable` to include generic runtime assertion text, selector timeout text, or action failure summaries.

## 14. Positive Test Strategy

Keep existing positive coverage:

- `python dev/dev_smoke_production_milestone_6.py`
- `python -m CLI.cli_production_proof_1a run-local-browser-proof`
- `python -m CLI.cli_production_proof_1a run-local-browser-proof --json`
- `python dev/dev_smoke_production_milestone_5.py`

Add one Milestone 8 smoke:

- `python dev/dev_smoke_production_milestone_8.py`

The Milestone 8 smoke should:

- start a local HTTP server on `127.0.0.1`
- validate a production-valid failure deploy bundle with VAL-2A `production=True`
- load through WORKFLOWS-1G
- execute through the existing RUN/PIPE/ACT path using a real browser when available
- expect controlled runtime failure
- assemble/verify failure artifacts using existing LOG/HISTORY/REPORT modules
- run the failure proof twice to prove repeatable ignored output directories and stable failure classification

## 15. Negative/Regression Test Strategy

Regression checks should include:

- Milestone 7 smoke still passes.
- Milestone 6 smoke still passes.
- Milestone 5 positive browser proof still passes or skips only for browser unavailability.
- VAL-2A dev smoke still passes.
- Production validation still rejects `log` through Milestone 7 coverage.
- The Milestone 8 runtime failure fixture is not rejected by VAL-2A; it must reach runtime and fail there.
- The failure fixture must not print `PASS`.
- The failure fixture must not print a browser-unavailable skip after the browser has been selected and execution begins.

## 16. File-By-File Implementation Options

Preferred minimal files:

- `dev/dev_smoke_production_milestone_8.py`
  - New focused smoke.
  - Runs the controlled local/static failure proof twice.
  - Prints `DEV_SMOKE_OK: production_milestone_8` only after expected failures and artifact checks complete.
  - Prints `SKIP: production_milestone_8 real browser unavailable: <reason>` only when browser/driver preflight is unavailable.

- `dev/fixtures/production_milestone_8/deploy_bundle_missing_selector.json`
  - Production-valid deploy bundle.
  - Uses `open`, then `wait_for_selector` or `click_selector` with a valid selector ref pointing to a missing local element.

- `dev/fixtures/production_milestone_8/site/index.html`
  - Controlled local/static page.
  - May copy the Milestone 5 page or use a simpler page with one known present element and one intentionally absent selector.

- `dev/fixtures/production_milestone_8/expected_artifacts.json`
  - Required artifact list for failure runs.

Optional helper, only if duplication becomes distracting:

- `dev/production_failure_proof_local_browser.py`
  - Dev-only helper mirroring the Milestone 5 helper shape but expecting failure.

Files to avoid changing unless a direct blocker is found:

- `RUN/run_1a_workflow_runner.py`
- `RUN/run_1e_deploy_bundle_runner_adapter.py`
- `PIPE/pipe_1a_run_orchestrator.py`
- `ACT/act_1a_action_engine.py`
- `VAL/val_2a_deploy_bundle_validator.py`
- `CLI/cli_production_proof_1a.py`

## 17. Risk Assessment

Low risk if implemented as a dev-only smoke and fixtures.

Primary risks:

- accidentally treating expected selector failure as browser-unavailable skip
- asserting only file existence instead of semantic failure content
- creating a fixture that fails validation instead of runtime
- broadening helper behavior used by the positive production proof
- claiming retry/idempotency support that is not actually implemented

Mitigation:

- keep Milestone 8 fixture production-valid
- keep failure proof separate from the Milestone 5 positive helper unless reuse is clearly safe
- assert report/history semantics
- run repeated proof sequences and final `git status`

## 18. Rollback Plan

Rollback should be simple:

- remove `dev/dev_smoke_production_milestone_8.py`
- remove `dev/fixtures/production_milestone_8/`
- remove any optional dev-only helper added for Milestone 8

No runtime, validation, registry, or CLI behavior should need rollback because the milestone should not modify those modules.

## 19. Milestone Exit Criteria

Milestone 8 exits when:

- a controlled failure deploy bundle passes VAL-2A production validation
- the bundle loads through WORKFLOWS-1G
- real browser execution reaches RUN/PIPE/ACT
- the expected selector/action failure is observed as a runtime failure, not a skip
- JSONL log, run manifest, step outcomes, bundle fingerprint, and report artifacts are produced and non-empty
- report/history artifacts semantically show failure
- repeated failure proof runs use unique ignored output directories and leave git status clean
- Milestones 5, 6, and 7 regression smokes still pass
- no broad retry framework, runtime refactor, registry authority change, external site support, downloads, or credential behavior is introduced
