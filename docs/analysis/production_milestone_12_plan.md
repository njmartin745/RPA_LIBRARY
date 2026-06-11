# Production Milestone 12 Plan

## 1. Milestone Definition

Production Milestone 12 should turn the Production Milestone 11 telemetry contract plan into durable contract documentation and example schema fixtures.

The milestone should define the artifact contracts for:

- `metrics/run_metrics.json`
- `history/record_outcomes.jsonl`
- `history/attempt_history.jsonl`
- optional `history/record_manifest.json`

Milestone 12 should remain documentation and fixture only. It should not implement runtime telemetry writers or make proof runs generate operational metrics.

## 2. Non-Goals

- Do not change runtime behavior.
- Do not change validation semantics.
- Do not write runtime telemetry.
- Do not generate `run_metrics.json` from proof runs.
- Do not add retry orchestration.
- Do not add resume/continuation behavior.
- Do not add multi-agent execution.
- Do not add external website support.
- Do not add downloads.
- Do not add credentials.
- Do not add arbitrary workflow execution.
- Do not make `REGISTRY/action_registry.json` authoritative.
- Do not broaden action coverage.
- Do not add dependencies.
- Do not create a full app/dashboard.
- Do not claim production readiness.
- Do not modify the Milestone 10 viewer to read example fixtures as proof artifacts.

## 3. Files/Modules To Inspect

Files inspected for this plan:

- `docs/analysis/production_milestone_11_plan.md`
- `docs/analysis/production_milestone_10_plan.md`
- `docs/analysis/production_proof_status.md`
- `dev/production_proof_demo_viewer.py`
- `dev/dev_smoke_production_milestone_10.py`
- `HISTORY/history_1a_run_manifest.py`
- `HISTORY/history_1b_step_outcomes.py`
- `REPORT/report_1a_run_report.py`
- `REPORT/report_1b_run_report_markdown.py`
- `REPORT/report_1d_generate_reports.py`
- `LOG/log_1a_structured_logging.py`
- `RUN/run_1a_workflow_runner.py`
- `PIPE/pipe_1e_runner.py`
- `PIPE/pipe_1a_run_orchestrator.py`
- `ACT/act_1a_action_engine.py`
- `CLI/cli_production_proof_1a.py`
- existing `docs/` directory structure
- existing `dev/fixtures/` directory structure

Current structure notes:

- No `docs/contracts/` directory exists yet on current `main`.
- `dev/fixtures/` currently contains milestone-specific fixture directories.
- Milestone 10 viewer already performs optional read-only lookup of `{run_output_dir}/metrics/run_metrics.json`.

## 4. Current Telemetry Plan Summary From Milestone 11

Milestone 11 recommended:

- `metrics/run_metrics.json` as the future run-level operational summary artifact
- `history/record_outcomes.jsonl` for append-only per-record lifecycle outcomes
- `history/attempt_history.jsonl` for explicit attempt, retry, and resume attempt records
- optional `history/record_manifest.json` for source record manifest metadata
- nullable unknown operational fields until runtime emits real values
- no inferred manifest record counts from step counts
- no inferred retries from repeated smoke runs
- no inferred worker count from local processes
- no inferred continuation/resume from rerunning a fixture
- no secret-bearing raw values in operational telemetry

Milestone 12 should make those contracts durable but still non-runtime.

## 5. Proposed Contract Documentation Files

Recommended contract documentation files:

- `docs/contracts/run_metrics_1a.md`
- `docs/contracts/record_outcomes_1a.md`
- `docs/contracts/attempt_history_1a.md`
- `docs/contracts/record_manifest_1a.md`
- `docs/analysis/operational_telemetry_contract.md`

Recommendation:

- Create all four contract docs, including `record_manifest_1a.md`, because future record outcomes need a stable source-manifest context even if runtime does not use it yet.
- Create `docs/analysis/operational_telemetry_contract.md` as the summary/index that explains how the four contracts fit together and repeats that these are not runtime-generated proof artifacts yet.

## 6. Proposed Schema/Example Fixture Files

Recommended example fixtures:

