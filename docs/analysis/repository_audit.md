# Repository Audit Report

**Date:** 2026-06-09
**Scope:** Full codebase — 182 indexed modules, 160 smoke tests
**Auditor:** Automated structural + source analysis

---

# Executive Summary

## Overall Repository Health Score: 6.5 / 10

The framework has a strong deterministic architecture and excellent test coverage for smoke scenarios, but suffers from significant module sprawl, code duplication, unstable module interfaces, and incomplete type coverage. The Phase 12 production-readiness layer introduced substantial technical debt through copy-paste patterns and hardcoded policies.

### Top Strengths

1. **Deterministic-by-design pipeline** — Every artifact is fingerprinted (SHA-256), every output is reproducible, no timestamps or randomness in generated bundles
2. **Comprehensive smoke test coverage** — 160 dev_smoke tests covering every milestone module; smoke-to-module mapping is machine-tracked in AGENT_PACKET
3. **Declarative workflow architecture** — Clean separation between workflow intent (JSON) and execution mechanics (Python runtime); 9-action grammar is enforced at multiple gates
4. **Selector-ref-first policy** — Prevents raw CSS/XPath in production workflows; enforced at build, validate, and load time
5. **Canonical execution path** — Single clear path from RUN-1A through PIPE-1E/PIPE-1A to ACT-1A; all paths converge

### Top Risks

1. **Module count explosion** — 182 indexed modules (+205 files missing headers = 387 total .py files) for a 9-action framework; extreme granularity creates navigation and maintenance burden
2. **Pervasive code duplication** — `_truthy()`, `_parse_bool()`, `_sha256_hex()`, `write_text_file()`, `_md()`, module discovery patterns, and canonical JSON dumps are reimplemented 3–7 times each
3. **Unstable module interfaces** — 15+ "best-effort" dynamic import chains with fallback naming; no explicit contracts (Protocol/ABC) between layers
4. **Registry/schema drift** — 6 of 9 actions have empty implementation mappings; `click_selector` mapped to a validator instead of an action handler; duplicate schema files
5. **Silent failure patterns** — 15+ bare `except Exception` blocks; validation bypass in non-strict modes; no logging in fallback paths

---

# Architecture Review

## Current Architecture Assessment

The framework follows a layered pipeline architecture with clear data flow:

```
CAPTURE → SNAP → WORKFLOW-1E/1F → BUILD → DEPLOY_BUNDLE → VAL-2A → WORKFLOW-1G → RUN-1E → ACT-1A → Selenium
```

This is architecturally sound. The layers are:

| Layer | Responsibility | Modules |
|-------|---------------|---------|
| Capture | Record user interactions | CAPTURE-1A, SNAP-1A/1B |
| Normalize | Convert captures to schema steps | WORKFLOW-1E, WORKFLOW-1F |
| Build | Generate and package deploy bundles | BUILD-1A through BUILD-3H |
| Validate | Enforce grammar and bundle integrity | LINT-1A, VAL-2A |
| Load | Unpack bundles for execution | WORKFLOW-1G |
| Run | Orchestrate pipeline execution | RUN-1A, PIPE-1E, PIPE-1A |
| Act | Execute browser actions | ACT-1A, ACT-1B |
| Observe | Record outcomes and artifacts | STATE-1B, LOG-1A, HISTORY-1A |
| Report | Generate run reports | REPORT-1A through REPORT-12G |

**Assessment:** The data flow is correct and well-documented. The problem is **over-modularization within each layer** — BUILD has 17 modules, PIPE has 18, REPORT has 16, CLI has 8 — creating deep call chains where each module adds minimal value beyond forwarding to the next.

## Areas of Concern

### 1. Grammar Gate Tower (BUILD-2D/2E/2F/2G)

Four modules that form a delegation chain with negligible logic at each level:
- 2D validates step actions (real logic)
- 2E wraps 2D for a workflow dict (shallow copy + delegate)
- 2F wraps 2E for a file (load JSON + delegate)
- 2G wraps 2F for a directory (glob + delegate)

Each layer adds ~100 lines for what could be 20 lines of argument parsing in 2D itself.

### 2. CLI Entry Point Proliferation

