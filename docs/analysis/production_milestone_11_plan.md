# Production Milestone 11 Plan

## 1. Milestone Definition

Production Milestone 11 should define the operational telemetry contracts needed to support the Run Operations Summary fields introduced visually in Milestone 10.

Milestone 10 made the viewer honest and readable: it displays captured run data and uses `Not captured yet` or `Not applicable for this fixture-bound proof` for missing operational metrics. Milestone 11 should decide what those missing metrics mean, where they should live, and which runtime/report/history boundaries should eventually own them.

Recommended milestone shape: design/contract only. Do not generate new telemetry from runtime yet.

## 2. Non-Goals

- Do not change runtime behavior.
- Do not change validation semantics.
- Do not add dependencies.
- Do not create a full app/dashboard.
- Do not add retry orchestration.
- Do not add multi-agent execution.
- Do not add resume/continuation behavior.
- Do not add external website support.
- Do not add downloads.
- Do not add credentials.
- Do not add arbitrary workflow execution.
- Do not make `REGISTRY/action_registry.json` authoritative.
- Do not broaden action coverage.
- Do not claim production readiness.

## 3. Files/Modules To Inspect

Files inspected for this plan:

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
- `dev/_smoke_artifacts/` structure, inspected only

Requested file not present on current `main` during inspection:

- `WORKFLOWS/workflows_1g_deploy_bundle_to_workflow.py`

The related deploy bundle workflow surface currently used by prior milestones is `WORKFLOWS/workflow_1g_deploy_bundle_loader.py`, but this plan does not require changing it.

## 4. Current Telemetry Artifacts

Current proof runs can produce:

- `history/run_manifest.json`
- `history/step_outcomes.jsonl`
- `report/run_report.json`
- `report/run_report.md`
- `logs/run.jsonl`
- `bundle/deploy_bundle_fingerprint.json`
- optional `metrics/run_metrics.json` can be read by the Milestone 10 viewer if present, but no writer currently creates it.

Current runtime summaries include:

- `run_id`
- `success`
- `errors`
- `step_logs` for single-item proof paths
- item-level `items`, `total`, `success_count`, and `failed` in `PIPE.pipe_1a_run_orchestrator`

Current action execution internals also contain step duration concepts, but those are not yet promoted into the proof artifacts as a stable operational metrics contract.

## 5. Current Gaps

Missing or not proven today:

- real manifest record counts
- per-record completed/failed/skipped counts
- retry attempts
- attempt history
- continuation/resume behavior
- multiple agents/workers
- per-agent throughput
- business idempotency / exactly-once behavior

Important distinction:

- status counts from `report/run_report.json` are step status counts, not record manifest counts
- repeated smoke runs are repeatability proof, not retry attempts
- one local process is not an agent/worker model
- rerunning a fixture is not continuation/resume behavior

## 6. Proposed `run_metrics.json` Contract

`metrics/run_metrics.json` should be the run-level operational summary artifact.

Recommended path:

- `{run_output_dir}/metrics/run_metrics.json`

Recommended schema id:

- `RUN-METRICS-1A`

Recommended ownership:

- future writer should live in a small telemetry/history module, not in the viewer
- viewer should remain a read-only consumer
- reports may include or summarize it after it exists

The contract should allow absent values without forcing fake telemetry:

- unknown metrics should be `null`
- not-applicable dimensions should be explicit strings or a `not_applicable` reason list
- values must identify their source when derived from existing artifacts

## 7. Proposed `record_manifest.json` Or `record_outcomes.jsonl` Contract

Record-level telemetry should be JSONL for outcomes.

Recommended path:

- `{run_output_dir}/history/record_outcomes.jsonl`

Optional run-level manifest metadata:

- `{run_output_dir}/history/record_manifest.json`

Rationale:

- JSONL supports append-only recording as records complete
- JSONL avoids rewriting one large file during long runs
- each record outcome can be independently redacted and audited

Minimum safe record identifier:

- `record_id`: deterministic, non-secret, workflow-local identifier
- if source data lacks a safe business id, generate a stable ordinal-scoped id such as `record_000001`
- never use raw customer identifiers, account numbers, emails, secrets, or credential-adjacent values as record ids

## 8. Proposed Attempt History Contract

Attempt history should be explicit JSONL.

Recommended path:

- `{run_output_dir}/history/attempt_history.jsonl`

Each line should represent one attempt against a run, record, or step, with clear scope:

- `scope`: `run`, `record`, or `step`
- `attempt_id`
- `attempt_index`
- `max_attempts`
- `parent_run_id`
- `record_id`, when record-scoped
- `step_index`, when step-scoped
- `status`
- `started_at_utc`
- `finished_at_utc`
- `duration_ms`
- `trigger`: `initial`, `retry`, `resume`, or `manual`
- safe error summary when failed

Do not infer attempt history from repeated smoke directories or repeated process invocations.

## 9. Proposed Retry Telemetry Model

Retry telemetry should describe behavior that actually happened, not behavior that could have happened.

Run-level fields:

- `attempts.total`
- `attempts.retry_attempts`
- `attempts.max_attempts`
- `attempts.retry_policy_id`
- `attempts.retry_policy_version`

Record-level fields:

- `attempt_count`
- `retry_count`
- `final_status`

Step-level fields:

- `attempt_count`
- `retry_count`
- `last_error`

Do not treat ACT-1A internal stale-click recovery as production retry orchestration unless it is explicitly surfaced as action-local retry telemetry with a clear scope such as `action_internal_retry`.

## 10. Proposed Continuation/Resume Telemetry Model

Continuation/resume telemetry should be explicit and separate from retries.

Recommended fields:

- `resume.enabled`
- `resume.resumed_from_run_id`
- `resume.resume_point`
- `resume.records_skipped_as_already_complete`
- `resume.records_replayed`
- `resume.continued_after_failure`
- `resume.reason`

Until runtime actually supports resume/continuation, these fields should be absent or `null`, and the viewer should continue to display `Not captured yet`.

## 11. Proposed Agent/Worker Telemetry Model

Worker telemetry should represent real execution workers only.

Recommended fields:

- `agents.worker_count`
- `agents.coordinator_id`
- `agents.workers[]`

Per worker:

- `worker_id`
- `role`
- `started_at_utc`
- `finished_at_utc`
- `duration_ms`
- `records_attempted`
- `records_completed`
- `records_failed`
- `records_skipped`
- `retry_attempts`
- `last_heartbeat_at_utc`

Do not infer worker count from local process count, browser count, or smoke helper count.

## 12. How Metrics Should Connect To Existing HISTORY Artifacts

Existing HISTORY artifacts should remain the foundation:

- `history/run_manifest.json` records run identity, workflow, bundle, timestamps, inputs, environment, and output location
- `history/step_outcomes.jsonl` records per-step status and safe step details

Milestone 11 should plan new HISTORY-adjacent artifacts:

- `history/record_outcomes.jsonl` for per-record lifecycle
- `history/attempt_history.jsonl` for attempts and retries
- optional `history/record_manifest.json` for source manifest metadata
- `metrics/run_metrics.json` for aggregated operational summary

`run_metrics.json` should reference HISTORY artifacts by relative path so reports and viewers can trace values back to source artifacts.

## 13. How Metrics Should Connect To REPORT Artifacts

`REPORT.report_1a_run_report` currently builds `report/run_report.json` from the run manifest and step outcomes.

Future report behavior should:

- load `metrics/run_metrics.json` if present
- include a `metrics` section in `run_report.json`
- keep old reports valid when metrics are absent
- render operational metrics in Markdown only when present
- display missing metrics as absent/unknown, not as zero

Milestone 11 should not change report generation unless the implementation is intentionally scoped to optional read/display support only.

## 14. How Metrics Should Connect To The Static Proof Viewer

Milestone 10 already made the viewer look for optional `metrics/run_metrics.json`.

Milestone 11 recommendation:

- preserve viewer as read-only artifact consumer
- do not add metrics writing to viewer
- optionally document or test a synthetic fixture-only `run_metrics.json` only if clearly marked as schema validation, not runtime proof
- keep current `Not captured yet` labels when metrics are absent

Viewer display should always distinguish:

- captured real metric
- not captured yet
- not applicable for fixture-bound proof

## 15. What Should Be Captured At Run Level

Run-level telemetry should include:

- run id
- workflow name/version
- bundle version/fingerprint
- run status
- started/finished/duration
- total records, completed records, failed records, skipped records
- total steps if meaningful at workflow level
- total attempts, retry attempts, max attempts
- continuation/resume status
- worker count
- artifact paths or relative references
- telemetry schema versions

Run-level data can safely include counts, timestamps, statuses, and artifact-relative paths.

## 16. What Should Be Captured At Record Level

Record-level telemetry should include:

- safe `record_id`
- record ordinal
- status: `pending`, `running`, `completed`, `failed`, `skipped`
- started/finished/duration
- attempt count
- retry count
- skipped reason, if skipped
- safe error category and message summary, if failed
- worker id, if real worker execution exists
- related step outcome indexes