- `dev/fixtures/telemetry_contracts/run_metrics_1a_example.json`
- `dev/fixtures/telemetry_contracts/record_outcomes_1a_example.jsonl`
- `dev/fixtures/telemetry_contracts/attempt_history_1a_example.jsonl`
- `dev/fixtures/telemetry_contracts/record_manifest_1a_example.json`

Recommendation:

- Use example JSON and JSONL fixtures first, not formal JSON Schema files.
- Keep the examples small, deterministic, and visibly labeled as contract examples.
- Include nullable fields where runtime telemetry is not yet proven.
- Avoid putting example fixtures under `dev/_smoke_artifacts/` because they are source fixtures, not generated proof artifacts.

Formal JSON Schema files can be deferred until the contracts stabilize after at least one runtime writer milestone.

## 7. Proposed Validation/Smoke Strategy

Milestone 12 implementation should include a fixture-only smoke only if the implementation adds example fixtures.

Recommended smoke:

- `dev/dev_smoke_production_milestone_12.py`

The smoke should:

- parse each example JSON/JSONL fixture
- assert required top-level keys exist
- assert `schema` values match contract docs
- assert nullable fields remain `null` where runtime has not proven values
- assert example files contain no obvious secret-bearing keys or values
- assert example labels clearly say they are contract examples, not runtime proof
- assert the viewer is not pointed at these examples as proof artifacts
- assert `git status --short --branch` remains clean after the smoke

The smoke should not write runtime artifacts and should not invoke RUN/PIPE/ACT.

## 8. Proposed `run_metrics_1a` Contract Scope

`run_metrics_1a` should define `{run_output_dir}/metrics/run_metrics.json`.

Scope:

- aggregate run-level operational telemetry
- summarize record outcomes if record telemetry exists
- summarize attempt history if attempt telemetry exists
- summarize worker/agent telemetry only when real worker execution exists
- reference source artifacts by relative path

Out of scope:

- step-by-step evidence details already owned by `history/step_outcomes.jsonl`
- raw record payloads
- secret values
- runtime writer behavior

Recommended schema id:

- `RUN-METRICS-1A`

## 9. Proposed `record_outcomes_1a` Contract Scope

`record_outcomes_1a` should define `{run_output_dir}/history/record_outcomes.jsonl`.

Scope:

- append-only per-record lifecycle outcomes
- one JSON object per record outcome
- safe record id
- status and timestamps
- attempt/retry counts if explicit attempt telemetry exists
- safe error summary
- optional worker id only if real worker execution exists
- links to related step outcome indexes

Out of scope:

- raw record data
- customer/account/person identifiers
- full browser evidence
- retry orchestration

Recommended schema id:

- `RECORD-OUTCOME-1A`

## 10. Proposed `attempt_history_1a` Contract Scope

`attempt_history_1a` should define `{run_output_dir}/history/attempt_history.jsonl`.

Scope:

- explicit attempt records for run, record, or step scope
- initial attempts
- future retries
- future resume-triggered attempts
- attempt status, timestamps, duration, and safe error summary

Out of scope:

- generating retry behavior
- deriving attempts from repeated smoke runs
- using directory count as attempt count

Recommended schema id:

- `ATTEMPT-HISTORY-1A`

## 11. Proposed Optional `record_manifest_1a` Contract Scope

`record_manifest_1a` should define `{run_output_dir}/history/record_manifest.json`.

Scope:

- metadata about the record source for a run
- safe record id strategy
- total expected record count only when the source manifest is explicit
- source artifact reference and fingerprint
- redaction policy metadata

Out of scope:

- raw source row values
- credentials
- downloaded file contents
- arbitrary worklist ingestion implementation

Recommended schema id:

- `RECORD-MANIFEST-1A`

Recommendation: include this optional contract in Milestone 12 because it prevents future ambiguity around how record ids and expected totals are established.

## 12. Required Fields Versus Nullable Fields

Required fields should establish identity, schema, and traceability.

Recommended always-required fields:

- `schema`
- `run_id`
- `timestamps` object
- `sources` or artifact references when applicable
- `status` for outcome records