Four near-identical `capture_to_deploy_bundle` CLIs (1a, 1b, 1c, 1d) with minor variations (BOM tolerance, auto-discovery). Each is a separate file with overlapping argparse setup.

### 3. Phase 12 Module Sprawl

Production readiness (milestones 12.1–12.6) generated 11 policy modules in REPORT + 2 in REGISTRY + 2 in DOC + 3 in RUN = 18 modules, many with copy-pasted helper functions (`_md()`, `write_text_file()`, `_sha256_hex()`).

### 4. Duplicate Module Names Within Same Package

- GUARD: `guard_1a_workflow_grammar_gate_guard.py` vs `guard_1a_workflow_grammar_guard.py`
- DOCTOR: `doctor_1a_workflow_grammar_gate.py` vs `doctor_1b_workflow_grammar_gate.py`
- REPORT-1A: `report_1a_generate.py` vs `report_1a_run_report.py` (both claim REPORT-1A)
- HISTORY-1C: `history_1c_error_normalization.py` vs `history_1c_run_history_loader.py`

## Suggested Improvements

1. **Collapse the grammar gate tower** — Merge 2D/2E/2F/2G into two modules: `build_2d_step_grammar_gate.py` (pure validation) and `build_2e_file_grammar_gate.py` (file I/O wrapper with directory support)
2. **Consolidate CLI entry points** — Single `cli_capture_to_deploy_bundle.py` with `--mode` flag
3. **Extract shared utilities** — `UTIL/util_common.py` for `_truthy()`, `_parse_bool()`, `_sha256_hex()`, `canonical_json_dumps()`, `write_text_file()`
4. **Define explicit interfaces** — Protocol classes for module contracts (e.g., `StepExecutor`, `WorkflowLoader`, `BundleValidator`)
5. **Centralize ALLOWED_ACTIONS** — Single constant imported from SCHEMA, not hardcoded in 3+ locations

---

# Findings

## F-01: Action Registry Has Missing Implementation Mappings

- **Severity:** Critical
- **Category:** Validation
- **Affected modules:** REGISTRY/action_registry.json, SCHEMA/steps_schema.json, REGISTRY/registry_1a_generate.py
- **Description:** 6 of 9 actions have empty `module` fields and `null` handler names in the registry. `click_selector` is mapped to `VAL/val_2a_deploy_bundle_validator.py` (a validator, not an action handler). The registry generator's handler discovery (`_find_handler_name_in_module()`) fails for all actions because it only checks 4 naming patterns and the actual implementations use different conventions.
- **Recommended fix:** Add explicit `implemented_by` annotations in ACT module docstrings; update registry generator to discover handlers from `_act_*` function prefix pattern; validate that every action in the registry has a non-empty module path pointing to an existing file
- **Estimated effort:** 4 hours

## F-02: Duplicate Schema Files

- **Severity:** High
- **Category:** Maintainability
- **Affected modules:** SCHEMA/steps_schema.json, SCHEMA/schema_1a_steps.json
- **Description:** Both files are identical (same content, same timestamp). If either is manually edited, the other diverges silently, creating schema drift. It is unclear which is authoritative.
- **Recommended fix:** Delete `schema_1a_steps.json` and have `steps_schema.json` as the single source of truth, or make `schema_1a_steps.json` a symlink/generated alias
- **Estimated effort:** 30 minutes

## F-03: Code Duplication in Phase 12 Production Modules

- **Severity:** High
- **Category:** Maintainability
- **Affected modules:** REPORT/report_12a through report_12g, REGISTRY/reg_12a, reg_12b
- **Description:** `_md()` is defined 6 times, `write_text_file()` 7 times, `_sha256_hex()` 3 times, `_truthy()` 3 times. The same canonical JSON serialization pattern is reimplemented in 20+ modules. Changes to any utility logic must be replicated across all copies.
- **Recommended fix:** Create `UTIL/util_common.py` with shared helpers; import from central location in all Phase 12 modules
- **Estimated effort:** 6 hours

## F-04: Four Duplicate CLI Capture-to-Deploy-Bundle Entry Points

