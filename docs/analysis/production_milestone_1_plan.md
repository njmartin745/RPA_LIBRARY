# Production Milestone 1 Plan

**Goal:** Prove deploy-bundle-to-execution golden path.  
**Source documents:** `docs/analysis/e2e_capability_assessment.md`, `docs/analysis/repository_audit.md`  
**Scope:** Minimal, release-oriented implementation plan only. No broad refactors, CLI consolidation, grammar-gate collapse, or new execution engine.

## Milestone Definition

Milestone 1 proves this exact deploy/runtime path:

`deploy bundle fixture -> VAL-2A strict production validation -> WORKFLOWS-1G loader -> RUN-1E/RUN-1A -> PIPE-1E -> ACT-1A -> LOG/HISTORY/REPORT artifacts`

The milestone is successful when one known-good deploy bundle fixture can be strictly validated, loaded, executed through the existing runtime path, and verified to produce the required production artifacts.

Capture-to-deploy-bundle generation is intentionally out of scope for Milestone 1. That path moves to Milestone 2 so the first production proof can isolate runtime validation, loading, execution, and audit artifacts.

## Non-Goals

- Do not refactor broad architecture.
- Do not consolidate CLIs.
- Do not collapse grammar gates.
- Do not create a new execution engine.
- Do not solve all registry/schema drift globally.
- Do not change agent-assisted generation behavior.
- Do not optimize code cleanliness.

## Exact Modules to Touch

Touch only the smallest set needed to prove the milestone.

### Required Touches

1. `VAL/val_2a_deploy_bundle_validator.py`
   - Add production validation checks or validation options for:
     - no TODO placeholders
     - selector-ref-first enforcement
     - registry action has implementation
     - bundle fingerprint present
   - Keep existing public behavior compatible; production checks should be opt-in or wired only through the production smoke path unless existing strict mode already covers them safely.

2. `RUN/run_1e_deploy_bundle_runner_adapter.py`
   - Use the existing deploy bundle loader and runner delegation.
   - Add only what is needed to support a deterministic production smoke invocation and artifact verification.
   - Prefer explicit runner injection for the test path to avoid relying on dynamic fallback resolution.

3. `REPORT/report_1d_generate_reports.py` or existing report generator surface used by the current runtime path
   - Ensure the milestone smoke can create or verify at least one markdown or JSON report.
   - Do not introduce a parallel reporting system.

4. `LOG/log_1a_structured_logging.py`, `HISTORY/history_1a_run_manifest.py`, `HISTORY/history_1b_step_outcomes.py`, or `STATE/state_1b_manifest_jsonl.py`
   - Touch only if the golden-path smoke cannot reliably produce or verify the required artifacts through existing hooks.
   - Prefer wiring existing outputs over adding new formats.

5. `dev/dev_smoke_production_milestone_1.py`
   - New focused smoke/acceptance test for this milestone.
   - Should orchestrate the path from fixture deploy bundle through strict validation, load, run, and artifact assertions.

### Avoid Touching

- `CLI/cli_1a_capture_to_deploy_bundle.py`, `CLI/cli_1b_capture_to_deploy_bundle.py`, `CLI/cli_1c_capture_to_deploy_bundle.py`, `CLI/cli_1d_capture_to_deploy_bundle_auto.py`
  - Avoid CLI consolidation in this milestone.
- `BUILD/build_2d_step_grammar_gate.py`, `BUILD/build_2e_workflow_grammar_gate.py`, `BUILD/build_2f_workflow_file_grammar_gate.py`, `BUILD/build_2g_workflow_tree_grammar_gate.py`
  - Avoid grammar-gate restructuring.
- `ACT/act_1a_action_engine.py`
  - Avoid touching unless the chosen golden fixture uses an action that is already intended to work but cannot be executed due to a small handler mapping issue.
- `AGENT/*`, `HEAL/*`, `REASON/*`
  - Out of scope for Milestone 1.

## Exact Fixture Files Needed

Add fixtures under a dedicated milestone directory so they do not blend into runtime data:

1. `dev/fixtures/production_milestone_1/deploy_bundle_golden.json`
   - Minimal known-good `DEPLOY_BUNDLE_1A`.
   - Should include:
     - one `open` step to a stable target
     - one selector-based step using `selector_ref`
     - a `selector_pack` containing the referenced selector
     - `version` and `fingerprint.sha256`
   - Keep it small enough to inspect by eye.

2. `dev/fixtures/production_milestone_1/deploy_bundle_todo_placeholder.json`
   - Same deploy bundle shape as golden fixture but includes an unresolved value such as `TODO_SELECTOR_1` or `TODO_ACTION`.
   - Used only for rejection testing.

