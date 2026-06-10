# End-to-End Capability Assessment

**Date:** 2026-06-10  
**Scope:** Read-only production-readiness assessment of the current RPA_LIBRARY repository.  
**Question:** Does the repository currently support an end-to-end production RPA workflow?

## Executive Assessment

The repository contains most of the architectural pieces required for an end-to-end RPA workflow: capture, normalization, deploy bundle creation, validation, loading, execution, logging, reporting, diagnostics, retry helpers, and agent-assisted orchestration. The intended flow is visible in existing modules and in the repository audit:

`CAPTURE -> SNAP/WORKFLOW -> BUILD -> DEPLOY_BUNDLE -> VAL -> WORKFLOWS loader -> RUN/PIPE/ACT -> LOG/HISTORY/REPORT -> REASON/HEAL/STATE/AGENT`

Production readiness is **Partial**. The strongest path is deterministic bundle build/load/run with smoke-level validation. The main production blockers are integration confidence, action registry drift, validation gaps, dynamic import ambiguity, and incomplete hardening of retry/agent-assisted mutation paths.

This assessment focuses on production readiness, not code cleanliness.

## Capability Matrix

| # | Capability | Status | Risk |
|---|------------|--------|------|
| 1 | Capture a workflow | Partial | High |
| 2 | Convert captured actions into normalized workflow steps | Partial | High |
| 3 | Build a deploy bundle | Partial | Medium |
| 4 | Validate the deploy bundle | Partial | High |
| 5 | Load the deploy bundle | Complete | Medium |
| 6 | Execute the workflow | Partial | High |
| 7 | Record logs, manifests, and reports | Partial | Medium |
| 8 | Diagnose failures | Partial | Medium |
| 9 | Retry failed work | Partial | High |
| 10 | Support safe agent-assisted workflow generation | Partial | High |

## 1. Capture a Workflow

**Status:** Partial  
**Risk level:** High

**Evidence from actual modules/files**

- `CAPTURE/capture_1a_semi_auto.py` exposes `capture_session(...)` and supports a headed capture session.
- `CAPTURE/capture_1a_step_recorder.py` provides `event_to_schema_step(...)` and `Capture1AStepRecorder`.
- `WORKFLOW/workflow_2b_capture_js_event_recorder.py` provides JavaScript event listener helpers such as `install_capture_listeners_in_page_1a(...)`, `drain_capture_events_from_page_1a(...)`, and `capture_events_to_schema_steps_1a(...)`.
- `WORKFLOW/workflow_2c_capture_events_to_schema_steps_encoder.py` provides `encode_capture_events_to_schema_steps_1a(...)`.
- `dev/dev_smoke_capture_1a.py` and related smoke files indicate capture has smoke coverage.

**Gaps**

- Capture appears split between semi-automatic capture, step recording, JS event recording, and encoding; the production operator path is not clearly documented as a single command.
- Capture support is likely adequate for basic clicks/navigation/password typing, but production coverage for frames, popups, downloads, tab flows, dynamic selectors, and authenticated sessions is unclear.
- The audit reports missing type hints and unstable interfaces in capture/encoder modules.

**Recommended next action**

Create one documented golden-path capture command or runbook that produces a `CAPTURE_BUNDLE_1A` accepted by `BUILD-3H`, then smoke it against one real headed browser workflow.

## 2. Convert Captured Actions Into Normalized Workflow Steps

**Status:** Partial  
**Risk level:** High

**Evidence from actual modules/files**

- `WORKFLOW/workflow_1e_steps_normalizer.py` is indexed as `WORKFLOW-1E - Workflow Steps Normalizer`.
- `WORKFLOW/workflow_1f_selector_ref_first.py` is indexed as selector-reference enforcement.
- `WORKFLOW/workflow_2a_capture_actions_to_schema_steps.py`, `workflow_2b_capture_js_event_recorder.py`, and `workflow_2c_capture_events_to_schema_steps_encoder.py` cover capture-to-step conversion.
- `BUILD/build_1c_action_normalizer.py` and `BUILD/build_2d_step_grammar_gate.py` support action normalization/gating.

**Gaps**

- The repository audit flags hardcoded allowed-action lists across multiple modules, creating risk that capture output, schema, registry, and execution drift.
- The audit flags nested validation gaps for repeat blocks and incomplete type validation.
- Some generators intentionally emit `TODO` placeholders for unresolved selectors or unknown actions, which is useful during build but not production-runnable.

**Recommended next action**

Add a narrow production gate that rejects unresolved `TODO_*` fields and validates captured steps against the same action set used by the runtime action engine.