- **Severity:** High
- **Category:** Architecture
- **Affected modules:** CLI/cli_1a_capture_to_deploy_bundle.py, cli_1b_capture_to_deploy_bundle.py, cli_1c_capture_to_deploy_bundle.py, cli_1d_capture_to_deploy_bundle_auto.py
- **Description:** Four separate CLI files with near-identical argparse setup, minor variations (BOM tolerance in 1c, auto-discovery in 1d). Each has its own error code conventions. Maintenance requires keeping 4 files in sync.
- **Recommended fix:** Merge into single `cli_capture_to_deploy_bundle.py` with `--mode` flag (standard, bom-tolerant, auto)
- **Estimated effort:** 3 hours

## F-05: Grammar Gate Module Tower (BUILD-2D/2E/2F/2G)

- **Severity:** High
- **Category:** Architecture
- **Affected modules:** BUILD/build_2d_step_grammar_gate.py, build_2e_workflow_grammar_gate.py, build_2f_workflow_file_grammar_gate.py, build_2g_workflow_tree_grammar_gate.py
- **Description:** Four modules forming a delegation chain where 2E wraps 2D, 2F wraps 2E, 2G wraps 2F. 2E adds only a shallow copy, 2F adds JSON file I/O, 2G adds directory glob. All logic is in 2D; the rest are thin forwarding layers.
- **Recommended fix:** Merge into `build_2d_step_grammar_gate.py` (pure validation) and `build_2e_file_grammar_gate.py` (file/directory I/O with built-in validation)
- **Estimated effort:** 4 hours

## F-06: Unstable Module Discovery via Dynamic Import Chains

- **Severity:** High
- **Category:** Architecture
- **Affected modules:** RUN/run_1a_workflow_runner.py, PIPE/pipe_1e_runner.py, CLI/cli_1a_run_pipeline.py, AGENT/agent_2a_autonomous_loop.py
- **Description:** 15+ locations use "best-effort" dynamic import with 4–12 fallback candidate module names. Example: `_find_pipe_entrypoint()` in RUN-1A tries 6+ import paths silently. `resolve_default_workflow_runner_callable()` in RUN-1E tries 5+ naming patterns. No logging of which path succeeded. Makes debugging nearly impossible when imports fail.
- **Recommended fix:** Define explicit Protocol interfaces for cross-module contracts; use a single import map (dict of module path → callable) with validation; log which import path succeeded at DEBUG level
- **Estimated effort:** 8 hours

## F-07: ALLOWED_ACTIONS Hardcoded in 3+ Locations

- **Severity:** Medium
- **Category:** Schema
- **Affected modules:** BUILD/build_2d_step_grammar_gate.py, BUILD/build_2a_nl_spec_generator.py, SNAP/snap_1a_workflow_capture.py, WORKFLOW/workflow_1a_loader.py
- **Description:** The set of allowed step actions is hardcoded independently in at least 4 modules. Adding a new action requires updating all 4 locations. No validation ensures they stay in sync.
- **Recommended fix:** Centralize in `SCHEMA/constants.py` or `REGISTRY/action_registry.json`; all modules import from single source
- **Estimated effort:** 2 hours

## F-08: Silent Validation Bypass in VAL-2A Non-Strict Mode

- **Severity:** Medium
- **Category:** Validation
- **Affected modules:** VAL/val_2a_deploy_bundle_validator.py, WORKFLOW/workflow_1f_selector_ref_first.py
- **Description:** VAL-2A in non-strict mode silently passes bundles with selector_ref mismatches (ref points to different selector than the one in the step). WORKFLOW-1F converts selectors to refs without validating the ref actually exists in the selector_pack. Invalid bundles can pass validation and fail at runtime.
- **Recommended fix:** Make strict mode the default; require explicit `--lenient` flag to bypass selector validation; add warning log for every bypassed check
- **Estimated effort:** 3 hours

## F-09: Bare Exception Handling (15+ Locations)