3. `dev/fixtures/production_milestone_1/deploy_bundle_registry_failure.json`
   - A deploy bundle with an action that is present in schema/registry but intentionally lacks a runtime implementation mapping.
   - Used only to prove registry-action mapping failure is detected before execution.

4. `dev/fixtures/production_milestone_1/site/index.html`
   - Static local HTML target for deterministic browser execution.
   - Should include a stable element for the selector-ref step.
   - Prefer local file or simple local static server fixture to avoid network dependence.

5. `dev/fixtures/production_milestone_1/expected_artifacts.json`
   - Lists required artifact filenames or patterns:
     - JSONL log
     - run manifest
     - step outcomes
     - bundle fingerprint
     - markdown or JSON report

## Required Production Artifacts

The positive golden-path test must fail if any required artifact is missing or empty.

1. **JSONL log**
   - Produced through existing `LOG-1A` / pipeline logging path.
   - Must contain at least one step lifecycle event or structured run event.

2. **Run manifest**
   - Produced through existing `HISTORY` or `STATE` manifest support.
   - Must include run id, workflow/bundle identity, status, and artifact references when available.

3. **Step outcomes**
   - Produced through existing `HISTORY-1B`, `ACT-1A` outcomes, or report step logs.
   - Must include step index, action, status, and failure details when applicable.

4. **Bundle fingerprint**
   - Produced by `BUILD-3B` / `BUILD-3F`.
   - Must be present on the deploy bundle before execution.

5. **Markdown or JSON report**
   - Produced through existing `REPORT-1A` / `REPORT-1D` path.
   - Must summarize success/failure and include step-level results or a pointer to them.

## Minimum Validation Gates

These gates should run before the positive fixture is executed and should be directly asserted in tests.

1. **No TODO placeholders**
   - Reject any workflow, selector pack, or deploy bundle value containing unresolved placeholders such as `TODO`, `TODO_*`, or `TODO:`.
   - Applies recursively to nested dict/list values.

2. **Selector-ref-first**
   - Production deploy bundles must use `selector_ref` for selector-based actions.
   - Raw selectors may exist in `selector_pack`, not directly as runnable step selectors when a selector reference is required.

3. **Registry action has implementation**
   - Every action in the deploy bundle must map to a concrete runtime implementation before execution.
   - For Milestone 1, this can be a narrow checker that validates actions used by the fixture against `ACT/act_1a_action_engine.py` handler availability.

4. **Deploy bundle fingerprint present**
   - `version` and `fingerprint.sha256` must be present on the deploy bundle fixture before `WORKFLOWS-1G`.

5. **Required artifacts produced**
   - Positive golden-path run must produce all required artifacts listed above.

## Test Strategy

### 1. Positive Golden-Path Test

**File:** `dev/dev_smoke_production_milestone_1.py`

Flow:

1. Load `dev/fixtures/production_milestone_1/deploy_bundle_golden.json`.
2. Validate with `VAL-2A` strict production gates.
3. Load with `WORKFLOWS/workflow_1g_deploy_bundle_loader.py`.
4. Execute with `RUN/run_1e_deploy_bundle_runner_adapter.py`, using the existing `RUN-1A` / `PIPE-1E` / `ACT-1A` path.
5. Write artifacts to a temporary milestone output directory.
6. Assert JSONL log, run manifest, step outcomes, bundle fingerprint, and markdown or JSON report exist and are non-empty.

Pass condition:

- The run exits successfully and all required artifacts are present.

### 2. Negative TODO-Placeholder Rejection Test

**File:** `dev/dev_smoke_production_milestone_1.py`

Flow:

1. Load `deploy_bundle_todo_placeholder.json`.
2. Attempt production validation before execution.
3. Assert validation fails with a clear issue pointing to the unresolved placeholder.

Pass condition:

- The bundle is rejected before execution.

### 3. Registry-Action Mapping Failure Test

**File:** `dev/dev_smoke_production_milestone_1.py`

Flow:

1. Load the registry-mapping failure fixture.
2. Run production validation.
3. Assert validation fails before execution because at least one action lacks a concrete runtime implementation.

Pass condition:

- The failure is reported as a validation issue, not as a Selenium/runtime error.

## File-by-File Implementation Plan

### `VAL/val_2a_deploy_bundle_validator.py`

Add minimal production-gate helpers:

- Recursive placeholder detector.
- Action implementation checker for actions present in a deploy bundle.
- Validation issue messages that include JSON-pointer-like paths.
- Optional production validation flag if needed, such as `production=True`, without changing default non-production callers.

