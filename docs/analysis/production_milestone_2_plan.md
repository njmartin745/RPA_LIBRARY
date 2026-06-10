# Production Milestone 2 Plan

**Goal:** Prove capture-bundle-to-deploy-bundle generation.  
**Context:** Production Milestone 1 proves that a known-good deploy bundle can be strictly validated, loaded, executed through the existing runtime path, and verified for artifacts.  
**Scope:** Planning only. No runtime code, fixtures, tests, broad refactors, CLI consolidation, grammar-gate collapse, or new execution engine.

## Milestone Definition

Milestone 2 proves this exact upstream generation path:

`capture bundle fixture -> BUILD-3H -> deploy bundle -> VAL-2A production validation gates from Milestone 1`

The milestone is successful when one deterministic capture bundle fixture can be converted by the existing `BUILD-3H` pipeline into a deploy bundle that passes `VAL-2A` production validation with:

- no TODO placeholders
- selector-ref-first deploy steps
- registry action has implementation
- deploy bundle fingerprint present

Milestone 2 does not need to execute the generated bundle. Execution was proven separately in Milestone 1. This milestone should only prove that upstream generation can produce a production-valid deploy artifact compatible with the runtime proof.

## Non-Goals

- Do not execute the generated deploy bundle.
- Do not re-prove LOG/HISTORY/REPORT artifact generation.
- Do not implement capture UI/session recording.
- Do not implement Milestone 1 runtime behavior again.
- Do not refactor broad architecture.
- Do not consolidate CLIs.
- Do not collapse grammar gates.
- Do not create a new execution engine.
- Do not make `REGISTRY/action_registry.json` authoritative yet.
- Do not optimize code cleanliness or module structure.

## Exact Modules to Inspect

Inspect these modules before implementation to confirm current behavior and avoid duplicate systems:

1. `BUILD/build_3h_capture_to_deploy_bundle_pipeline.py`
   - Public functions:
     - `load_json_mapping_from_path(...)`
     - `build_write_deploy_bundle_1a_from_capture_bundle(...)`
     - `build_write_deploy_bundle_1a_from_capture_bundle_path(...)`
   - Main concern: whether it can call downstream validation with `production=True` or whether the smoke should perform production validation after `BUILD-3H` returns.

2. `BUILD/build_3c_deploy_bundle_builder.py`
   - Public functions:
     - `build_stamp_validate_deploy_bundle_1a(...)`
     - `build_stamp_validate_deploy_bundle_1a_with_report(...)`
   - Main concern: production validation currently needs to be reused without changing default behavior for non-production callers.

3. `BUILD/build_3a_deploy_bundle_format.py`
   - Main concern: capture bundle shape conversion into `DEPLOY_BUNDLE_1A`, workflow, selector pack, and metadata.

4. `BUILD/build_3f_deploy_bundle_stamper.py`
   - Public function:
     - `ensure_deploy_bundle_version_fingerprint_1a(...)`
   - Main concern: deterministic `version` and `fingerprint.sha256` stamping.

5. `BUILD/build_3b_bundle_fingerprint.py`
   - Main concern: deterministic fingerprint computation and key exclusion rules.

6. `BUILD/build_3g_deploy_bundle_writer.py`
   - Main concern: write path validation and whether post-write output remains identical to the returned deploy bundle.

7. `VAL/val_2a_deploy_bundle_validator.py`
   - Public functions:
     - `validate_deploy_bundle_1a(..., production=True)`
     - `assert_deploy_bundle_1a(..., production=True)`
   - Main concern: reuse Milestone 1 production gates after generation.

8. `WORKFLOW/workflow_1f_selector_ref_first.py`
   - Main concern: selector-ref-first conversion or validation behavior used by the build path.

9. `SNAP/snap_1a_workflow_capture.py`
   - Main concern: `ALLOWED_WORKFLOW_ACTIONS` and capture/workflow action compatibility.

10. `ACT/act_1a_action_engine.py`
    - Main concern: existing `_ACTIONS` map used by Milestone 1 production validation to prove runtime action implementation availability.

## Exact Modules Likely to Touch

Touch only the smallest set needed to prove the milestone.