- **Severity:** Medium
- **Category:** Validation
- **Affected modules:** ACT/act_1b_logging_integration.py, RUN/run_1d_runner_with_history.py, PIPE/pipe_1c_steps_loader.py, STATE/state_1b_manifest_jsonl.py, CLI/cli_1a_run_pipeline.py
- **Description:** 15+ instances of `except Exception` with no logging or re-raising. Exceptions are silently swallowed, making debugging extremely difficult. In several cases, the exception type is converted to a string with no traceback preserved.
- **Recommended fix:** Replace bare catches with specific exception types; add `logger.debug()` for caught exceptions; preserve traceback info where possible
- **Estimated effort:** 4 hours

## F-10: Missing Type Hints on Critical Paths

- **Severity:** Medium
- **Category:** Typing
- **Affected modules:** WORKFLOW/workflow_2a_capture_actions_to_schema_steps.py, WORKFLOW/workflow_2b_capture_js_event_recorder.py, WORKFLOW/workflow_2c_capture_events_to_schema_steps_encoder.py, CLI/cli_1a_run_pipeline.py, CLI/cli_1c_args_overrides.py, DEPLOY/deploy_1a_service_runner.py
- **Description:** Capture and encoder modules (WORKFLOW-2a/2b/2c) have no return type hints on any public function. CLI-1A and CLI-1C have zero type hints. Several `cfg` and `driver` parameters use `Any` or are untyped throughout the codebase.
- **Recommended fix:** Add return type hints to all public functions in WORKFLOW-2a/2b/2c; add TypedDict for `cfg` parameter shape; type `driver` as `WebDriver` from selenium
- **Estimated effort:** 6 hours

## F-11: Duplicate Module Names Creating Import Ambiguity

- **Severity:** Medium
- **Category:** Architecture
- **Affected modules:** GUARD/guard_1a_workflow_grammar_gate_guard.py vs guard_1a_workflow_grammar_guard.py, DOCTOR/doctor_1a_workflow_grammar_gate.py vs doctor_1b_workflow_grammar_gate.py, HISTORY/history_1c_error_normalization.py vs history_1c_run_history_loader.py
- **Description:** Multiple pairs of modules with near-identical names and overlapping responsibilities. In GUARD, two modules both handle grammar validation with different approaches. In DOCTOR, 1a provides programmatic API while 1b provides PIPE-backed diagnosis — callers don't know which to import. HISTORY has two modules both numbered 1c.
- **Recommended fix:** Rename to clarify purpose: `guard_1a_gate_report_validator.py` vs `guard_1a_execution_guard.py`; `doctor_1a_programmatic_gate.py` vs `doctor_1b_pipe_diagnosis.py`; renumber `history_1c_run_history_loader.py` → `history_1d_run_history_loader.py`
- **Estimated effort:** 3 hours

## F-12: LINT-1A Missing Nested Field Validation for Repeat Blocks

- **Severity:** Medium
- **Category:** Validation
- **Affected modules:** LINT/lint_1a_steps_validator.py, WORKFLOW/workflow_1e_steps_normalizer.py
- **Description:** LINT-1A recurses into `repeat.steps` for structure validation but does not validate field types within nested steps. A `repeat` block containing steps with wrong field types (e.g., `times` as string instead of int) passes linting. WORKFLOW-1E normalizes repeat `times` from string to int but does not validate the value is a positive integer, allowing `repeat: {times: 0}`.
- **Recommended fix:** Add recursive type validation in LINT-1A for nested steps; add positive integer check in WORKFLOW-1E for repeat counts
- **Estimated effort:** 3 hours

## F-13: Schema Pollution Risk in SCHEMA-1A Generator

- **Severity:** Medium
- **Category:** Schema
- **Affected modules:** SCHEMA/schema_1a_generate.py
- **Description:** The AST visitor `_ActionStringVisitor` extracts action names from any dict literal, variable assignment, or comparison in Python source files. This means test stubs, configuration dicts, and comments containing action-like strings can pollute the generated schema with spurious actions. The canonical gate (`CANONICAL_STEP_GRAMMAR_ACTIONS`) blocks unknown actions but is a hardcoded list, preventing discovery of legitimately new actions without source changes.
- **Recommended fix:** Restrict AST scanning to `_act_*` function definitions only; make canonical action list configurable or read from registry; add validation that generated actions match handlers
- **Estimated effort:** 4 hours

## F-14: ACT-1A Duplicate Action Implementations