Do not rewrite validator structure. Extend the current issue collection pattern.

### `RUN/run_1e_deploy_bundle_runner_adapter.py`

Use existing loader and runner adapter behavior.

Possible minimal additions:

- Allow the production smoke to pass explicit `runner` and `runner_kwargs`.
- Ensure run metadata from `WORKFLOWS-1G` can be surfaced to artifact/report generation.

Do not replace dynamic resolution globally.

### `REPORT/report_1d_generate_reports.py`

Use the existing report generation surface to produce the milestone report.

Possible minimal additions:

- Accept the normalized golden-path run summary if the current function cannot.
- Ensure JSON or markdown output can be written into the milestone artifact directory.

Do not create a new reporting format.

### `dev/dev_smoke_production_milestone_1.py`

Create a single focused smoke file that contains:

- `test_positive_golden_path()` or equivalent callable smoke section.
- `test_reject_todo_placeholder()` or equivalent callable smoke section.
- `test_reject_registry_mapping_failure()` or equivalent callable smoke section.
- Temporary output directory handling.
- Direct assertions for required artifacts.

Keep this as the milestone proof, not a broad test framework.

### `dev/fixtures/production_milestone_1/deploy_bundle_golden.json`

Create the smallest complete deploy bundle accepted by `VAL-2A` strict production validation and `WORKFLOWS-1G`.

Use stable selectors, selector references, a valid fingerprint, and actions that are already supported by `ACT-1A`.

### `dev/fixtures/production_milestone_1/deploy_bundle_todo_placeholder.json`

Create the smallest invalid deploy bundle that demonstrates placeholder rejection.

### `dev/fixtures/production_milestone_1/deploy_bundle_registry_failure.json`

Create the smallest invalid fixture that demonstrates action-mapping rejection.

### `dev/fixtures/production_milestone_1/site/index.html`

Create a deterministic target page for the positive run.

Keep it static and local. Avoid external network dependence.

### `dev/fixtures/production_milestone_1/expected_artifacts.json`

Define artifact names or glob patterns checked by the smoke.

This keeps the smoke explicit and easy to update without hiding requirements in code.

## Estimated Effort

| Work item | Estimate |
|-----------|----------|
| Add production validation gates in `VAL-2A` | 3-5 hours |
| Create milestone fixtures | 1-2 hours |
| Add positive golden-path smoke | 4-6 hours |
| Add two negative validation tests | 2-3 hours |
| Wire/report required artifacts through existing modules | 3-5 hours |
| Local verification and documentation updates | 1-2 hours |

**Total estimate:** 14-23 hours

## Milestone 2 Preview

Milestone 2 should prove the upstream generation path:

`capture bundle -> BUILD-3H -> deploy bundle`

Milestone 2 should start only after Milestone 1 proves that a known-good deploy bundle can be validated, loaded, executed, and audited. Its scope should include capture bundle fixture design, `BUILD-3H` execution, deploy bundle stamping/fingerprinting, and compatibility with the Milestone 1 production validation gates.

## Rollback Risk

**Risk level:** Low to Medium

Rollback should be straightforward if production gates are added as opt-in behavior or only used by the milestone smoke. The main rollback risk is accidental tightening of `VAL-2A` default behavior, which could break existing dev smoke tests or legacy bundle loading.

Rollback plan:

1. Revert the milestone smoke and fixture files.
2. Disable the production validation flag or remove the new gate calls.
3. Leave existing build/load/run behavior unchanged.

## Compatibility Risk

**Risk level:** Medium

Compatibility concerns:

- Existing bundles with raw selectors may fail if selector-ref-first enforcement is made default instead of production-only.
- Existing generated workflows with `TODO` notes may be rejected if placeholder checks are applied broadly.
- Registry-action checks may expose existing known drift from `REGISTRY/action_registry.json`.
- Artifact checks may fail on environments without a working browser driver if the positive smoke uses real Selenium execution.

Compatibility controls:

- Keep stricter gates scoped to the production milestone path first.
- Use a local static HTML fixture to avoid network instability.
- Prefer existing actions already handled by `ACT-1A`.
- Keep required artifact checks in the milestone smoke until the production path is proven.

## Milestone Exit Criteria

Milestone 1 is complete when:

1. The positive golden-path smoke passes locally.
2. The TODO-placeholder fixture is rejected before execution.
3. The registry-action mapping failure fixture is rejected before execution.
4. The positive run produces:
   - JSONL log
   - run manifest
   - step outcomes
   - bundle fingerprint
   - markdown or JSON report
5. No broad architecture refactor was required.
6. Existing runtime entry points remain compatible for non-production callers.