Record-level telemetry should never store raw row data unless it has a separate redaction contract.

## 17. What Should Be Captured At Step Level

Step-level telemetry should include:

- step index
- action
- selector_ref or safe target reference
- status
- started/finished/duration
- attempt count
- action-local retry count, if explicitly surfaced
- safe result/evidence fields
- safe error class/message/category
- record id when the step belongs to a record

Existing `history/step_outcomes.jsonl` is the right starting point, but it lacks explicit result/evidence, record id, and attempt fields.

## 18. What Should Never Be Captured Because Of Secrets/Privacy

Never capture:

- passwords
- tokens
- cookies
- session headers
- raw secrets
- secret values resolved from secret refs
- full screenshots containing sensitive data unless a separate evidence redaction policy exists
- raw customer/account/person identifiers as record ids
- raw form payloads
- downloaded file contents unless an explicit artifact retention/redaction policy exists
- browser local storage/session storage values
- credentialed URLs

Safe references are acceptable:

- `secret_ref`
- `selector_ref`
- redacted error category/message
- stable non-secret record ids
- artifact-relative paths

## 19. How To Avoid Fake Or Inferred Metrics

Rules:

- derive duration only from artifact timestamps
- derive step status counts only from step outcomes
- derive record counts only from record telemetry artifacts
- derive retry counts only from attempt history or explicit retry events
- derive resume state only from explicit resume telemetry
- derive worker counts only from explicit worker telemetry
- do not use repeated smoke runs as retries
- do not use process count as worker count
- do not use step count as record count
- do not use directory count as attempt count

Unknown values must remain `null` in metrics and `Not captured yet` in the viewer.

## 20. How To Handle Fixture-Bound Proof Runs

Fixture-bound proof runs should remain honest:

- run status, workflow, run id, step outcomes, status counts, duration, artifact paths, and bundle fingerprint can be shown
- manifest record counts should remain `Not captured yet`
- retries should remain `Not captured yet`
- continuation/resume should remain `Not captured yet`
- agent/worker metrics should remain `Not captured yet`
- downloads and credentials should remain `Not applicable for this fixture-bound proof`

Fixture runs may include a schema fixture for metrics validation, but that must not be described as runtime-generated production telemetry.

## 21. How To Handle Future Real Manifest-Based Runs

For future manifest-based runs:

- require a record manifest or worklist contract with safe record ids
- emit one record outcome per record
- emit attempts only when attempts actually happen
- emit resume telemetry only when a run resumes from prior state
- emit worker telemetry only when there are real workers
- aggregate `run_metrics.json` from explicit artifacts
- include source artifact references in `run_metrics.json`

The first real manifest-based proof should be a local/static fixture, not an external website or credentialed workflow.

## 22. Proposed Schema Examples

Future `metrics/run_metrics.json`:

```json
{
  "schema": "RUN-METRICS-1A",
  "run_id": "production-proof-run",
  "status": "ok",
  "timestamps": {
    "started_at_utc": "2026-01-01T00:00:00+00:00",
    "finished_at_utc": "2026-01-01T00:00:02+00:00",
    "duration_ms": 2000
  },
  "manifest_records": {
    "total": null,
    "completed": null,
    "failed": null,
    "skipped": null
  },
  "attempts": {
    "total": null,
    "retry_attempts": null,
    "max_attempts": null,
    "continued_after_failure": null
  },
  "agents": {
    "worker_count": null,
    "workers": []
  },
  "sources": {
    "run_manifest": "history/run_manifest.json",
    "step_outcomes": "history/step_outcomes.jsonl",
    "record_outcomes": null,
    "attempt_history": null
  }
}
```

Future `history/record_outcomes.jsonl` line:

```json
{
  "schema": "RECORD-OUTCOME-1A",
  "run_id": "production-proof-run",
  "record_id": "record_000001",
  "record_index": 0,
  "status": "completed",
  "timestamps": {
    "started_at_utc": "2026-01-01T00:00:00+00:00",
    "finished_at_utc": "2026-01-01T00:00:02+00:00",
    "duration_ms": 2000
  },
  "attempt_count": 1,
  "retry_count": 0,
  "worker_id": null,
  "error": null
}
```

Future `history/attempt_history.jsonl` line:

```json
{
  "schema": "ATTEMPT-HISTORY-1A",
  "run_id": "production-proof-run",
  "attempt_id": "attempt_000001",
  "scope": "record",
  "record_id": "record_000001",
  "step_index": null,
  "attempt_index": 1,
  "max_attempts": 1,
  "trigger": "initial",
  "status": "completed",
  "timestamps": {
    "started_at_utc": "2026-01-01T00:00:00+00:00",
    "finished_at_utc": "2026-01-01T00:00:02+00:00",
    "duration_ms": 2000
  },
  "error": null
}
```

## 23. Backward Compatibility Plan

Compatibility rules:

- existing proof artifacts must remain valid
- existing viewer must render without `metrics/run_metrics.json`
- `run_report.json` should remain valid without a metrics section
- `history/run_manifest.json` and `history/step_outcomes.jsonl` schemas should not be broken
- new telemetry artifacts should be additive
- future readers should treat missing telemetry artifacts as unknown, not failure, unless the caller explicitly requires operational metrics

## 24. Positive Test Strategy

For Milestone 11 as a design/contract milestone:

- validate the plan document exists
- inspect that no runtime files changed
- keep existing Milestone 10 smoke as proof the viewer still handles missing metrics honestly

If optional schema fixtures are later added:

- add a fixture `metrics/run_metrics.json` with null unknowns
- verify viewer displays real values where present and `Not captured yet` where null/absent
- verify no metrics writer runs
- verify generated artifacts remain ignored

## 25. Negative/Regression Test Strategy

Negative assertions for any implementation following this plan:

- missing `metrics/run_metrics.json` must not fail viewer rendering
- malformed metrics JSON should fail clearly only when explicitly loaded
- zeros must not be substituted for unknown record/retry/worker metrics
- repeated fixture runs must not become retry counts
- step counts must not become record counts
- local process/browser count must not become worker count
- no secret-bearing fields are written into record ids, metrics, reports, or logs
- existing Milestone 1-10 smokes continue to pass

## 26. File-By-File Implementation Options

Recommended Milestone 11 implementation scope:

- `docs/analysis/production_milestone_11_plan.md`
  - add this contract plan

Optional contract-only follow-up files:

- `docs/analysis/operational_telemetry_contract.md`
  - detailed schemas for `run_metrics.json`, `record_outcomes.jsonl`, and `attempt_history.jsonl`

- `dev/fixtures/production_milestone_11/run_metrics_example.json`
  - schema example only, clearly not runtime-generated

Implementation to defer:

- runtime writer for `metrics/run_metrics.json`
- `HISTORY` writers for record outcomes or attempt history
- `REPORT` aggregation of metrics
- runtime retry/resume/worker support

Files to avoid touching in Milestone 11 unless the milestone is explicitly expanded:

- `RUN/*`
- `PIPE/*`
- `ACT/*`
- `WORKFLOWS/*`
- `VAL/*`
- `CLI/cli_production_proof_1a.py`
- `REGISTRY/*`
- Milestone 1-10 fixtures and smokes

## 27. Risk Assessment

Low risk:

- documenting schemas and telemetry ownership
- keeping viewer optional-read behavior unchanged
- preserving current missing-metric labels

Medium risk:

- adding schema fixtures, because they could be mistaken for runtime-generated proof
- adding optional report/viewer metrics tests, because they must not imply production telemetry exists

High risk and out of scope:

- generating metrics from runtime before record/retry/resume semantics are settled
- adding retry orchestration
- adding resume/continuation
- adding worker orchestration
- treating inferred counts as production metrics

The highest product risk is false confidence. Milestone 11 should make operational telemetry requirements precise, not make the proof look more complete than it is.

## 28. Rollback Plan

If Milestone 11 remains plan-only:

- revert `docs/analysis/production_milestone_11_plan.md`

If optional contract docs or fixtures are added later:

- remove the optional docs/fixtures
- leave runtime, report, history, and viewer behavior untouched

No runtime rollback should be required because this milestone should not alter runtime behavior.

## 29. Milestone Exit Criteria

Milestone 11 is complete when:

- the current telemetry artifacts are documented
- missing operational metrics are explicitly listed
- `run_metrics.json` is defined as a future run-level operational summary contract
- record-level telemetry has a proposed JSONL contract
- attempt/retry telemetry has a proposed explicit event contract
- continuation/resume telemetry is defined without claiming support exists
- worker/agent telemetry is defined without implementing multi-agent execution
- secret/privacy exclusions are documented
- fixture-bound proof handling remains honest
- future manifest-based run handling is outlined
- backward compatibility expectations are clear
- recommended implementation scope is contract/design first, not runtime behavior