- **Severity:** Low
- **Category:** Maintainability
- **Affected modules:** ACT/act_1a_action_engine.py
- **Description:** `_act_open()` and `_act_get()` are functionally identical (both call `driver.get(url)`). `_act_click()` and `_act_click_selector()` have overlapping click logic with different error handling. Both `open` and `get` appear in the dispatch dict.
- **Recommended fix:** Unify `_act_open` as alias for `_act_get` with deprecation notice; consolidate click logic into single implementation
- **Estimated effort:** 2 hours

## F-15: dev_smoke() Functions Embedded in Production Modules

- **Severity:** Low
- **Category:** Testing
- **Affected modules:** LOG/log_1b_logger_reset.py, DOCTOR/doctor_1a_check.py, ACT/act_1a_action_engine.py, DEPLOY/deploy_1a_service_runner.py, multiple others
- **Description:** 10+ production modules contain `dev_smoke()` functions with file I/O, temporary file creation, and test assertions. These functions are never called in production but add LOC and import test-only dependencies.
- **Recommended fix:** Move all `dev_smoke()` functions to `dev/` test files; import and call from there
- **Estimated effort:** 4 hours

## F-16: Hardcoded Policies with No External Configuration

- **Severity:** Low
- **Category:** Architecture
- **Affected modules:** REGISTRY/reg_12a_versioning_policy.py, reg_12b_promotion_gates.py, REPORT/report_12d_artifact_retention_policy.py, report_12e_alerting_signals.py
- **Description:** Phase 12 policies (SemVer rules, promotion gates, retention periods, alert thresholds) are defined as hardcoded Python dicts. No way to override per environment without code changes. Promotion paths are hardcoded as dev→stage→prod.
- **Recommended fix:** Externalize to YAML/JSON policy files; add `--policy-file` CLI flag; provide default policies as fallback
- **Estimated effort:** 8 hours

## F-17: Configuration Key Aliases Create Ambiguity

- **Severity:** Low
- **Category:** Maintainability
- **Affected modules:** PIPE/pipe_1b_worklist_config.py, CLI/cli_1b_config_loader.py, VAL/val_1a_ui_state.py
- **Description:** 50+ configuration key aliases exist without documented priority. Examples: `EXPLICIT_WAIT` / `EXPLICIT_WAIT_SEC` / `WAIT_EXPLICIT_SEC` (3 keys for one value), `WORKLIST` / `WORKLIST_PATH` / `STEPS_PATH` / `INPUT_XLSX` (4 keys for worklist). Code uses `_first_present()` patterns that silently fall through.
- **Recommended fix:** Document canonical key names with aliases; add deprecation warnings for non-canonical keys; consolidate to single key per concept
- **Estimated effort:** 6 hours

## F-18: eval() Usage in ACT-1A Safe Assert

- **Severity:** Low
- **Category:** Validation
- **Affected modules:** ACT/act_1a_action_engine.py
- **Description:** `_safe_assert_eval()` uses Python `eval()` for runtime expression evaluation. Although restricted to a limited namespace, this is a potential code injection vector if step definitions come from untrusted sources.
- **Recommended fix:** Replace with a safe expression evaluator (e.g., `ast.literal_eval` extension or simple comparison parser); restrict to known operators only
- **Estimated effort:** 4 hours

## F-19: Empty/Dead Module: LINT/lint_steps.py

- **Severity:** Low
- **Category:** Dead Code
- **Affected modules:** LINT/lint_steps.py
- **Description:** File exists with 1 line (docstring placeholder only). Referenced in AGENT_PACKET as a CLI entry point (`python LINT/lint_steps.py path/to/steps.json`) but contains no executable code.
- **Recommended fix:** Populate with actual lint utility (delegate to lint_1a_steps_validator) or delete and update references
- **Estimated effort:** 1 hour

## F-20: JavaScript Injection in Capture Modules Without Escaping

- **Severity:** Low
- **Category:** Validation
- **Affected modules:** WORKFLOW/workflow_2b_capture_js_event_recorder.py
- **Description:** The JS capture listener string is built via string formatting with `CAPTURE_QUEUE_GLOBAL_1A` variable interpolated without escaping. If this variable could be influenced by external input, it could enable JavaScript injection. CSS selector generation (`_cssPath()`) only handles ASCII character escaping.
- **Recommended fix:** Sanitize `CAPTURE_QUEUE_GLOBAL_1A` to alphanumeric only; extend CSS escaping for Unicode; validate JS template has no unescaped interpolations
- **Estimated effort:** 2 hours