## 3. Build a Deploy Bundle

**Status:** Partial  
**Risk level:** Medium

**Evidence from actual modules/files**

- `BUILD/build_3a_deploy_bundle_format.py` defines the deploy bundle format.
- `BUILD/build_3b_bundle_fingerprint.py` computes bundle fingerprints.
- `BUILD/build_3c_deploy_bundle_builder.py` exposes `build_stamp_validate_deploy_bundle_1a(...)`.
- `BUILD/build_3f_deploy_bundle_stamper.py` stamps version/fingerprint metadata.
- `BUILD/build_3g_deploy_bundle_writer.py` writes deploy bundles.
- `BUILD/build_3h_capture_to_deploy_bundle_pipeline.py` exposes `build_write_deploy_bundle_1a_from_capture_bundle(...)` and `build_write_deploy_bundle_1a_from_capture_bundle_path(...)`.
- `dev/dev_smoke_build_3c_deploy_bundle_builder.py` and related `BUILD-3*` smoke tests exist.

**Gaps**

- The deploy bundle path has deterministic construction and smoke coverage, but production release criteria are not yet proven by an integrated E2E acceptance test.
- `BUILD-3H` documents the correct pipeline, but production readiness depends on upstream capture bundle quality and downstream validator strictness.
- Multiple CLI entry points exist for capture-to-bundle flows, which can make the intended production command ambiguous.

**Recommended next action**

Promote one capture-to-deploy-bundle command as the production path and verify it with a real sample capture bundle checked into a fixture directory.

## 4. Validate the Deploy Bundle

**Status:** Partial  
**Risk level:** High

**Evidence from actual modules/files**

- `VAL/val_2a_deploy_bundle_validator.py` exposes `validate_deploy_bundle_1a(...)` and `assert_deploy_bundle_1a(...)`.
- `WORKFLOWS/workflow_1g_deploy_bundle_loader.py` calls `assert_deploy_bundle_1a(...)` when loading bundles.
- `BUILD/build_3c_deploy_bundle_builder.py` and `BUILD/build_3g_deploy_bundle_writer.py` validate during build/write paths.
- `WORKFLOW/workflow_1f_selector_ref_first.py` supports selector-ref-first enforcement.

**Gaps**

- The repository audit flags registry/schema drift: several actions have missing implementation mappings and one action maps to a validator rather than an action handler.
- The audit flags non-strict validation bypass risk for selector references.
- Validation appears structurally strong but not yet sufficient to prove that every valid bundle is executable by `ACT-1A`.

**Recommended next action**

Make the production deploy validation profile strict by default and add a small action-registry-to-ACT implementation check to the release gate.

## 5. Load the Deploy Bundle

**Status:** Complete  
**Risk level:** Medium

**Evidence from actual modules/files**

- `WORKFLOWS/workflow_1g_deploy_bundle_loader.py` exposes `load_deploy_bundle_1a(...)`, `load_deploy_bundle_1a_from_path(...)`, and `extract_runnable_from_deploy_bundle_1a(...)`.
- The loader normalizes/stamps version and fingerprint metadata, validates via `VAL-2A`, and extracts `(workflow, selector_pack, run_meta)`.
- `RUN/run_1e_deploy_bundle_runner_adapter.py` uses the loader and delegates extracted assets to a runner.
- Loader `dev_smoke()` builds a bundle, loads it, extracts runtime assets, and checks legacy fingerprint compatibility.

**Gaps**

- The loader is solid as a boundary, but production confidence still depends on the validator and runner resolving the correct downstream implementation.
- `RUN-1E` is marked `Draft` and uses dynamic runner resolution.

**Recommended next action**

Keep the loader as-is for release, but pin the production runner callable explicitly in the deploy-bundle run command instead of relying on dynamic fallback resolution.

## 6. Execute the Workflow

**Status:** Partial  
**Risk level:** High

**Evidence from actual modules/files**

- `RUN/run_1a_workflow_runner.py` exposes the canonical `run_workflow(...)` entry point.
- `PIPE/pipe_1e_runner.py` exposes `run_pipeline(...)` and is described as the canonical execution integration layer.
- `PIPE/pipe_1a_run_orchestrator.py`, `PIPE/pipe_1c_steps_loader.py`, and `PIPE/pipe_1d_step_executor.py` provide lower-level execution orchestration.
- `ACT/act_1a_action_engine.py` is the canonical Selenium action execution layer.
- `ACT/act_1b_logging_integration.py` wraps action execution with structured step lifecycle logging.
- `CLI/cli_2b_unified.py` has a `run` command that calls `RUN-1A`.