Recommended nullable fields until runtime emits real telemetry:

- `finished_at_utc`
- `duration_ms`
- `manifest_records.total`
- `manifest_records.completed`
- `manifest_records.failed`
- `manifest_records.skipped`
- `attempts.total`
- `attempts.retry_attempts`
- `attempts.max_attempts`
- `attempts.continued_after_failure`
- `agents.worker_count`
- per-worker counts and durations
- `worker_id`
- `error`
- `record_manifest` source fingerprint if no source manifest exists

Do not use `0` when the actual value is unknown. Use `null`.

## 13. Safe Identifiers And Redaction Rules

Safe identifiers:

- `run_id`: existing run identifier
- `record_id`: deterministic, workflow-local, non-secret id such as `record_000001`
- `attempt_id`: deterministic, workflow-local id such as `attempt_000001`
- `worker_id`: generated non-secret id only when real worker execution exists

Forbidden identifiers:

- emails
- account numbers
- raw customer ids
- usernames tied to credentials
- tokens
- cookies
- session ids
- raw record payload values

Redaction rules:

- keep `secret_ref`, never secret value
- keep `selector_ref`, not sensitive DOM values
- keep error class/category/message only after reasonable truncation/redaction
- avoid screenshots or downloaded content in telemetry contracts

## 14. Artifact Path Conventions

Runtime output paths should remain relative to `run_output_dir`:

- `metrics/run_metrics.json`
- `history/record_manifest.json`
- `history/record_outcomes.jsonl`
- `history/attempt_history.jsonl`
- `history/run_manifest.json`
- `history/step_outcomes.jsonl`
- `report/run_report.json`
- `report/run_report.md`
- `logs/run.jsonl`

Contract example fixture paths should live outside generated artifact directories:

- `dev/fixtures/telemetry_contracts/*`

The examples should include a field such as:

- `"example_only": true`
- `"runtime_generated": false`

This prevents confusion with proof-run artifacts.

## 15. Backward Compatibility Expectations

Backward compatibility requirements:

- existing proof artifacts remain valid without `metrics/run_metrics.json`
- Milestone 10 viewer continues to render proof runs with absent metrics
- `REPORT-1A` remains valid without metrics
- `HISTORY-1A` and `HISTORY-1B` remain unchanged
- future contract files are additive
- fixtures are examples only and must not be required by runtime

No existing Milestone 1-11 smoke should be required to change for a plan/contract fixture milestone.

## 16. Viewer Compatibility Expectations

The viewer should not read example fixtures as proof artifacts.

Expected behavior:

- proof viewer reads optional `metrics/run_metrics.json` only from the selected run artifact directory
- absent metrics continues to show `Not captured yet`
- fixture examples under `dev/fixtures/telemetry_contracts/` are for contract validation only
- no viewer change is required for Milestone 12 unless a future implementation explicitly adds optional schema-demo rendering separated from proof artifacts

Preferred answer: do not connect the viewer to Milestone 12 fixtures.

## 17. Report Compatibility Expectations

Report modules should not change in Milestone 12.

Future report behavior may:

- include metrics if `metrics/run_metrics.json` exists
- summarize record outcomes when `record_outcomes.jsonl` exists
- summarize attempt history when `attempt_history.jsonl` exists

But Milestone 12 should keep this as contract documentation, not implementation.

## 18. How To Avoid Fake Metrics

Rules:

- examples must be labeled examples, not proof outputs
- examples must include `runtime_generated: false`
- nullable unknown operational fields should stay `null`
- do not place examples under run artifact directories
- do not make proof helpers copy examples into proof runs
- do not derive record counts from step counts
- do not derive retries from repeated smoke runs
- do not derive worker count from process/browser count
- do not derive continuation/resume from rerunning fixtures

## 19. How Fixture Examples Should Be Labeled As Examples, Not Runtime Proof

Each example fixture should include metadata such as:

```json
{
  "example_only": true,
  "runtime_generated": false,
  "notes": "Contract example only; not emitted by runtime."
}
```

JSONL example lines should include the same `example_only` and `runtime_generated` flags.