## F-21: Duplicate Fingerprint Key Lists in BUILD-3B and BUILD-3F

- **Severity:** Low
- **Category:** Maintainability
- **Affected modules:** BUILD/build_3b_bundle_fingerprint.py, BUILD/build_3f_deploy_bundle_stamper.py
- **Description:** `DEFAULT_FINGERPRINT_DROP_TOP_LEVEL_KEYS` is defined identically in both modules. If one changes, the other must be manually updated or fingerprint computation breaks.
- **Recommended fix:** Define once in BUILD-3B; import in BUILD-3F
- **Estimated effort:** 30 minutes

## F-22: Non-ASCII Debug String in agent_2b_scheduler.py

- **Severity:** Low
- **Category:** Maintainability
- **Affected modules:** AGENT/agent_2b_scheduler.py
- **Description:** Line 82 contains a non-ASCII string ("شروع") in a print statement. This may cause encoding issues in restricted environments.
- **Recommended fix:** Replace with ASCII equivalent
- **Estimated effort:** 5 minutes

## F-23: No Cookie File Permission Checks in AUTH-1B

- **Severity:** Low
- **Category:** Validation
- **Affected modules:** AUTH/auth_1b_session_restore.py
- **Description:** Session cookies are saved to disk without restricting file permissions. On multi-user systems, cookies.json may be world-readable, exposing session tokens.
- **Recommended fix:** Set file permissions to 0600 on cookie file write; warn if existing file has broad permissions
- **Estimated effort:** 1 hour

## F-24: Potential Infinite Recursion in VAR-1A Variable Rendering

- **Severity:** Low
- **Category:** Validation
- **Affected modules:** VAR/var_1a_runtime_store.py
- **Description:** `render_vars()` performs recursive `${VAR}` substitution but has no cycle detection. A circular reference like `${A}` → `${B}` → `${A}` would cause infinite recursion.
- **Recommended fix:** Add max_depth parameter (default 10); detect and raise on circular references
- **Estimated effort:** 1 hour

## F-25: Race Condition in VAL-1B Download Validation

- **Severity:** Low
- **Category:** Performance
- **Affected modules:** VAL/val_1b_download_validation.py
- **Description:** File matching sorts by `(mtime, path)` descending. Under concurrent writes, mtime may not reflect actual completion order, causing the wrong file to be selected as the download result.
- **Recommended fix:** Add file stability check (size unchanged over polling interval) before matching; prefer filename-based matching over mtime
- **Estimated effort:** 2 hours

---

# Missing Test Coverage

Top 25 modules ranked by priority for receiving formal unit tests (beyond dev_smoke scripts):