**Gaps**

- The audit reports dynamic import chains in `RUN-1A`, `PIPE-1E`, `CLI`, and `AGENT` paths, making production failure modes harder to diagnose.
- The audit reports action registry gaps and incomplete handler mappings, which means a workflow can pass some checks but fail at execution.
- There are smoke tests, but no confirmed production E2E test that captures, bundles, loads, runs, logs, reports, and exits with a reliable production status.

**Recommended next action**

Create a single production E2E smoke workflow using a stable local or example target and run it through deploy-bundle execution, not just raw workflow execution.

## 7. Record Logs, Manifests, and Reports

**Status:** Partial  
**Risk level:** Medium

**Evidence from actual modules/files**

- `LOG/log_1a_structured_logging.py` provides JSONL-capable structured logging with secret redaction.
- `LOG/log_1b_error_taxonomy.py` classifies exceptions and redacts secrets.
- `HISTORY/history_1a_run_manifest.py`, `HISTORY/history_1a_store.py`, and `HISTORY/history_1b_step_outcomes.py` cover run manifests/history/outcomes.
- `STATE/state_1b_manifest_jsonl.py` provides JSONL manifest persistence.
- `REPORT/report_1a_generate.py`, `report_1b_run_report_markdown.py`, `report_1c_junit_xml.py`, and `report_1d_generate_reports.py` provide report generation.
- `REPORT/report_12a_release_manifest.py`, `report_12b_bundle_fingerprint.py`, and `report_12g_evidence_bundle_assembler.py` add release/evidence artifacts.
- `CLI/cli_2b_unified.py` reconstructs step logs from JSONL when possible.

**Gaps**

- Logging/reporting is present, but some paths are best-effort and may silently continue if report/log enrichment fails.
- The audit flags bare exception handling and silent fallback patterns in logging, state, and CLI modules.
- Production retention, alerting, and promotion policies exist but are hardcoded and not yet proven as deploy-time gates.

**Recommended next action**

Define the minimum required production artifacts for a run and fail the production smoke if any are missing: JSONL log, run manifest, step outcomes, bundle fingerprint, and markdown/JSON report.

## 8. Diagnose Failures

**Status:** Partial  
**Risk level:** Medium

**Evidence from actual modules/files**

- `REASON/reason_1a_diagnose.py` exposes failure diagnosis helpers and recommendations.
- `LOG/log_1b_error_taxonomy.py` classifies common runtime exceptions.
- `SNAP/snap_1a_failure_capture.py`, `snap_1b_screenshot.py`, and `snap_1c_persist.py` support failure evidence capture.
- `LEARN/learn_1a_failure_patterns.py` and `LEARN/learn_1b_selector_intelligence.py` provide history-based analysis.
- `DOCTOR` modules and Phase 12 smoke tests cover pre-run/release-readiness diagnostics.

**Gaps**

- Diagnosis appears rule-based and agent-friendly, but not guaranteed to have all context unless logging/snapshot artifacts are consistently produced.
- Some diagnosis and doctor resolution paths are best-effort, so failure diagnosis may degrade silently.
- There is not yet a clear production incident packet contract that ties logs, screenshots, manifests, and diagnosis together for every failed run.

**Recommended next action**

Add a production failure fixture and verify that one failed run always produces a diagnosis object plus a complete evidence bundle.

## 9. Retry Failed Work

**Status:** Partial  
**Risk level:** High

**Evidence from actual modules/files**

- `STATE/state_1c_retry_helpers.py` provides retry/resume helpers.
- `STATE/state_1d_manifest_row_helpers.py` standardizes manifest row shapes.
- `AGENT/agent_2a_autonomous_loop.py` retries up to `max_attempts`, records history, invokes diagnosis/healing, and can continue with a patched workflow.
- `RUN/run_12b_rollback_rerun_determinism.py` and `dev/dev_smoke_12_6_2_rollback_rerun_determinism.py` indicate rollback/rerun determinism coverage.

**Gaps**

- Retry exists at helper/orchestration level, but production semantics are not clearly proven for item-level idempotency, partial work, resume markers, and external side effects.
- `AGENT-2A` can retry without a patch when no patch is available, which may repeat the same failure.
- Retry safety depends on workflow actions being idempotent or guarded; that contract is not enforced by deploy validation.

**Recommended next action**

Define a minimal retry contract for production: manifest states, max attempts, idempotency notes per workflow, and a rule that repeated identical failure exits cleanly with evidence instead of looping through ineffective retries.