Docs should state:

- fixtures validate schema shape only
- fixtures are not production proof artifacts
- fixtures do not prove runtime telemetry writers exist
- fixtures do not prove retry, resume, worker, record manifest, or idempotency behavior

## 20. Positive Test Strategy

For implementation:

- `python dev/dev_smoke_production_milestone_12.py`

Positive assertions:

- all contract docs exist
- example JSON files parse
- example JSONL files parse line by line
- each example has expected `schema`
- required keys exist
- unknown/unproven operational fields remain nullable
- `example_only` is true
- `runtime_generated` is false
- no forbidden secret-like values appear
- no runtime modules are imported or invoked
- git status remains clean

## 21. Negative/Regression Test Strategy

Negative/regression assertions:

- malformed JSON/JSONL fixtures fail fixture-only smoke clearly
- missing required keys fail fixture-only smoke clearly
- examples with `runtime_generated: true` fail
- examples with non-null retry/resume/worker claims fail unless explicitly documented as synthetic examples
- examples containing obvious secret-bearing keys or placeholder secret values fail
- Milestone 10 viewer does not treat fixture examples as proof artifacts
- existing Milestone 10, proof CLI, and VAL smokes remain unaffected

## 22. File-By-File Implementation Options

Recommended Milestone 12 implementation scope:

- `docs/contracts/run_metrics_1a.md`
- `docs/contracts/record_outcomes_1a.md`
- `docs/contracts/attempt_history_1a.md`
- `docs/contracts/record_manifest_1a.md`
- `docs/analysis/operational_telemetry_contract.md`
- `dev/fixtures/telemetry_contracts/run_metrics_1a_example.json`
- `dev/fixtures/telemetry_contracts/record_outcomes_1a_example.jsonl`
- `dev/fixtures/telemetry_contracts/attempt_history_1a_example.jsonl`
- `dev/fixtures/telemetry_contracts/record_manifest_1a_example.json`
- `dev/dev_smoke_production_milestone_12.py`

Implementation should avoid:

- `RUN/*`
- `PIPE/*`
- `ACT/*`
- `HISTORY/*`
- `REPORT/*`
- `LOG/*`
- `VAL/*`
- `CLI/cli_production_proof_1a.py`
- `dev/production_proof_demo_viewer.py`
- Milestone 1-11 proof fixtures/smokes

## 23. Risk Assessment

Low risk:

- adding docs under a new `docs/contracts/` directory
- adding static example fixtures under `dev/fixtures/telemetry_contracts/`
- adding a fixture-only parseability smoke

Medium risk:

- example fixtures may be mistaken for runtime proof unless clearly labeled
- contract docs may over-specify fields before runtime writers exist

High risk and out of scope:

- adding telemetry writers prematurely
- changing report generation to depend on new metrics
- changing the viewer to present examples as real proof runs
- implementing retries/resume/workers

The main risk is epistemic: making examples look like capabilities. The docs and fixtures should be almost annoyingly clear about being examples.

## 24. Rollback Plan

If Milestone 12 remains plan-only:

- revert `docs/analysis/production_milestone_12_plan.md`

If the future implementation adds docs/fixtures/smoke:

- remove `docs/contracts/*`
- remove `docs/analysis/operational_telemetry_contract.md`
- remove `dev/fixtures/telemetry_contracts/`
- remove `dev/dev_smoke_production_milestone_12.py`

No runtime rollback should be needed because runtime modules should not change.

## 25. Milestone Exit Criteria

Milestone 12 is complete when:

- the plan recommends docs plus example fixtures, not runtime writers
- contract doc paths are named
- fixture paths are named
- fixture-only smoke strategy is defined
- run metrics, record outcomes, attempt history, and record manifest scopes are clear
- required versus nullable fields are clear
- safe identifiers and redaction rules are clear
- artifact path conventions are clear
- viewer/report backward compatibility is clear
- fake metric avoidance rules are explicit
- examples are clearly labeled as examples, not runtime proof
- runtime behavior, validation semantics, reports, viewer proof behavior, and milestone smokes are preserved