| Rank | Module | Reason | Current Coverage |
|------|--------|--------|-----------------|
| 1 | ACT/act_1a_action_engine.py | Core execution engine; 895 LOC; only dev_smoke | dev_smoke only |
| 2 | PIPE/pipe_1e_runner.py | Canonical pipeline runner | dev_smoke only |
| 3 | PIPE/pipe_1a_run_orchestrator.py | Worklist orchestrator | dev_smoke only |
| 4 | RUN/run_1a_workflow_runner.py | Top-level entry point | dev_smoke only |
| 5 | LINT/lint_1a_steps_validator.py | Schema enforcement | dev_smoke only |
| 6 | VAL/val_2a_deploy_bundle_validator.py | Pre-deploy gate | dev_smoke only |
| 7 | WORKFLOWS/workflow_1a_loader.py | Workflow loader/normalizer | dev_smoke only |
| 8 | WORKFLOW/workflow_1f_selector_ref_first.py | Policy enforcer | dev_smoke only |
| 9 | SCHEMA/schema_1a_generate.py | Schema generation (AST) | dev_smoke only |
| 10 | REGISTRY/registry_1a_generate.py | Registry generation | dev_smoke only |
| 11 | BUILD/build_3c_deploy_bundle_builder.py | Bundle builder | dev_smoke only |
| 12 | BUILD/build_1a_workflow_generator.py | Workflow generator | dev_smoke only |
| 13 | PIPE/pipe_1c_steps_loader.py | Steps loader + template sub | dev_smoke only |
| 14 | WORKFLOWS/workflow_1g_deploy_bundle_loader.py | Bundle loader | dev_smoke only |
| 15 | BUILD/build_3a_deploy_bundle_format.py | Bundle format converter | dev_smoke only |
| 16 | REPORT/report_1a_step_logs_from_jsonl.py | Log reconstruction | dev_smoke only |
| 17 | GUARD/guard_12a_prod_defaults.py | Production guardrails | dev_smoke only |
| 18 | HISTORY/history_12a_audit_logging_replay_spec.py | Audit logging spec | dev_smoke only |
| 19 | AGENT/agent_2a_autonomous_loop.py | Autonomous execution | dev_smoke only |
| 20 | AUTH/auth_1b_session_restore.py | Session management | dev_smoke only |
| 21 | RUN/run_1e_deploy_bundle_runner_adapter.py | Bundle execution | dev_smoke only |
| 22 | WORKFLOW/workflow_1e_steps_normalizer.py | Step normalization | dev_smoke only |
| 23 | REPORT/report_12g_evidence_bundle_assembler.py | Evidence assembly | dev_smoke only |
| 24 | STATE/state_1b_manifest_jsonl.py | Manifest persistence | dev_smoke only |
| 25 | BUILD/build_2d_step_grammar_gate.py | Grammar enforcement | dev_smoke only |

**Note:** All modules have dev_smoke() scripts that verify basic functionality, but these are not formal unit tests — they lack assertions, edge case coverage, negative testing, and regression protection. The priority ordering above weights: (1) modules on the critical execution path, (2) modules with validation responsibility, (3) modules with complex logic.

---

# Technical Debt

Ranked by ROI (impact of fixing / effort to fix):

| Rank | Debt Item | Impact | Effort | ROI |
|------|----------|--------|--------|-----|
| 1 | Centralize shared utilities (_truthy, _parse_bool, _sha256_hex, canonical_json, write_text_file) | Eliminates 25+ duplication sites | 6h | **Very High** |
| 2 | Fix action registry implementation mappings (6/9 missing) | Enables runtime action tracing, documentation, and AI capability handshake | 4h | **Very High** |
| 3 | Remove duplicate schema file (schema_1a_steps.json) | Eliminates schema drift risk | 0.5h | **Very High** |
| 4 | Consolidate 4 CLI capture_to_deploy_bundle entry points | Reduces maintenance burden by 4x | 3h | **High** |
| 5 | Collapse grammar gate tower (2D/2E/2F/2G → 2 modules) | Removes 2 unnecessary abstraction layers | 4h | **High** |
| 6 | Add explicit Protocol interfaces for cross-module contracts | Eliminates 15+ fragile dynamic import chains | 8h | **High** |
| 7 | Centralize ALLOWED_ACTIONS constant | Prevents action list drift across 4 modules | 2h | **High** |
| 8 | Make strict validation default in VAL-2A | Prevents invalid bundles from passing | 3h | **High** |
| 9 | Add type hints to WORKFLOW-2a/2b/2c and CLI modules | Improves IDE support and type checking | 6h | **Medium** |
| 10 | Resolve duplicate module names (GUARD, DOCTOR, HISTORY) | Removes import ambiguity | 3h | **Medium** |
| 11 | Replace bare except Exception with specific types | Improves debuggability dramatically | 4h | **Medium** |
| 12 | Add nested field validation in LINT-1A for repeat blocks | Prevents invalid nested steps | 3h | **Medium** |
| 13 | Externalize hardcoded Phase 12 policies to config files | Enables per-environment customization | 8h | **Medium** |
| 14 | Remove dev_smoke() from production modules | Clean separation of test/production code | 4h | **Medium** |
| 15 | Consolidate RUN-1B/1C/1D into RUN-1A with feature flags | Redces 3 wrapper modules | 4h | **Medium** |
| 16 | Add cookie file permission checks in AUTH-1B | Security improvement | 1h | **Medium** |
| 17 | Add cycle detection in VAR-1A variable rendering | Prevents infinite recursion | 1h | **Medium** |
| 17 | Populate or delete LINT/lint_steps.py | Removes dead code reference | 1h | **Medium** |
| 19 | Replace eval() in ACT-1A with safe expression parser | Removes code injection risk | 4h | **Low** |
| 20 | Unify _act_open/_act_get in ACT-1A | Removes dead code dispatch | 2h | **Low** |