1. `dev/dev_smoke_production_milestone_2.py`
   - New focused smoke file for Milestone 2.
   - Should load capture fixtures, invoke `BUILD-3H`, validate the generated deploy bundle with `VAL-2A production=True`, and assert deterministic output.

2. `BUILD/build_3h_capture_to_deploy_bundle_pipeline.py`
   - Touch only if the implementation needs an opt-in `production` validation flag inside the pipeline.
   - Prefer preserving current defaults and adding optional parameters rather than changing existing behavior.
   - If production validation can safely happen in the smoke after `BUILD-3H`, do not touch this file.

3. `BUILD/build_3c_deploy_bundle_builder.py`
   - Touch only if production validation needs to be exposed through `BUILD-3C` for a cleaner `BUILD-3H` implementation.
   - Keep non-production behavior unchanged.

4. `VAL/val_2a_deploy_bundle_validator.py`
   - Touch only if Milestone 1 production gates need a narrow bug fix for generated deploy bundles.
   - Do not add new production gates unless the generated bundle exposes a direct blocker to the stated milestone.

5. `BUILD/build_3a_deploy_bundle_format.py`
   - Touch only if the generated deploy bundle cannot preserve selector references, source metadata, or workflow shape required by existing validation.

## Fixture Files Needed

Create fixtures only during implementation, not during planning.

1. `dev/fixtures/production_milestone_2/capture_bundle_golden.json`
   - Minimal deterministic `CAPTURE_BUNDLE_1A`.
   - Should include:
     - `schema_id: CAPTURE_BUNDLE_1A`
     - stable `name`
     - workflow with one `open` step and one selector-based action already expressible as `selector_ref`
     - selector pack containing the referenced selector
   - Must not contain timestamps, random IDs, environment-specific paths, or TODO placeholders.

2. `dev/fixtures/production_milestone_2/capture_bundle_todo_placeholder.json`
   - Same basic shape as the golden capture bundle, but with one unresolved `TODO` value in workflow, selector pack, or metadata.
   - Used to prove the generated deploy bundle or production validation rejects unresolved placeholders before runtime.

3. `dev/fixtures/production_milestone_2/capture_bundle_raw_selector.json`
   - Capture bundle containing a selector-based step with a raw selector that should be converted or rejected depending on existing `BUILD-3H` behavior.
   - Used to prove Milestone 2 does not emit production deploy steps with raw runnable selectors.

4. `dev/fixtures/production_milestone_2/capture_bundle_registry_failure.json`
   - Capture bundle with an action that reaches deploy validation but has no `ACT-1A` runtime implementation.
   - Used to prove Milestone 1 registry/action implementation validation is reused in the upstream build proof.

5. `dev/fixtures/production_milestone_2/expected_deploy_bundle_golden.json`
   - Optional but recommended golden output fixture.
   - Should be used only if the generated deploy bundle is fully deterministic and stable enough for exact JSON comparison.
   - If exact comparison proves too brittle, replace this with explicit structural assertions in the smoke.

6. `dev/fixtures/production_milestone_2/expected_validation_report.json`
   - Optional expected validation report shape for the golden bundle.
   - Use only for stable fields such as `ok`, required schema id, and empty `errors`.

## Validation Gates to Reuse From Milestone 1

Milestone 2 should call `VAL.validate_deploy_bundle_1a(..., production=True)` or `VAL.assert_deploy_bundle_1a(..., production=True)` on the generated deploy bundle.

Required gates:

1. **No TODO placeholders**
   - Generated deploy bundles must not contain unresolved placeholder values anywhere in nested JSON.

2. **Selector-ref-first**
   - Generated deploy bundle steps must use `selector_ref` for selector-based actions.
   - Raw selectors may remain in `selector_pack.selectors`, not directly on runnable deploy steps.

3. **Registry action has implementation**
   - Every generated deploy step action must have a current runtime implementation.
   - For this milestone, continue using the Milestone 1 scoped `ACT-1A` implementation check.

4. **Deploy bundle fingerprint present**
   - Generated deploy bundles must contain non-empty `version` and valid `fingerprint.sha256`.

## Positive Test Strategy

Add one focused smoke:

**File:** `dev/dev_smoke_production_milestone_2.py`

Flow:

1. Load `dev/fixtures/production_milestone_2/capture_bundle_golden.json`.
2. Call `BUILD.build_3h_capture_to_deploy_bundle_pipeline.build_write_deploy_bundle_1a_from_capture_bundle_path(...)`.
3. Write output to an ignored smoke artifact path such as `dev/_smoke_artifacts/production_milestone_2/deploy_bundle_golden.generated.json`.
4. Load the generated deploy bundle from disk.
5. Validate using `VAL-2A` with:
   - `require_version_fingerprint=True`
   - `require_selector_ref=True`
   - `production=True`
6. Assert the generated bundle contains:
   - `schema_id: DEPLOY_BUNDLE_1A`
   - stable `name`
   - workflow steps
   - selector pack
   - source metadata indicating `CAPTURE_BUNDLE_1A`
   - valid `version`
   - valid `fingerprint.sha256`
7. Assert deterministic generation by running the same `BUILD-3H` path twice from the same capture fixture and comparing canonical JSON output or matching fingerprints.

Pass condition:

- The generated deploy bundle passes production validation.
- Repeated generation from identical input produces identical deploy bundle content or identical canonical fingerprint.

## Negative Test Strategy

Keep negative tests pre-runtime and focused on production validation.

1. **TODO placeholder rejection**
   - Input: `capture_bundle_todo_placeholder.json`
   - Flow:
     - Run through `BUILD-3H` if the builder currently allows it.
     - Validate generated deploy bundle with `production=True`.
     - If `BUILD-3H` rejects earlier, assert the error is clear and no deploy bundle is accepted.
   - Pass condition:
     - Placeholder-containing input does not produce a production-valid deploy bundle.

2. **Raw selector / selector-ref-first failure**
   - Input: `capture_bundle_raw_selector.json`
   - Flow:
     - Run through `BUILD-3H`.
     - Validate generated deploy bundle with `production=True`.
   - Pass condition:
     - Either `BUILD-3H` converts runnable raw selectors to `selector_ref`, or production validation rejects the generated deploy bundle.
     - A generated deploy bundle with raw runnable selectors must not pass.

3. **Registry/action implementation failure**
   - Input: `capture_bundle_registry_failure.json`
   - Flow:
     - Run through `BUILD-3H` if allowed by grammar.
     - Validate generated deploy bundle with `production=True`.
   - Pass condition:
     - Unsupported or unimplemented action is rejected before runtime.

## File-by-File Implementation Plan

### `dev/dev_smoke_production_milestone_2.py`

Create a single focused smoke containing:

- `test_positive_capture_to_deploy_bundle()` or equivalent section.
- `test_reject_todo_placeholder()` or equivalent section.
- `test_selector_ref_first_generation_or_rejection()` or equivalent section.
- `test_reject_registry_mapping_failure()` or equivalent section.
- Temporary/ignored output handling under `dev/_smoke_artifacts/production_milestone_2/`.
- Canonical JSON helper local to the smoke if needed for deterministic comparison.

The smoke should print:

`DEV_SMOKE_OK: production_milestone_2`

### `dev/fixtures/production_milestone_2/capture_bundle_golden.json`

Create the smallest capture bundle that can generate a production-valid deploy bundle.

Preferred workflow:

- `open` a deterministic local or example URL string.
- `click_selector` using `selector_ref`.

Do not include runtime-only artifact expectations; those belong to Milestone 1.

### `dev/fixtures/production_milestone_2/capture_bundle_todo_placeholder.json`

Create a minimal capture bundle that carries one unresolved placeholder into build/validation.

The placeholder should be obvious and isolated, such as `TODO_SELECTOR` or `TODO_URL`.

### `dev/fixtures/production_milestone_2/capture_bundle_raw_selector.json`

Create a minimal capture bundle that tests whether BUILD produces selector-ref-first deploy output.

Use this to decide whether implementation needs a narrow BUILD-3A/3H fix or whether current behavior already converts correctly.

### `dev/fixtures/production_milestone_2/capture_bundle_registry_failure.json`

Create a minimal capture bundle with an action that should fail production action implementation validation before runtime.