## 10. Support Safe Agent-Assisted Workflow Generation

**Status:** Partial  
**Risk level:** High

**Evidence from actual modules/files**

- `AGENT/agent_1a_context_pack.py` exports an agent context pack from existing generated artifacts.
- `BUILD/build_2a_nl_spec_generator.py` converts natural language into a build spec using deterministic rules.
- `BUILD/build_2b_plan_optimizer.py` optimizes generated plans without Selenium execution.
- `BUILD/build_2c_full_bundle.py` orchestrates natural-language build output.
- `SCHEMA/schema_1a_generate.py` and `REGISTRY/registry_1a_generate.py` expose schema/registry artifacts for AI handoff.
- `AGENT/agent_2a_autonomous_loop.py` coordinates run, snapshot, reason, heal, retry, report, and learning.
- `HEAL/heal_1a_patch_workflow.py` generates workflow patches from diagnosis.

**Gaps**

- Agent-assisted generation is deterministic and constrained in places, but it can emit TODO placeholders and patched workflow files.
- `HEAL-1A` may insert placeholder actions such as `TODO_IFRAME_SWITCH` when a safe supported action is unknown.
- The audit flags registry/schema drift and hardcoded action lists, which weaken the safety boundary for generated workflows.
- There is no single production approval gate that proves agent-generated or healed workflows are selector-ref-first, TODO-free, valid, executable, and reviewed before execution.

**Recommended next action**

Add a production agent safety gate: generated/healed workflows must pass strict grammar, selector-ref, no-TODO, registry-handler, and deploy-bundle validation before any execution attempt.

## Production Blockers vs Nice-to-Have Improvements

### Production Blockers

1. No confirmed single-command production E2E path from capture bundle to deploy bundle to validated execution artifacts.
2. Action registry/schema/runtime drift means validation cannot yet guarantee executability.
3. Strict production validation is not clearly enforced across all entry points.
4. Retry semantics are not yet production-safe for partial side effects and idempotency.
5. Agent-generated/healed workflow safety gates are incomplete.

### Nice-to-Have Improvements

1. Consolidate duplicate CLI entry points after the production path is proven.
2. Reduce duplicated helpers in Phase 12 modules.
3. Add stronger type hints on capture and CLI surfaces.
4. Externalize hardcoded production policies.
5. Rename ambiguous modules once runtime behavior is stable.

## Shortest Path to a Usable Production Release

1. Pick one production path and freeze it for release:
   `capture bundle -> BUILD-3H -> VAL-2A strict -> WORKFLOWS-1G -> RUN-1E/RUN-1A -> PIPE-1E -> ACT-1A -> LOG/HISTORY/REPORT`.
2. Add one checked-in golden capture bundle fixture and one checked-in deploy bundle fixture.
3. Add one production E2E smoke that validates, loads, executes against a stable target, and verifies required artifacts.
4. Add strict release gates: no TODOs, selector-ref-first, registry action has implementation, bundle fingerprint present, required reports/logs present.
5. Document the exact operator command sequence and expected outputs.

## Top 5 Blockers

1. **Executability gap:** validation does not yet prove every valid action maps to an actual `ACT-1A` handler.
2. **No proven full E2E release smoke:** existing smoke coverage is broad, but production readiness requires the whole path to run together.
3. **Capture-to-runtime contract risk:** capture/normalization can produce placeholders or unsupported shapes.
4. **Retry/idempotency ambiguity:** failed work can be retried without a proven side-effect contract.
5. **Agent safety gate incomplete:** generated or patched workflows need strict validation before execution.

## Top 5 Highest-ROI Implementation Tasks

1. Add a strict `production_e2e_smoke` that runs the selected golden path and verifies logs, manifest, report, and exit status.
2. Add a registry-to-runtime check that every allowed production action has a concrete handler in `ACT/act_1a_action_engine.py`.
3. Add a no-TODO/no-placeholder production validation rule for workflows and deploy bundles.
4. Define and enforce the required production run artifact set: JSONL log, manifest, step outcomes, bundle fingerprint, report.
5. Add a minimal retry safety contract to manifests: item id, attempt number, prior status, retry reason, and terminal failure evidence.

## Final Readiness Call

The repository is **close to an integrated production-capable framework**, but it should be treated as **not production-ready yet** until the golden E2E path is proven under strict validation and artifact checks. The next work should be narrow and release-oriented: prove the existing systems together, close the validation-to-execution gap, and add safety gates around retry and agent-assisted generation.