---

# Recommended Roadmap

## Phase 1 — Highest ROI (Stabilization)

**Goal:** Eliminate the highest-impact sources of bugs, drift, and confusion.

| Action | Effort | Deliverable |
|--------|--------|-------------|
| 1.1 Centralize shared utilities | 6h | `UTIL/util_common.py` with `_truthy()`, `_parse_bool()`, `_sha256_hex()`, `canonical_json_dumps()`, `write_text_file()`, `_md()` |
| 1.2 Fix action registry mappings | 4h | All 9 actions mapped to correct ACT implementation modules with handler function names |
| 1.3 Remove duplicate schema file | 0.5h | Delete `SCHEMA/schema_1a_steps.json`; update any references |
| 1.4 Centralize ALLOWED_ACTIONS | 2h | Single constant in `SCHEMA/constants.py`; all modules import from it |
| 1.5 Make strict validation default | 3h | VAL-2A defaults to strict; `--lenient` flag for backward compat |
| 1.6 Populate or delete lint_steps.py | 1h | Either delegate to lint_1a or remove and update AGENT_PACKET |

**Phase 1 total effort:** ~16.5 hours

## Phase 2 — Important (Consolidation)

**Goal:** Reduce module count and maintenance surface area.

| Action | Effort | Deliverable |
|--------|--------|-------------|
| 2.1 Consolidate CLI capture entry points | 3h | Single CLI with `--mode` flag |
| 2.2 Collapse grammar gate tower | 4h | `build_2d_step_grammar_gate.py` + `build_2e_file_grammar_gate.py` |
| 2.3 Resolve duplicate module names | 3h | Renamed GUARD, DOCTOR, HISTORY modules |
| 2.4 Add type hints to WORKFLOW-2a/2b/2c | 4h | Full return type annotations on all public functions |
| 2.5 Add nested validation to LINT-1A | 3h | Recursive type checking for repeat.steps fields |
| 2.6 Replace bare except blocks | 4h | Specific exception types + debug logging in 15+ locations |
| 2.7 Consolidate RUN-1B/1C/1D wrappers | 4h | Feature flags on RUN-1A instead of 3 separate wrapper files |
| 2.8 Add Protocol interfaces for cross-module contracts | 8h | `StepExecutor`, `WorkflowLoader`, `BundleValidator`, `PipelineRunner` protocols |

**Phase 2 total effort:** ~33 hours

## Phase 3 — Nice to Have (Hardening)

**Goal:** Production-grade polish, externalization, and security.

| Action | Effort | Deliverable |
|--------|--------|-------------|
| 3.1 Externalize Phase 12 policies to YAML | 8h | Policy files for versioning, promotion, retention, alerting |
| 3.2 Move dev_smoke() to test files | 4h | Clean production module separation |
| 3.3 Add formal unit test suite | 16h | pytest suite for top 25 modules |
| 3.4 Replace eval() with safe parser | 4h | Restricted expression evaluator in ACT-1A |
| 3.5 Add cookie file permissions | 1h | 0600 mode on AUTH-1B cookie files |
| 3.6 Add VAR-1A cycle detection | 1h | max_depth + circular reference detection |
| 3.7 Unify ACT-1A duplicate actions | 2h | Deprecate `_act_open` in favor of `_act_get` |
| 3.8 Sanitize JS capture templates | 2h | Alphanumeric-only validation for global var name |
| 3.9 Consolidate config key aliases | 6h | Canonical key names + deprecation warnings |
| 3.10 Extract shared redaction utility | 2h | Single redact() for HISTORY, STATE, ACT modules |

**Phase 3 total effort:** ~46 hours

---

*End of audit report.*