Prefer an action shape that reaches `VAL-2A` cleanly so the smoke tests the intended production gate, not unrelated malformed JSON.

### `dev/fixtures/production_milestone_2/expected_deploy_bundle_golden.json`

Add only if exact deterministic output is stable.

If added, keep it compact and compare canonical JSON, not pretty-print formatting.

### `BUILD/build_3h_capture_to_deploy_bundle_pipeline.py`

First implementation preference:

- No change.
- Let the smoke call existing `BUILD-3H`, then call `VAL-2A production=True` on the result.

Fallback minimal change:

- Add an optional `production: bool = False` parameter and pass it through to downstream validation if needed.
- Preserve default behavior.

### `BUILD/build_3c_deploy_bundle_builder.py`

First implementation preference:

- No change.

Fallback minimal change:

- Add optional `production: bool = False` to report/fail-fast builder functions only if `BUILD-3H` must expose a production validation mode.
- Preserve default behavior.

### `VAL/val_2a_deploy_bundle_validator.py`

First implementation preference:

- No change.

Fallback minimal change:

- Fix only defects where a generated bundle that should satisfy Milestone 1 gates is incorrectly rejected or incorrectly accepted.
- Keep new behavior opt-in under `production=True`.

## Estimated Effort

| Work item | Estimate |
|-----------|----------|
| Inspect BUILD-3H/3C/3A/3F/3G and VAL-2A behavior | 1-2 hours |
| Design deterministic capture fixtures | 1-2 hours |
| Add positive capture-to-deploy smoke | 2-4 hours |
| Add negative validation cases | 2-3 hours |
| Add optional BUILD production flag only if needed | 1-3 hours |
| Local verification and cleanup | 1 hour |

**Total estimate:** 8-15 hours

## Compatibility Risks

**Risk level:** Low to Medium

- If production validation is added directly to `BUILD-3H` defaults, existing non-production capture-to-bundle callers could start failing on TODO placeholders or raw selectors.
- Existing capture bundles may rely on raw selector fields that are currently normalized later.
- Exact golden deploy-bundle comparison may be brittle if fingerprint canonicalization intentionally evolves.
- Registry/action implementation validation still uses the Milestone 1 scoped `ACT-1A` `_ACTIONS` check, not the future authoritative registry.

Compatibility controls:

- Keep stricter production validation opt-in or smoke-scoped.
- Prefer validating generated output after `BUILD-3H` rather than changing builder defaults.
- Compare deterministic fingerprints or canonical JSON, not formatting.
- Keep registry-authoritative validation as a later milestone.

## Rollback Risks

**Risk level:** Low

Rollback should be straightforward if implementation is limited to fixtures, one smoke file, and optional opt-in production flags.

Rollback plan:

1. Remove `dev/dev_smoke_production_milestone_2.py`.
2. Remove `dev/fixtures/production_milestone_2/`.
3. Revert optional `BUILD-3H` / `BUILD-3C` production flag wiring if added.
4. Leave Milestone 1 validation gates unchanged.

Primary rollback concern:

- Accidentally changing default `BUILD-3H` or `BUILD-3C` validation behavior. Avoid this by making production validation explicit.

## Milestone Exit Criteria

Milestone 2 is complete when:

1. `python dev/dev_smoke_production_milestone_2.py` passes locally.
2. A deterministic golden capture bundle produces a deploy bundle through `BUILD-3H`.
3. The generated deploy bundle passes `VAL-2A` with `production=True`.
4. The generated deploy bundle includes valid `version` and `fingerprint.sha256`.
5. The generated deploy bundle is selector-ref-first for runnable selector steps.
6. The generated deploy bundle contains no TODO placeholders.
7. Every generated action has a current `ACT-1A` runtime implementation under the Milestone 1 check.
8. Repeated generation from the same capture bundle is deterministic.
9. Negative placeholder input does not produce a production-valid deploy bundle.
10. Negative selector-ref or registry/action input does not produce a production-valid deploy bundle.
11. No runtime execution path is modified.
12. No broad architecture refactor, CLI consolidation, grammar-gate collapse, or new execution engine is introduced.
