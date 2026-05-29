# Python Library Index

AUTO-GENERATED. DO NOT EDIT MANUALLY.

## Repository Summary

| Category | Count |
|----------|-------|
| ACT | 5 |
| AGENT | 3 |
| AUTH | 2 |
| BUILD | 9 |
| CAPTURE | 1 |
| CLI | 8 |
| DEPLOY | 1 |
| DIFF | 3 |
| DOC | 8 |
| DOCTOR | 5 |
| ENTRY | 3 |
| GUARD | 4 |
| HEAL | 1 |
| HISTORY | 7 |
| INPUT | 3 |
| LEARN | 2 |
| LINT | 1 |
| LOG | 2 |
| LOOP | 1 |
| NAV | 2 |
| OBS | 1 |
| OUT | 2 |
| PACK | 1 |
| PIPE | 18 |
| PLAN | 1 |
| REASON | 1 |
| REG | 2 |
| REGISTRY | 1 |
| REPLAY | 2 |
| REPO | 1 |
| REPORT | 15 |
| RUN | 8 |
| RUNBOOK | 1 |
| SCHEMA | 1 |
| SELECTOR | 1 |
| SHA | 1 |
| SNAP | 4 |
| STATE | 3 |
| UNKNOWN | 29 |
| VAL | 3 |
| VAR | 1 |
| WORKFLOW | 4 |
| TOTAL | 172 |

## Capability Summary

| Module | Description |
|--------|-------------|
| ACT-1A | ACT-1A — Canonical Action Execution Layer |
| ACT-1A | Dev smoke test for ACT-1A action engine. |
| ACT-1B | ACT-1B — Structured logging integration wrapper for ACT-1A |
| ACT-1B | Dev smoke test for ACT-1B logging integration. |
| ACT-1C | ACT-1C — Conditional Step Guards. |
| AGENT-1A | AGENT-1A — Agent Context Pack Exporter (single pasteable bundle) |
| AGENT-2A | AGENT-2A — Autonomous Execution Loop (orchestration only) |
| AGENT-2B | AGENT-2B — Continuous / Scheduled Execution (timing + orchestration only) |
| AUTH-1A | AUTH-1A — Standard username/password form login with guarded "already logged in" check. |
| AUTH-1B | AUTH-1B — Session Restore (cookies/local storage) + guarded fallback to AUTH-1A. |
| BUILD-1A | BUILD-1A: workflow grammar gate entrypoints spec. |
| BUILD-2A | BUILD-2A — Natural Language → Build Spec Generator |
| BUILD-2A | BUILD-2A — Repeat Support (Milestone 12.5.7) |
| BUILD-2B | BUILD-2B — Workflow Plan Optimizer (pure transformation) |
| BUILD-2C | BUILD-2C — Full Automation Bundle Generator (orchestration only) |
| BUILD-2D | BUILD-2D: Step grammar enforcement / gating. |
| BUILD-2E | BUILD-2E: Workflow-level wrapper around BUILD-2D step grammar enforcement. |
| BUILD-2F | BUILD-2F: File-level workflow grammar gating. |
| BUILD-2G | BUILD-2G: Directory/tree-level workflow grammar gating. |
| CAPTURE-1A | CAPTURE-1A — Semi-Automatic Selector Capture (headed capture session) |
| CLI-1A | CLI-1A — Command Line Pipeline Runner. |
| CLI-1A | CLI-1A: Workflow grammar gate CLI. |
| CLI-1B | CLI-1B — Configuration Loader. |
| CLI-1C | CLI-1C — CLI Flags + Overrides |
| CLI-1F | CLI-1F — Generate reports for a run output directory (10.4.3) |
| CLI-1G | CLI-1G: Workflow grammar gate CLI. |
| CLI-1H | CLI-1H: Workflow grammar gate pipeline CLI. |
| CLI-2B | CLI-2B — Unified Automation Command Interface (orchestration only) |
| DEPLOY-1A | DEPLOY-1A — Runtime Service + Packaging (service runner) |
| DIFF-12A | DIFF-12A: Reviewable Diffs (Milestone 12.2.2) |
| DIFF-1A | DIFF-1A — Workflow & Selector Change Diff + Version Stamp |
| DIFF-1A | DIFF-1A: Workflow grammar gate report diff. |
| DOC-12A | DOC-12A: SLOs and Success Criteria (Milestone 12.1.1) |
| DOC-12B | DOC-12B: Operator Runbooks (Milestone 12.1.2) |
| DOC-12C | DOC-12C: Support and Escalation Paths (Milestone 12.1.3) |
| DOC-12D | DOC-12D: Rollback and Recovery Procedures (Milestone 12.4.3) |
| DOC-1A | DOC-1A — Library Index Generator |
| DOC-1A | DOC-1A: Workflow grammar gate documentation builder. |
| DOC-1G | DOC-1G — Doc Index Entry Contract (Validator) |
| DOC-1H | DOC-1H — Doc Index Collect + Validate Wrapper |
| DOCTOR-12A | DOCTOR-12A: Pre-run DOCTOR Checks Policy (Milestone 12.4.1) |
| DOCTOR-12D | DOCTOR-12D: Release Readiness Gate (Milestone 12.5.6) |
| DOCTOR-1A | DOCTOR-1A — Environment Self-Check (“preflight”) |
| DOCTOR-1A | DOCTOR-1A: Workflow grammar gate (programmatic check/fix). |
| DOCTOR-1B | DOCTOR-1B: Workflow grammar gate diagnosis (PIPE-backed). |
| ENTRY-1A | Smoke Test: ENTRY-1A webdriver bootstrap (Edge + Chrome) |
| ENTRY-1A | ENTRY-1A — Standard headless-first webdriver bootstrap (Chrome/Edge configurable) |
| ENTRY-1A | ENTRY-1A: Workflow grammar gate entry point. |
| GUARD-12A | GUARD-12A: Production-default GUARD Policy (Milestone 12.4.2) |
| GUARD-1A | GUARD-1A — Runtime Guardrails (stability layer) |
| GUARD-1A | GUARD-1A: Workflow grammar gate guard. |
| GUARD-1A | GUARD-1A: Workflow grammar guard. |
| HEAL-1A | HEAL-1A — Auto-fix Suggestion Applier (workflow patch generator) |
| HISTORY-12A | HISTORY-12A: Audit-Friendly Logging + Replay Spec (Milestone 12.5.3) |
| HISTORY-1A | HISTORY-1A — Run manifest (10.2.1) |
| HISTORY-1A | HISTORY-1A — Run History Store (append-only JSONL) |
| HISTORY-1A | HISTORY-1A: Workflow grammar gate history. |
| HISTORY-1B | HISTORY-1B — Step outcomes recorder (10.2.2) |
| HISTORY-1C | HISTORY-1C — Error normalization (10.2.3) |
| HISTORY-1C | HISTORY-1C — Run history loader (9.4.3) |
| INPUT-1B | Smoke test for top-level INPUT-1B shim: input_1b_excel_provider.py |
| INPUT-1B | Smoke test for: |
| INPUT-1B | INPUT-1B — Excel provider (sheet + column -> list of IDs) + optional manifest writer |
| LEARN-1A | LEARN-1A — Failure Pattern Analytics (pure, deterministic) |
| LEARN-1B | LEARN-1B — Selector Intelligence & Stability Scoring (pure analysis) |
| LINT-1A | LINT-1A — Step Validation Engine |
| LOG-1A | LOG-1A — Standard structured logging + run_id + per-item context (stdlib only) |
| LOG-1B | LOG-1B — Error Taxonomy + Exception Normalization. |
| LOOP-1B | LOOP-1B — Per-item loop (generic iterator over worklist) |
| NAV-1A | Dev smoke test for NAV-1A Selenium helpers. |
| NAV-1A | NAV-1A — Selenium navigation and interaction helpers (pure helpers, no logging) |
| OBS-1A | OBS-1A — Run Observability Timeline |
| OUT-1A | OUT-1A — Download wait/poll + directory management. |
| OUT-1B | OUT-1B — Artifact Normalization (rename/move/archive, collision-safe). |
| PACK-1A | PACK-1A — Golden-Path CLI (one-command framework usage) |
| PIPE-1A | Dev smoke test for PIPE-1A run orchestrator. |
| PIPE-1A | PIPE-1A — End-to-end per-run orchestrator (glue module) |
| PIPE-1A | PIPE-1A: Workflow grammar gate pipeline runner. |
| PIPE-1B | Dev smoke test — PIPE-1B (worklist configuration adapter) |
| PIPE-1B | PIPE-1B — Worklist configuration adapter |
| PIPE-1C | Dev smoke test — PIPE-1C (steps loader + template substitution) |
| PIPE-1C | PIPE-1C — Steps loader + template substitution (stdlib-only) |
| PIPE-1D | Dev smoke test — PIPE-1D (step execution adapter) |
| PIPE-1D | PIPE-1D — Step Execution Adapter |
| PIPE-1E | PIPE-1E — Single runnable pipeline entrypoint. |
| PIPE-1F | PIPE-1F: Environment overrides applied to cfg. |
| PIPE-1G | PIPE-1G — Environment Force Overrides |
| PIPE-1H | PIPE-1H — JSONL Log Path Policy |
| PIPE-2A | PIPE-2A — Variable-aware Step Execution (VAR-1A integration). |
| PIPE-2B | PIPE-2B — Step Blocks & Branching (if/else + try blocks). |
| PIPE-2C | PIPE-2C — Error Plumbing Integration (LOG-1B + LOG-1A + STATE). |
| PIPE-2D | PIPE-2D — Artifact + Manifest Integration. |
| PIPE-2E | PIPE-2E — Run Summary + Metrics. |
| PLAN-1A | PLAN-1A — Workflow Step Planner / Skeleton Generator |
| REASON-1A | REASON-1A — Failure Diagnosis Engine (agent-friendly) |
| REG-12A | REG-12A: Versioning Policy (Milestone 12.2.1) |
| REG-12B | REG-12B: Promotion Gates Policy (Milestone 12.2.3) |
| REGISTRY-1A | REGISTRY-1A — Action/Step Registry Export (AI Capability Handshake) |
| REPLAY-12A | REPLAY-12A: Replay Index Verifier (Milestone 12.5.4) |
| REPLAY-1A | REPLAY-1A — Deterministic Run Replayer |
| REPO-INTEL-1A | MODULE: REPO-INTEL-1A |
| REPORT-12A | REPORT-12A: Release Manifest (Milestone 12.3.1) |
| REPORT-12B | REPORT-12B: Bundle Fingerprint (Milestone 12.3.2) |
| REPORT-12C | REPORT-12C: Promotion Record (Milestone 12.3.3) |
| REPORT-12D | REPORT-12D: Artifact Retention Policy (Milestone 12.5.1) |
| REPORT-12E | REPORT-12E: Alerting Signals From Run Outcomes (Milestone 12.5.2) |
| REPORT-12F | REPORT-12F: Incident Packet Manifest (Milestone 12.5.5) |
| REPORT-1A | REPORT-1A — Run Report Generator (HTML + JSON + MD) |
| REPORT-1A | REPORT-1A — Run report aggregation (10.3.1) |
| REPORT-1A | REPORT-1A — Build step_logs from LOG JSONL events. |
| REPORT-1A | REPORT-1A: Workflow grammar gate reporting. |
| REPORT-1B | REPORT-1B — Run report markdown renderer (10.3.2) |
| REPORT-1B | REPORT-1B: Deterministic text rendering for workflow grammar gate reports. |
| REPORT-1C | REPORT-1C — JUnit XML renderer (10.3.3) |
| REPORT-1C | REPORT-1C: Workflow grammar gate report summary. |
| REPORT-1D | REPORT-1D — Generate standard report artifacts (10.4.1) |
| RUN-1A | RUN-1A: Pre-run workflow grammar gate. |
| RUN-1A | RUN-1A: Workflow grammar gate run orchestration. |
| RUN-1A | RUN-1A — Unified Workflow Runner |
| RUN-1B | RUN-1B — Workflow Runner With Snapshot Capture |
| RUN-1C | RUN-1C — Wrapper to enable GUARD-1A without refactoring RUN-1A. |
| RUN-1D | RUN-1D — Wrapper to append HISTORY-1A records after running RUN-1A / REPORT-1A. |
| RUN-1E | RUN-1E — Deploy Bundle Runner Adapter |
| RUN-1E | RUN-1E — Post-run reporting hook (10.4.2) |
| RUNBOOK-1A | RUNBOOK-1A — Operational Playbook Generator |
| SCHEMA-1A | SCHEMA-1A — Step/Action Schema Export (AI-friendly) |
| SELECTOR-1A | SELECTOR-1A — Selector Registry / Resolver |
| SHA-256 | Deterministic canonicalization / serialization utilities. |
| SNAP-1A | SNAP-1A — Evidence Capture on Failure (artifacts bundle) |
| SNAP-1A | SNAP-1A — Failure capture (10.1.1) |
| SNAP-1B | SNAP-1B — Screenshot capture (10.1.2) |
| SNAP-1C | SNAP-1C — Persist snapshot artifacts deterministically (10.1.3) |
| STATE-1B | STATE-1B — JSONL manifest state (queued/success/fail + metadata) — stdlib-only |
| STATE-1C | STATE-1C — Retry / Resume helpers (additive to STATE-1B). |
| STATE-1D | STATE-1D — Manifest Row Helpers (standardize queued/success/fail shapes). |
| UNKNOWN | app.py — Simplified Selenium RPA runner |
| UNKNOWN | How to run: |
| UNKNOWN | Dev smoke test for ACT download_wait integration. |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | How to run: |
| UNKNOWN | Dev bootstrap: ensure repo root is on sys.path. |
| UNKNOWN | report_12g_evidence_bundle_assembler.py |
| UNKNOWN | run_12a_prod_smoke_pipeline.py |
| UNKNOWN | run_12b_rollback_rerun_determinism.py |
| UNKNOWN | run_12c_operational_gates_enforcement.py |
| VAL-1A | VAL-1A — UI state validation via selector presence + text checks. |
| VAL-1B | VAL-1B — Download validation (file exists, size > 0, optional name patterns). |
| VAL-2A | VAL-2A — Deploy Bundle Validator |
| VAR-1A | VAR-1A — Runtime Variable Store. |
| WORKFLOW-1A | WORKFLOW-1A — Workflow file loader + validator + normalizer |
| WORKFLOW-1E | WORKFLOW-1E — Workflow Steps Normalizer |
| WORKFLOW-1F | WORKFLOW-1F — Selector Reference First Enforcement |
| WORKFLOW-1G | WORKFLOW-1G — Deploy Bundle Loader |

## ACT\act_1a_action_engine.py

**Module ID:** ACT-1A

```
ACT-1A — Canonical Action Execution Layer

Purpose
-------
Execute normalized workflow steps against a live browser session.

This module serves as the primary runtime action engine and provides
the standard execution surface used by workflow runners, deploy bundles,
and future orchestration layers.

Responsibilities
----------------
- Execute workflow actions sequentially
- Resolve workflow variables (${TOKEN})
- Resolve selector references (selector_ref)
- Interact with Selenium WebDriver
- Record step outcomes and execution timing
- Enforce fail-fast execution behavior
- Execute JavaScript actions
- Support download monitoring and validation
- Capture runtime failures with structured diagnostics

Supported Action Categories
---------------------------
Navigation
- open
- get

Synchronization
- wait
- wait_for_element

Element Interaction
- click
- type
- select
- hover
- scroll
- element lookup

JavaScript
- inline script execution
- external script execution

Downloads
- download_wait
- file existence validation
- file stability validation

Assertions
- runtime expression evaluation
- workflow validation checks

Architecture Position
---------------------
CAPTURE
    ↓
SNAP
    ↓
WORKFLOW-1E
    Normalize
    ↓
WORKFLOW-1F
    Selector Ref First
    ↓
BUILD
    ↓
DEPLOY_BUNDLE
    ↓
VAL-2A
    Validate
    ↓
WORKFLOW-1G
    Load Bundle
    ↓
RUN-1E
    Runner Adapter
    ↓
ACT-1A
    Action Engine
    ↓
SELENIUM

Public API
----------
StepOutcome
ActionEngineError
run_actions(...)
outcomes_as_dicts(...)
outcomes_all_ok(...)
dev_smoke(...)

Dependencies
------------
selenium
NAV-1A

Status
------
Audited

Notes
-----
This is the canonical workflow execution engine.

All workflow execution paths ultimately converge here before
interacting with Selenium WebDriver.

The module provides the foundation for future healing,
telemetry, reporting, replay, and multi-agent execution.
```

## ACT\act_1b_logging_integration.py

**Module ID:** ACT-1B

```
ACT-1B — Structured logging integration wrapper for ACT-1A  
  
Purpose  
-------  
Orchestrate execution of ACT-1A steps while automatically emitting structured logs  
(using LOG-1A) for:  
- step_start  
- step_success  
- step_error  
  
This module does NOT change ACT-1A behavior; it wraps ACT-1A execution to add  
consistent logging and cfg-driven stop/continue behavior.  
  
Key behaviors  
-------------  
- Uses cfg["STOP_ON_ERROR"] (default True) to determine fail-fast behavior.  
- Preserves ACT-1A per-step `continue_on_error` behavior.  
- Binds per-item context (run_id/current_id/item_index/total_items) if present in cfg.  
- Uses LOG-1A `log_exception` for exceptions, capturing step_id + milestone + taxonomy tag.
```

## ACT\act_1c_conditional_guards.py

**Module ID:** ACT-1C

```
ACT-1C — Conditional Step Guards.  
  
Goal  
----  
Allow step execution to branch safely based on UI state without failing the run.  
  
All helpers:  
- Fail safe: return False instead of throwing  
- Never break pipeline (no exceptions propagate)  
  
Primary helpers (required)  
--------------------------  
element_exists(driver, by, selector) -> bool  
text_equals(driver, by, selector, expected) -> bool  
text_contains(driver, by, selector, substring) -> bool  
attribute_equals(driver, by, selector, attr, expected) -> bool  
  
Optional adapter (additive, for ACT engine integration)  
-------------------------------------------------------  
should_run_step(driver, step: Mapping[str, Any]) -> bool  
  
This evaluates guard fields like:  
  - if_exists: ".submit"  (defaults to by="css")  
  - if_text_contains: {"selector": ".dialog-title", "text": "Confirm", "by": "css"}
```

## AGENT\agent_1a_context_pack.py

**Module ID:** AGENT-1A

```
AGENT-1A — Agent Context Pack Exporter (single pasteable bundle)  
  
Reads existing generated artifacts (DO NOT re-derive) and produces:  
- DOC/AGENT_PACKET.md   (human + LLM paste bundle)  
- DOC/agent_packet.json (machine bundle; includes paths, exports, actions)  
  
Inputs (required):  
- DOC/library_index.json  
- SCHEMA/steps_schema.json (or other SCHEMA-1A schema output filenames)  
  
Inputs (optional):  
- SCHEMA/steps_examples.json  
- REGISTRY/action_registry.json  
- data/selectors.json  
  
Rules:  
- No side-effect imports of project modules.  
- Prefer pure helpers; no printing/logging here.  
- Deterministic output ordering.
```

## AGENT\agent_2a_autonomous_loop.py

**Module ID:** AGENT-2A

```
AGENT-2A — Autonomous Execution Loop (orchestration only)  
  
Coordinates: RUN → (on failure) SNAP → REASON → HEAL → retry → (on success) REPORT  
Then runs LEARN analysis over HISTORY to produce recommendations.  
  
Constraints:  
- No direct Selenium logic here (delegates to existing modules).  
- Deterministic behavior (no randomness).  
- Additive module; does not modify existing modules.
```

## AGENT\agent_2b_scheduler.py

**Module ID:** AGENT-2B

```
AGENT-2B — Continuous / Scheduled Execution (timing + orchestration only)  
  
Reuses AGENT-2A as the execution engine; does not implement execution logic.  
No Selenium.  
  
Public API:  
- run_continuous(...)  
- run_once_with_delay(...)
```

## AUTH\auth_1a_form_login_guarded.py

**Module ID:** AUTH-1A

```
AUTH-1A — Standard username/password form login with guarded "already logged in" check.  
  
Public API  
----------  
ensure_logged_in(driver, cfg: dict) -> dict  
login(driver, cfg: dict) -> dict  
    Returns:  
        {  
          "ok": bool,  
          "already_logged_in": bool,  
          "result": dict | None,  
          "error": str | None  
        }  
  
Config (env-friendly)  
---------------------  
LOGIN_URL  
USERNAME / PASSWORD  
USERNAME_SELECTOR / PASSWORD_SELECTOR / SUBMIT_SELECTOR  
USERNAME_BY / PASSWORD_BY / SUBMIT_BY  (css|xpath|id|name; default css)  
  
LOGGED_IN_SELECTOR (preferred guard + post-login success indicator)  
LOGGED_IN_BY (default css)  
POST_LOGIN_SELECTOR / POST_LOGIN_BY (fallback success indicator)  
  
EXPLICIT_WAIT / EXPLICIT_WAIT_SEC / WAIT_EXPLICIT_SEC (default 10)  
STOP_ON_ERROR (unused here; consumed by higher layers)
```

## AUTH\auth_1b_session_restore.py

**Module ID:** AUTH-1B

```
AUTH-1B — Session Restore (cookies/local storage) + guarded fallback to AUTH-1A.  
  
Goal  
----  
Speed up runs and reduce auth flakiness by restoring a prior session when possible.  
  
Notes  
-----  
- Filesystem-only for session artifacts.  
- Headless-first; no OS dialogs; no coordinate clicking.  
- Never logs secrets or cookie values.  
- Does NOT duplicate AUTH-1A logic; attempts to call AUTH-1A as fallback.  
  
Config keys  
-----------  
SESSION_RESTORE: bool  
SESSION_COOKIE_PATH: optional explicit cookies.json  
LOGIN_URL / DOMAIN_URL (DOMAIN_URL required for cookie injection)  
POST_LOGIN_SELECTOR: CSS/XPath selector indicating logged-in state  
POST_LOGIN_BY: "css"|"xpath"|... (default "css")  
SESSION_SAVE_ON_SUCCESS: bool (default True)  
SESSION_DIR: optional base directory for sessions (default "./sessions")  
PORTAL: optional portal name (otherwise derived from DOMAIN_URL hostname)  
USER / USERNAME / EMAIL: optional user id for per-user folder
```

## base_app.py

**Module ID:** UNKNOWN

```
app.py — Simplified Selenium RPA runner
---------------------------------------
Runs a JSON-driven list of RPA steps such as:
    open, wait_for_selector, type_selector, click_selector,
    exec_js, exec_js_file, set_var_from_js,
    repeat (with RPA_BREAK_LOOP support),
    switch_back_to_main_tab, wait_until_only_main_tab_left,
    switch_to_tab_index, close_current_tab, switch_to_default_content

Each step is defined in steps.json with fields like:
    { "action": "click_selector", "strategy": "css", "selector": ".submit-btn" }

This runner executes them in order and logs all actions to console + rpa.log
```

## BUILD\build_1a_workflow_grammar_gate_entrypoints.py

**Module ID:** BUILD-1A

```
BUILD-1A: workflow grammar gate entrypoints spec.  
  
Single responsibility:  
- Provide a deterministic mapping of console_script style entrypoints for packaging/CI.  
  
This does not perform packaging; it only returns data (pure helpers).
```

## BUILD\build_2a_nl_spec_generator.py

**Module ID:** BUILD-2A

```
BUILD-2A — Natural Language → Build Spec Generator  
  
Goal:  
- Accept plain-English process descriptions  
- Convert them into a structured spec that can be consumed by BUILD-1A (or passed  
  through as workflow steps directly)  
- Respect the supported STEP_GRAMMAR (no Selenium execution here)  
  
Notes:  
- This module is deterministic and rule-based (no LLM calls, no randomness).  
- It prefers `selector_ref` and emits placeholder selector hints for later capture.  
- IMPORTANT: Final emitted actions are filtered to what exists in REGISTRY, but  
  action names are normalized to canonical STEP_GRAMMAR vocabulary.
```

## BUILD\build_2a_repeat_support.py

**Module ID:** BUILD-2A

```
BUILD-2A — Repeat Support (Milestone 12.5.7)  
  
Purpose  
-------  
Provide deterministic, rule-based helpers for BUILD-2A that:  
- preserve `repeat` blocks (instead of flattening them)  
- normalize actions using an alias->canonical mapping (ACTION_MAP)  
- filter steps to those allowed by the action registry  
- validate steps recursively, including nested `repeat` blocks  
  
Notes  
-----  
- This module is intentionally pure/deterministic (no I/O, no registry reads).  
- It is designed to be called by BUILD/build_2a_nl_spec_generator.py.
```

## BUILD\build_2b_plan_optimizer.py

**Module ID:** BUILD-2B

```
BUILD-2B — Workflow Plan Optimizer (pure transformation)  
  
Takes a spec (from BUILD-2A or BUILD-1B) and optimizes it *before* BUILD-1A  
compiles it into a workflow.  
  
Constraints:  
- No Selenium execution.  
- Deterministic.  
- Only uses existing STEP_GRAMMAR actions (does not invent new step types).  
- Does not remove non-redundant required steps (conservative removals only).
```

## BUILD\build_2c_full_bundle.py

**Module ID:** BUILD-2C

```
BUILD-2C — Full Automation Bundle Generator (orchestration only)  
  
Pipeline (explicit imports, no dynamic resolution required):  
1) BUILD-2A: NL -> spec  
2) BUILD-2B: optimize spec  
3) BUILD-1A: spec -> workflow JSON  
4) BUILD-1C: workflow -> smoke test stub  
5) optional: run via RUN-1A  
  
Constraints:  
- No Selenium logic here  
- No duplication of submodule logic (this is an orchestrator)  
- Deterministic outputs (stable filenames derived from description)
```

## BUILD\build_2d_determinism.py

**Module ID:** SHA-256

```
Deterministic canonicalization / serialization utilities.  
  
Single responsibility:  
- Convert common Python structures into a canonical JSON-compatible form.  
- Provide stable JSON dumps and stable SHA-256 fingerprints.  
  
This is useful for ensuring workflow/selector/bundle generation is deterministic  
(given the same logical inputs, the produced artifacts can be compared reliably).
```

## BUILD\build_2d_step_grammar_gate.py

**Module ID:** BUILD-2D

```
BUILD-2D: Step grammar enforcement / gating.  
  
Single responsibility:  
- Validate that a workflow "steps" list only uses supported STEP_GRAMMAR actions.  
- Provide pure, deterministic helpers to find/strip unsupported steps.
```

## BUILD\build_2e_workflow_grammar_gate.py

**Module ID:** BUILD-2E

```
BUILD-2E: Workflow-level wrapper around BUILD-2D step grammar enforcement.  
  
Single responsibility:  
- Apply step grammar validation/sanitization to a *workflow dict* (not just steps).  
- Keep behavior pure and deterministic; do not mutate inputs.
```

## BUILD\build_2f_workflow_file_grammar_gate.py

**Module ID:** BUILD-2F

```
BUILD-2F: File-level workflow grammar gating.  
  
Single responsibility:  
- Load a workflow JSON file (dict with "steps"), validate or sanitize its step actions  
  using BUILD-2E/2D gates, and optionally write the sanitized workflow back.  
  
This module is additive: it does not modify any existing builders; it provides a  
safe wrapper you can call from CLI/build scripts.
```

## BUILD\build_2g_workflow_tree_grammar_gate.py

**Module ID:** BUILD-2G

```
BUILD-2G: Directory/tree-level workflow grammar gating.  
  
Single responsibility:  
- Find workflow JSON files under a directory (deterministic order).  
- Batch assert/sanitize them using BUILD-2F.  
  
This is additive and does not modify existing builders.
```

## CAPTURE\capture_1a_semi_auto.py

**Module ID:** CAPTURE-1A

```
CAPTURE-1A — Semi-Automatic Selector Capture (headed capture session)  
  
Developer tool:  
- Launches a headed browser session (forces headless off)  
- User clicks an element once  
- Captures element attributes + generates selector candidates (CSS + XPath)  
- Prompts user to choose a candidate  
- Saves into SELECTOR-1A registry JSON format (preserving existing entries)  
  
Notes:  
- User click is only for capture. No coordinate clicking automation is used for production.  
- Prints instructions (interactive developer tool).
```

## CLI\cli_1a_run_pipeline.py

**Module ID:** CLI-1A

```
CLI-1A — Command Line Pipeline Runner.  
  
Provides:  
- run_pipeline(cfg) -> run summary dict (PIPE-2E)  
- __main__ runnable entry point (uses an inline config for now)  
  
Integrations:  
- ENTRY-1A: WebDriver creation (best-effort resolution)  
- LOG-1A: logging init + structured events (best-effort resolution)  
- PIPE orchestration: prefer PIPE-2C wrapper; fallback to PIPE runner (PIPE-1E/PIPE-2B)  
- PIPE-2E: run summary object
```

## CLI\cli_1a_workflow_grammar_gate.py

**Module ID:** CLI-1A

```
CLI-1A: Workflow grammar gate CLI.  
  
Single responsibility:  
- Parse argv, load optional baseline/meta JSON, call RUN-1A, print compact output,  
  and return an exit code (no sys.exit inside core function).  
  
This is a thin wrapper over RUN/run_1a_workflow_grammar_gate_run.py.
```

## CLI\cli_1b_config_loader.py

**Module ID:** CLI-1B

```
CLI-1B — Configuration Loader.  
  
Loads configuration from JSON or YAML files and expands environment variables like:  
  ${HOME}  
  ${RUN_ID}  
  
Format support:  
- JSON: always supported.  
- YAML: supported via PyYAML (yaml.safe_load) if installed.  
  If PyYAML is unavailable, default behavior is "JSON-only" (clear error for YAML).  
  
Compatibility / preserving existing functionality:  
- This module still includes the prior minimal YAML parser for very simple YAML files.  
  It is **opt-in** when PyYAML is not installed by setting:  
      CLI_CONFIG_ALLOW_MINIMAL_YAML=1  
  (This preserves the previously-working fallback behavior without violating the  
  "JSON-only without PyYAML" default expectation.)  
  
Environment expansion:  
- Expands ${VAR_NAME} in string *values* recursively (not keys).  
- If a referenced env var is missing, raises a clear error.
```

## CLI\cli_1c_args_overrides.py

**Module ID:** CLI-1C

```
CLI-1C — CLI Flags + Overrides  
  
Adds argparse flags and a pure function to apply runtime overrides onto an existing  
config dict (typically produced by CLI-1B load_config()).  
  
Integration snippet (CLI-1A style)  
----------------------------------  
    from CLI.cli_1b_config_loader import load_config  
    from CLI.cli_1c_args_overrides import build_arg_parser, apply_overrides  
  
    parser = build_arg_parser()  
    args = parser.parse_args()  
  
    cfg = {}  
    if args.config:  
        cfg = load_config(args.config)  
  
    cfg = apply_overrides(cfg, args)  
  
Rules  
-----  
- Flags take precedence over config values.  
- apply_overrides does NOT mutate the incoming cfg; it returns a new dict.
```

## CLI\cli_1f_generate_reports.py

**Module ID:** CLI-1F

```
CLI-1F — Generate reports for a run output directory (10.4.3)  
  
Single responsibility:  
- Parse CLI args and invoke RUN-1E post-run reporting hook.  
  
Usage:  
  python -m CLI.cli_1f_generate_reports --run-output-dir <dir>
```

## CLI\cli_1g_workflow_grammar_gate.py

**Module ID:** CLI-1G

```
CLI-1G: Workflow grammar gate CLI.  
  
Single responsibility:  
- Provide a small CLI entrypoint to assert/sanitize workflow JSON files under a directory  
  using BUILD-2G, and optionally emit a deterministic JSON report using REPORT-1A.  
  
Exit codes (deterministic):  
- 0: success (assert mode with no violations OR sanitize mode completed)  
- 2: assert mode found violations  
- 1: unexpected error / invalid usage
```

## CLI\cli_1h_workflow_grammar_gate_pipeline.py

**Module ID:** CLI-1H

```
CLI-1H: Workflow grammar gate pipeline CLI.  
  
Single responsibility:  
- Provide an argparse-based CLI wrapper around PIPE-1A pipeline runner.  
- Optionally emits:  
  - JSON report via PIPE (report_json_path)  
  - Text report via REPORT-1B (report_text_path and/or stdout)  
  
Does not invent new workflow step types; only gates workflows.
```

## CLI\cli_2b_unified.py

**Module ID:** CLI-2B

```
CLI-2B — Unified Automation Command Interface (orchestration only)  
  
Commands:  
- auto <natural_language>   -> BUILD-2C (build bundle) then optional AGENT-2A run  
- run <workflow_path>       -> RUN-1A (best effort)  
- doctor                    -> DOCTOR-1A (best effort)  
- history                   -> print history summary (reads jsonl)  
- replay <run_id>           -> REPLAY-1A (best effort)  
- report <run_id>           -> REPORT-1A (best effort)  
  
UX constraints:  
- no stack traces shown to user  
- clear success/failure messages
```

## CLI\cli_pack_1a.py

**Module ID:** PACK-1A

```
PACK-1A — Golden-Path CLI (one-command framework usage)  
  
CLI commands:  
- run <workflow_path>        -> calls RUN-1A  
- report <run_id>            -> calls REPORT-1A  
- replay <run_id>            -> calls REPLAY-1A  
- heal <workflow_path> --from-run <run_id> -> loads diagnosis from artifacts/<run_id>, calls HEAL-1A patch generator  
- doctor                     -> calls DOCTOR-1A  
- history                    -> prints summary from HISTORY-1A  
  
Rules:  
- Orchestrate existing modules; do not re-implement their core logic.  
- Human readable output; no stack traces unless failure (or --debug).  
- Exit code 0 on success; 1 on failure.
```

## DEPLOY\deploy_1a_service_runner.py

**Module ID:** DEPLOY-1A

```
DEPLOY-1A — Runtime Service + Packaging (service runner)  
  
No Selenium logic. Orchestration + lifecycle only.  
Reuses AGENT-2A as the execution engine.  
  
Public API:  
- run_service(workflows, interval_seconds=300, cfg=None) -> None  
- run_single_job(workflow, cfg=None) -> dict  
  
Notes:  
- run_service loops until stopped (KeyboardInterrupt) or until cfg["max_cycles"] (if provided) is reached.  
- Exceptions are caught and logged; service continues.
```

## dev\dev_smoke_act_1b_logging.py

**Module ID:** ACT-1B

```
Dev smoke test for ACT-1B logging integration.  
  
- Uses ENTRY-1A to create a driver  
- Uses LOG-1A for one-line JSON logs  
- Opens example.com  
- Executes 2–3 steps through ACT-1B, showing automatic step_* logs  
  
Run:  
  python dev_smoke_act_1b_logging.py
```

## dev\dev_smoke_act_1c.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_act_1c.py
```

## dev\dev_smoke_act_action_engine.py

**Module ID:** ACT-1A

```
Dev smoke test for ACT-1A action engine.  
  
- Uses ENTRY-1A webdriver bootstrap  
- Opens example.com  
- Runs a small varied set of step types  
- Prints structured results  
  
Run:  
  python dev_smoke_act_action_engine.py
```

## dev\dev_smoke_act_download_wait.py

**Module ID:** UNKNOWN

```
Dev smoke test for ACT download_wait integration.
 
This validates:
ENTRY -> ACT -> NAV -> filesystem
 
It simulates a download by creating a file
while ACT waits for it.
```

## dev\dev_smoke_auth_1a.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_auth_1a.py
```

## dev\dev_smoke_auth_1b.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_auth_1b.py
```

## dev\dev_smoke_cli_1a.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_cli_1a.py
```

## dev\dev_smoke_cli_1b.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_cli_1b.py
```

## dev\dev_smoke_cli_1b_config_loader.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_cli_1b_config_loader.py
```

## dev\dev_smoke_cli_1c.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_cli_1c.py
```

## dev\dev_smoke_doc_1a.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_doc_1a.py
```

## dev\dev_smoke_entry_bootstrap.py

**Module ID:** ENTRY-1A

```
Smoke Test: ENTRY-1A webdriver bootstrap (Edge + Chrome)
 
Runs quick headless boots for each supported browser and navigates to https://example.com.
 
Usage:
  python dev_smoke_entry_bootstrap.py
  python dev_smoke_entry_bootstrap.py --headed
  python dev_smoke_entry_bootstrap.py --browser edge
  python dev_smoke_entry_bootstrap.py --browser chrome
 
Notes:
- This is intentionally NOT pytest. It's a fast manual sanity check.
- Requires drivers under ./drivers/ OR DRIVER_PATH/RPA_DRIVER_PATH set.
```

## dev\dev_smoke_input_1b_excel_provider.py

**Module ID:** INPUT-1B

```
Smoke test for top-level INPUT-1B shim: input_1b_excel_provider.py  
  
How to run:  
  python dev/dev_smoke_input_1b_excel_provider.py
```

## dev\dev_smoke_log_1b.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_log_1b.py
```

## dev\dev_smoke_nav_1a.py

**Module ID:** NAV-1A

```
Dev smoke test for NAV-1A Selenium helpers.
 
- Uses ENTRY-1A to create a WebDriver
- Opens example.com
- Demonstrates wait_for_visible + click
 
Run:
  python dev_smoke_nav_1a.py
```

## dev\dev_smoke_out_1a.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_out_1a.py
```

## dev\dev_smoke_out_1b.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_out_1b.py
```

## dev\dev_smoke_pipe_1a.py

**Module ID:** PIPE-1A

```
Dev smoke test for PIPE-1A run orchestrator.  
  
Creates a tiny 2-ID worklist (as an .xlsx) and runs a short step sequence against  
example.com through the full pipeline:  
INPUT-1B -> LOOP-1B -> ACT-1B -> STATE-1B, with LOG-1A enabled.  
  
Run:  
  python dev_smoke_pipe_1a.py
```

## dev\dev_smoke_pipe_1b.py

**Module ID:** PIPE-1B

```
Dev smoke test — PIPE-1B (worklist configuration adapter)  
  
Purpose  
-------  
Validate that PIPE.pipe_1b_worklist_config correctly:  
1) Resolves configuration into a normalized worklist spec  
2) Loads IDs from an Excel worklist via INPUT-1B through the PIPE-1B adapter  
  
How it works  
------------  
- If env var WORKLIST_PATH points to an existing Excel file, the script uses it.  
- Otherwise, it attempts to generate a temporary .xlsx using pandas (if available).  
  
Config keys used (required by test)  
-----------------------------------  
- WORKLIST_PATH  
- WORKLIST_SHEET  
- WORKLIST_ID_COLUMN
```

## dev\dev_smoke_pipe_1c.py

**Module ID:** PIPE-1C

```
Dev smoke test — PIPE-1C (steps loader + template substitution)  
  
Behavior  
--------  
- Create a temp directory and write a small steps.json file containing:  
    - get to https://example.com (via ${BASE_URL})  
    - wait_for_element on ("css", "h1")  
    - js step returning a dict and using save_as  
- Build cfg:  
    - STEPS_PATH -> temp steps.json  
    - browser/headless/waits set to common defaults  
    - Does NOT require a real Excel; omits WORKLIST_PATH on purpose  
- Call:  
    steps = load_steps_from_cfg(cfg)  
    summary = PIPE.pipe_1a_run_orchestrator.run_worklist(cfg, steps)  
- Print:  
    - resolved steps count  
    - summary JSON  
- Exit 0 if summary["failed"] == 0 else exit 1
```

## dev\dev_smoke_pipe_1d_a.py

**Module ID:** PIPE-1D

```
Dev smoke test — PIPE-1D (step execution adapter)  
  
Flow  
----  
1) Use ENTRY-1A to create driver  
2) Load steps from PIPE-1C  
3) Execute steps through PIPE-1D  
4) Run: get example.com -> wait_for_element h1 -> js return document.title  
5) Print results for each step  
6) Exit 0 if all steps succeed
```

## dev\dev_smoke_pipe_1e.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev_smoke_pipe_1e.py
```

## dev\dev_smoke_pipe_2a.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_pipe_2a.py
```

## dev\dev_smoke_pipe_2b.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_pipe_2b.py
```

## dev\dev_smoke_pipe_2c.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_pipe_2c.py
```

## dev\dev_smoke_pipe_2d.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_pipe_2d.py
```

## dev\dev_smoke_pipe_2e.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_pipe_2e.py
```

## dev\dev_smoke_state_1c.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_state_1c.py
```

## dev\dev_smoke_state_1d.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_state_1d.py
```

## dev\dev_smoke_state_input.py

**Module ID:** INPUT-1B

```
Smoke test for:
- INPUT/input_1b_excel_provider.py
- STATE/state_1b_manifest_jsonl.py
 
What it does:
1) Creates a tiny Excel file (if missing) with sheet+column you can control.
2) Uses INPUT-1B to extract IDs and (optionally) write a baseline manifest.jsonl.
3) Uses STATE-1B to choose active manifest, load IDs, and append an audit record.
4) Creates a retry manifest with a subset of IDs and verifies STATE chooses it.
 
How to run:
  python dev_smoke_state_input.py
 
Notes:
- Adjust imports at the top if your function names differ.
- This script is intentionally "loud" with prints and assertions.
```

## dev\dev_smoke_val_1a.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_val_1a.py
```

## dev\dev_smoke_val_1b.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_val_1b.py
```

## dev\dev_smoke_var_1a.py

**Module ID:** UNKNOWN

```
How to run:  
  python dev/dev_smoke_var_1a.py
```

## dev\sitecustomize.py

**Module ID:** UNKNOWN

```
Dev bootstrap: ensure repo root is on sys.path.  
  
When running:  
  python dev/dev_smoke_state_input.py  
  
Python typically puts the *dev/* directory on sys.path (not the repo root),  
so imports like `import INPUT...` can fail. This file is auto-imported by  
Python's `site` module (unless -S is used) and adds the repo root deterministically.
```

## DIFF\diff_12a_reviewable_diffs.py

**Module ID:** DIFF-12A

```
DIFF-12A: Reviewable Diffs (Milestone 12.2.2)  
  
Single responsibility:  
- Provide deterministic, reviewable diffs for workflow/selector changes.  
- Canonicalize JSON (stable key ordering) to avoid noisy diffs from formatting/key order.  
  
This module is intentionally additive: it does not enforce policy automatically.  
CI/BUILD governance can call these helpers to require diff artifacts and/or  
block changes without reviewable diffs.
```

## DIFF\diff_1a_config_changes.py

**Module ID:** DIFF-1A

```
DIFF-1A — Workflow & Selector Change Diff + Version Stamp  
  
Deterministic change-tracking utilities:  
- compute stable fingerprints (hashes) for workflows + selectors + schema  
- diff two fingerprints  
- write fingerprint + diff reports (JSON + MD)  
  
No Selenium.
```

## DIFF\diff_1a_workflow_grammar_gate_report_diff.py

**Module ID:** DIFF-1A

```
DIFF-1A: Workflow grammar gate report diff.  
  
Single responsibility:  
- Compute a deterministic structured diff between two workflow-grammar-gate  
  report dicts (as produced by REPORT/PIPE/DOCTOR layers).
```

## DOC\doc_12a_slos_success_criteria.py

**Module ID:** DOC-12A

```
DOC-12A: SLOs and Success Criteria (Milestone 12.1.1)  
  
Single responsibility:  
- Provide deterministic, reviewable definitions for operational SLOs and  
  production success criteria for this RPA framework.  
- Provide pure renderers to Markdown/JSON for operator documentation.  
  
Notes:  
- This module is intentionally framework-agnostic: it does not assume any  
  particular deployment environment or external monitoring stack.  
- Where measurement hooks depend on other modules, they are described as  
  "Measurement" fields rather than invoked directly.
```

## DOC\doc_12b_operator_runbooks.py

**Module ID:** DOC-12B

```
DOC-12B: Operator Runbooks (Milestone 12.1.2)  
  
Single responsibility:  
- Provide deterministic, reviewable operator runbooks for production operation  
  of the Selenium RPA framework.  
- Provide pure renderers to Markdown/JSON for operator-facing documentation.  
  
Notes:  
- This module avoids hard-coding environment-specific commands. Where CLI entry  
  points vary by installation, steps call out "use your standard runner entry point".
```

## DOC\doc_12c_support_escalation_paths.py

**Module ID:** DOC-12C

```
DOC-12C: Support and Escalation Paths (Milestone 12.1.3)  
  
Single responsibility:  
- Define deterministic, reviewable support + escalation standards for operating  
  the RPA framework in production.  
- Provide pure renderers (Markdown/JSON) for operator documentation.  
  
Scope:  
- Defines roles, severity taxonomy, response targets, escalation matrix, and  
  incident ticket requirements. Does not integrate with any external paging/ticketing.
```

## DOC\doc_12d_rollback_recovery_procedures.py

**Module ID:** DOC-12D

```
DOC-12D: Rollback and Recovery Procedures (Milestone 12.4.3)  
  
Single responsibility:  
- Provide a canonical, deterministic rollback/recovery playbook structure for operators.  
- Provide deterministic renderers (Markdown/JSON) and a minimal validator.  
  
Determinism:  
- No timestamps generated.  
- Stable ordering (procedures sorted by procedure_id).  
- JSON uses sort_keys=True.
```

## DOC\doc_1a_library_index.py

**Module ID:** DOC-1A

```
DOC-1A — Library Index Generator  
  
Generates:  
- DOC/LIBRARY_INDEX.md  
- DOC/library_index.json  
  
Constraints:  
- Must not import project modules (avoid side effects).  
- Only reads files from disk and parses using stdlib (ast, json, pathlib, etc).
```

## DOC\doc_1a_workflow_grammar_gate.py

**Module ID:** DOC-1A

```
DOC-1A: Workflow grammar gate documentation builder.  
  
Single responsibility:  
- Produce deterministic Markdown documentation for the workflow grammar gate subsystem.  
- No I/O; formatting only.
```

## DOC\doc_1g_doc_index_entry_contract.py

**Module ID:** DOC-1G

```
DOC-1G — Doc Index Entry Contract (Validator)  
  
Single responsibility:  
- Validate the dict shape expected by DOC.doc_1f_doc_index_aggregator.collect_doc_index_entries_1a().  
  
This module is pure + deterministic and safe to import (no side effects).
```

## DOC\doc_1h_doc_index_collect_validate.py

**Module ID:** DOC-1H

```
DOC-1H — Doc Index Collect + Validate Wrapper  
  
Single responsibility:  
- Collect doc-index entries using DOC-1F and validate them using DOC-1G.  
  
Why:  
- Prevent silent omissions: if a module is discovered but its entry shape is wrong,  
  validation can fail fast with actionable errors.  
  
Deterministic, side-effect free beyond what the collector already does.
```

## DOC\runbook_1a_generator.py

**Module ID:** RUNBOOK-1A

```
RUNBOOK-1A — Operational Playbook Generator  
  
Pure documentation generator. No Selenium.  
Writes a deterministic Markdown runbook describing how to use/run/debug/maintain the system.
```

## DOCTOR\doctor_12a_pre_run_checks.py

**Module ID:** DOCTOR-12A

```
DOCTOR-12A: Pre-run DOCTOR Checks Policy (Milestone 12.4.1)  
  
Single responsibility:  
- Define a deterministic pre-run DOCTOR policy (especially for production).  
- Provide a pure evaluator that decides pass/fail from supplied evidence.  
- Provide deterministic renderers (Markdown/JSON) for operator-facing documentation.  
  
Determinism constraints:  
- No timestamps.  
- Stable ordering (sorted by check_id).  
- JSON rendering uses sort_keys=True.
```

## DOCTOR\doctor_12d_release_readiness_gate.py

**Module ID:** DOCTOR-12D

```
DOCTOR-12D: Release Readiness Gate (Milestone 12.5.6)  
  
Single responsibility:  
- Provide a deterministic "release readiness" gate:  
  - canonical readiness policy (required checks by env)  
  - pure evaluator that consumes caller-supplied observations  
  - deterministic JSON/Markdown renderers  
  
Determinism:  
- No timestamps generated.  
- Stable ordering by check_id.  
- JSON uses sort_keys=True.  
  
This module does NOT execute workflows and does NOT mutate state.
```

## DOCTOR\doctor_1a_check.py

**Module ID:** DOCTOR-1A

```
DOCTOR-1A — Environment Self-Check (“preflight”)  
  
Deterministic preflight checker:  
- No Selenium required (optional import only to validate installation)  
- No driver launching (file existence only)  
- Best-effort git branch detection (no subprocess)  
  
Public API:  
  run_preflight(root=".", strict=False, cfg=None) -> dict  
  format_preflight_report(result: dict) -> str
```

## DOCTOR\doctor_1a_workflow_grammar_gate.py

**Module ID:** DOCTOR-1A

```
DOCTOR-1A: Workflow grammar gate (programmatic check/fix).  
  
Single responsibility:  
- Provide a DOCTOR-layer API to (a) check workflows for unsupported actions without writing,  
  or (b) sanitize workflows (in-place or to output_dir), and always produce a structured report.  
  
Builds on:  
- BUILD-2G for tree gating  
- REPORT-1A for deterministic report generation
```

## DOCTOR\doctor_1b_workflow_grammar_gate.py

**Module ID:** DOCTOR-1B

```
DOCTOR-1B: Workflow grammar gate diagnosis (PIPE-backed).  
  
Single responsibility:  
- Provide a programmatic "doctor" API that runs the PIPE workflow grammar gate  
  and returns a deterministic diagnosis object (status + report text).  
  
Notes:  
- No CLI parsing here (CLI-1H owns argv handling).  
- Does not duplicate BUILD/REPORT logic; delegates to PIPE + REPORT-1B.
```

## ENTRY\entry_1a_webdriver_bootstrap.py

**Module ID:** ENTRY-1A

```
ENTRY-1A — Standard headless-first webdriver bootstrap (Chrome/Edge configurable)  
  
Purpose  
-------  
Create and configure a Selenium WebDriver with consistent defaults for:  
- headless mode  
- download directory behavior  
- stability flags for CI/headless environments  
- optional attach-to-existing-browser via remote debugging port  
  
Inputs  
------  
cfg: Mapping[str, Any] typically populated from env/CLI. Supported keys:  
- BROWSER: "edge" or "chrome" (default: "edge")  
- HEADLESS: truthy string ("1"/"true"/"yes"/"on") enables headless  
- DOWNLOAD_DIR: downloads folder path (default: env RPA_DOWNLOAD_DIR else "downloads")  
- IMPLICIT_WAIT: seconds for Selenium implicit wait (default: 0)  
- PAGELOAD_TIMEOUT: seconds for page load timeout (optional)  
- DEBUG_PORT: optional port number string (alternate to env REMOTE_DEBUG_PORT)  
- DRIVER_PATH: optional explicit driver path (alternate to env RPA_DRIVER_PATH)  
  
Selenium Manager controls (optional)  
------------------------------------  
- SELENIUM_MANAGER / USE_SELENIUM_MANAGER: truthy => force Selenium Manager (ignore DRIVER_PATH)  
- SELENIUM_MANAGER_FALLBACK: truthy/falsey => if local driver fails due to version mismatch,  
  retry using Selenium Manager. Default: enabled.  
  
Outputs  
-------  
- selenium WebDriver instance (Edge or Chrome)  
  
When to use  
-----------  
- You need a consistent local webdriver bootstrap with predictable headless + downloads behavior.  
  
When NOT to use  
---------------  
- You need Selenium Grid / remote execution.  
- You need enterprise profile/cert injection or special SSO policies (propose a new ENTRY option).  
  
Headless notes  
--------------  
- Uses Chromium headless mode ("--headless=new") when HEADLESS is enabled.  
- Adds common flags: --no-sandbox, --disable-dev-shm-usage, --disable-gpu  
  
Dependencies  
------------  
- selenium  
- standard library: os, pathlib, typing  
  
Common failure modes + mitigations  
----------------------------------  
- Driver binary missing -> FileNotFoundError with actionable path (unless Selenium Manager is enabled).  
- Driver version mismatch -> SessionNotCreatedException; with fallback enabled this will retry via Selenium Manager.  
- Debug attach fails -> verify browser launched with remote debugging port enabled.  
  
Minimal usage example  
---------------------  
from ENTRY.entry_1a_webdriver_bootstrap import make_driver  
cfg = {"BROWSER": "chrome", "HEADLESS": "true", "DOWNLOAD_DIR": "downloads"}  
driver = make_driver(cfg)  
driver.get("https://example.com")  
driver.quit()
```

## ENTRY\entry_1a_workflow_grammar_gate.py

**Module ID:** ENTRY-1A

```
ENTRY-1A: Workflow grammar gate entry point.  
  
Single responsibility:  
- Provide a thin ENTRY-layer wrapper around CLI-1H's cli_main, suitable for console entrypoints.
```

## GUARD\guard_12a_prod_defaults.py

**Module ID:** GUARD-12A

```
GUARD-12A: Production-default GUARD Policy (Milestone 12.4.2)  
  
Single responsibility:  
- Define deterministic GUARD policy defaults, especially for production.  
- Provide a pure evaluator that checks a workflow (dict) + selectors (dict) against the policy.  
- Provide deterministic Markdown/JSON renderers for operator-facing docs.  
  
Notes:  
- This module does not execute Selenium, and does not mutate workflows.  
- It is intended to be called by RUN/PIPE layers before execution in production.  
- Deterministic: no timestamps; stable ordering of violations.  
  
Policy intent (prod defaults):  
- Disallow exec_js / exec_js_file by default.  
- Require https URLs for open.  
- Optionally restrict open hostnames.  
- Require selector_ref (not raw selector strings) for selector-based steps.  
- Require selector_ref keys to exist in selectors bundle.
```

## GUARD\guard_1a_runtime.py

**Module ID:** GUARD-1A

```
GUARD-1A — Runtime Guardrails (stability layer)  
  
Pure wrapper utilities:  
- No Selenium driver creation  
- Must NOT duplicate ACT/NAV logic (wrap existing runners only)  
  
Public API:  
  wrap_step_runner(step_runner_fn, *, cfg) -> wrapped_fn  
  guarded_call(fn, *, retries, retry_on, on_retry=None) -> object  
  normalize_guard_cfg(cfg) -> dict
```

## GUARD\guard_1a_workflow_grammar_gate_guard.py

**Module ID:** GUARD-1A

```
GUARD-1A: Workflow grammar gate guard.  
  
Single responsibility:  
- Evaluate a workflow-grammar-gate report against deterministic policy thresholds,  
  optionally comparing to a baseline report (delta policy), and return a decision  
  suitable for CI gating.  
  
Builds on:  
- REPORT-1C for summary extraction  
- DIFF-1A for baseline delta computation
```

## GUARD\guard_1a_workflow_grammar_guard.py

**Module ID:** GUARD-1A

```
GUARD-1A: Workflow grammar guard.  
  
Single responsibility:  
- Provide a GUARD-layer wrapper around RUN-1A gating that:  
  - returns a workflow dict safe to execute (validated or sanitized)  
  - optionally raises a more informative ValueError message on violations
```

## HEAL\heal_1a_patch_workflow.py

**Module ID:** HEAL-1A

```
HEAL-1A — Auto-fix Suggestion Applier (workflow patch generator)  
  
Pure utility:  
- No Selenium calls  
- File I/O allowed for reading workflow + writing patch outputs  
- Deterministic rule-based patching driven by REASON-1A diagnosis object  
  
Public API:  
  apply_diagnosis_patch(workflow_path, *, diagnosis, output_dir="workflows", selector_patch_path=None) -> dict
```

## HISTORY\history_12a_audit_logging_replay_spec.py

**Module ID:** HISTORY-12A

```
HISTORY-12A: Audit-Friendly Logging + Replay Spec (Milestone 12.5.3)  
  
Single responsibility:  
- Define a canonical, deterministic spec for audit logs and replay index artifacts.  
- Provide pure validators for events/index.  
- Provide deterministic renderers (Markdown/JSON) and deterministic JSONL serialization.  
- Provide deterministic SHA256 hashing of canonical event JSON.  
  
Determinism:  
- No timestamps generated (timestamps, if present, are caller-supplied strings).  
- Stable ordering for rendering/serialization (sort by seq then event_type then run_id).  
- JSON uses sort_keys=True.  
  
This module does NOT write runtime logs automatically and does NOT perform replay.  
It defines a stable, audit-friendly structure that other layers can emit/consume.
```

## HISTORY\history_1a_run_manifest.py

**Module ID:** HISTORY-1A

```
HISTORY-1A — Run manifest (10.2.1)  
  
Single responsibility:  
- Build and write a stable run manifest JSON under a provided run output directory.  
  
Notes:  
- Deterministic JSON formatting (sorted keys, stable indentation).  
- Relative paths normalized to POSIX-style for cross-platform stability.  
- This module does not record step outcomes (10.2.2) and does not normalize errors (10.2.3).
```

## HISTORY\history_1a_store.py

**Module ID:** HISTORY-1A

```
HISTORY-1A — Run History Store (append-only JSONL)  
  
- No Selenium  
- Append-only JSONL history suitable for analytics/agent reasoning  
- Sanitizes records to avoid secrets  
  
Public API:  
  sanitize_run_record(record: dict) -> dict  
  append_run_history(record: dict, *, history_path="history/run_history.jsonl") -> Path  
  read_run_history(*, history_path="history/run_history.jsonl", limit=200) -> list[dict]  
  summarize_history(rows: list[dict]) -> dict
```

## HISTORY\history_1a_workflow_grammar_gate_history.py

**Module ID:** HISTORY-1A

```
HISTORY-1A: Workflow grammar gate history.  
  
Single responsibility:  
- Persist and load workflow-grammar-gate run records to/from a JSONL file, with  
  deterministic serialization and deterministic run_id derivation (when omitted).
```

## HISTORY\history_1b_step_outcomes.py

**Module ID:** HISTORY-1B

```
HISTORY-1B — Step outcomes recorder (10.2.2)  
  
Single responsibility:  
- Build and append per-step outcome records to a JSONL file under a run output dir.  
  
This module does NOT:  
- normalize exceptions/tracebacks in a structured way (10.2.3)  
- run steps or interact with Selenium
```

## HISTORY\history_1c_error_normalization.py

**Module ID:** HISTORY-1C

```
HISTORY-1C — Error normalization (10.2.3)  
  
Single responsibility:  
- Normalize Python exceptions into a deterministic, JSON-serializable structure  
  suitable for history logs and reports.  
  
Design notes:  
- Avoid repr() (can include memory addresses).  
- Traceback filenames are normalized (default: basename only) for cross-machine stability.  
- Supports __cause__ and __context__ chaining with bounded depth.
```

## HISTORY\history_1c_run_history_loader.py

**Module ID:** HISTORY-1C

```
HISTORY-1C — Run history loader (9.4.3)  
  
Single responsibility:  
- Load HISTORY artifacts for a run_output_dir:  
  - Run manifest (HISTORY-1A*)  
  - Step outcomes (HISTORY-1B*) from JSONL or JSON  
  
This module is intentionally file-layout tolerant:  
- It scans {run_output_dir}/history first (if present), otherwise scans run_output_dir.  
- It identifies artifacts by 'schema' prefixes (HISTORY-1A / HISTORY-1B).  
  
Deterministic behavior:  
- Candidate paths are processed in sorted order.  
- Step outcomes are returned sorted by (step_index, original_order).
```

## INPUT\input_1b_excel_provider.py

**Module ID:** INPUT-1B

```
INPUT-1B — Excel provider (sheet + column -> list of IDs) + optional manifest writer  
  
Purpose  
-------  
Read an Excel worksheet, extract a primary-key column into a normalized worklist,  
and (optionally) write a minimal manifest JSONL with one object per ID.  
  
This module is responsible for Excel ingestion only. It intentionally does NOT:  
- write audit logs  
- select retry vs baseline manifests  
- implement per-item looping  
  
Dependencies  
------------  
- openpyxl (for .xlsx reading/writing)  
  
Security rule  
-------------  
- Never log secrets. Treat IDs as non-secret operational identifiers.
```

## LEARN\learn_1a_failure_patterns.py

**Module ID:** LEARN-1A

```
LEARN-1A — Failure Pattern Analytics (pure, deterministic)  
  
Analyzes HISTORY-1A JSONL rows to identify recurring failure patterns and produce  
actionable recommendations compatible with the existing STEP_GRAMMAR.  
  
No Selenium. No side effects beyond reading a history file in load_history().
```

## LEARN\learn_1b_selector_intelligence.py

**Module ID:** LEARN-1B

```
LEARN-1B — Selector Intelligence & Stability Scoring (pure analysis)  
  
Analyzes HISTORY rows to:  
- compute per-selector usage/failure counts  
- derive stability scores  
- identify low-stability / high-risk selectors  
- generate general, actionable recommendations (no DOM access, no workflow edits)  
  
No Selenium execution. Deterministic.
```

## LINT\lint_1a_steps_validator.py

**Module ID:** LINT-1A

```
LINT-1A — Step Validation Engine  
  
Validates step definitions (steps.json) against SCHEMA/steps_schema.json (SCHEMA-1A)  
*before execution*.  
  
Constraints:  
- Do NOT import/execute project modules with side effects.  
- Use SCHEMA output as the authority; do not re-derive schema from ACT/PIPE.
```

## LOG\log_1a_structured_logging.py

**Module ID:** LOG-1A

```
LOG-1A — Standard structured logging + run_id + per-item context (stdlib only)  
  
Purpose  
-------  
Establish a consistent, enterprise-friendly logging layer using ONLY the Python  
standard library (`logging`) that emits one-line JSON logs with:  
  
- Stable top-level keys:  
    timestamp_utc, level, logger, message, event,  
    run_id, current_id, item_index, total_items, fields  
- A lightweight context mechanism (run_id + per-item context) that works across  
  modules without passing logger adapters everywhere.  
- Built-in redaction to prevent accidental leakage of secrets.  
  
Inputs / Outputs  
----------------  
setup_logging(cfg) -> logging.Logger  
- Reads cfg keys:  
  - LOG_LEVEL (default "INFO")  
  - LOG_PATH (optional file path; enables rotating file logging)  
  - RUN_ID (optional; generated if missing)  
  - LOG_JSON (default true; retained for compatibility; JSON output remains the default)  
  - QUIET_CONSOLE (optional; suppress console handler if truthy)  
- Returns the base logger ("rpa") configured with handlers + JSON formatter.  
  
bind_context(cfg, **fields) -> None  
- Stores run_id/current_id/item_index/total_items into a context store.  
- Also ensures cfg["RUN_ID"] exists (generated if missing).  
- Common workflow usage: call once per run, and again per item.  
  
log_event(logger, event: str, **fields) -> None  
- Emits one structured JSON log line.  
- Redacts secrets by key name: password, secret, token, api_key (case-insensitive).  
  
log_exception(logger, exc, *, step_id=None, milestone=None, tag=None, event="exception", **fields) -> None  
- Emits one structured error log line with traceback + optional step metadata.  
  
When to use  
-----------  
- Any Selenium/RPA workflow where consistent, machine-parsable logs are needed.  
- CI runs, headless runs, enterprise environments requiring stdlib-only logging.  
  
When NOT to use  
---------------  
- If you need distributed tracing, OpenTelemetry exporters, or third-party logging stacks.  
  (This module intentionally stays stdlib-only; integrate downstream if needed.)  
  
Failure modes + mitigations  
---------------------------  
- Duplicate logs due to repeated setup: setup_logging() is idempotent and replaces handlers.  
- Non-JSON-serializable field values: values are JSON-dumped with default=str.  
- Secret leakage: keys matching the sensitive set are redacted; avoid passing whole cfg  
  or raw credential blobs into log_event fields.  
  
Minimal usage example  
---------------------  
from LOG.log_1a_structured_logging import setup_logging, bind_context, log_event  
  
cfg = {"LOG_LEVEL": "INFO"}  
logger = setup_logging(cfg)  
bind_context(cfg, run_id=cfg["RUN_ID"])  
  
log_event(logger, "run_start", version="1.0.0")  
bind_context(cfg, current_id="A123", item_index=1, total_items=10)  
log_event(logger, "item_start")
```

## LOG\log_1b_error_taxonomy.py

**Module ID:** LOG-1B

```
LOG-1B — Error Taxonomy + Exception Normalization.  
  
Provides a single place to:  
- define error codes  
- classify exceptions into safe, structured payloads  
- produce minimal manifest-friendly fields  
  
Constraints  
-----------  
- Does not modify/integrate with existing modules yet.  
- Must not leak secrets (best-effort redaction).
```

## LOOP\loop_1b_per_item.py

**Module ID:** LOOP-1B

```
LOOP-1B — Per-item loop (generic iterator over worklist)  
  
Purpose  
-------  
Provide a reusable, workflow-agnostic per-item execution loop that:  
- iterates a worklist of item IDs  
- injects per-item context into a shared cfg mapping (e.g., CURRENT_ID)  
- calls a caller-supplied `process_item` function for each item  
- supports either fail-fast (stop_on_error=True) or best-effort continuation  
  
This module is intentionally limited to loop orchestration (LOOP milestone).  
It does NOT:  
- read inputs from Excel/CSV/API (INPUT milestone)  
- select retry/baseline manifests or write audit JSONL (STATE milestone)  
- implement Selenium actions/steps execution (ACT/NAV milestones)  
  
Inputs  
------  
- work_items: iterable[str] of work item identifiers  
- cfg: mutable mapping used as shared run context (e.g., env-derived config)  
- process_item: callable invoked per item:  
    process_item(item_id: str, cfg: MutableMapping[str, Any]) -> Any  
- id_var: cfg key to store current item ID (default: "CURRENT_ID")  
- index_var: cfg key to store 1-based index (default: "ITEM_INDEX")  
- total_var: cfg key to store total items count (default: "TOTAL_ITEMS")  
- stop_on_error: if True, re-raise first exception; else continue and collect errors  
- on_* callbacks (optional): hooks for start/success/error events  
  
Outputs  
-------  
- list[ItemOutcome]: ordered results for each attempted item (including errors if not fail-fast)  
- cfg is mutated in-place with per-item variables during execution  
  
When to use  
-----------  
- Your automation runs the same workflow for a list of IDs (per-location/per-account/etc.).  
- You want a consistent way to inject CURRENT_ID and loop metadata into cfg.  
  
When NOT to use  
---------------  
- Single-run workflows with no worklist (use LOOP-1A).  
- Highly parallel processing (this loop is sequential).  
- You need retry-manifest selection/auditing (use STATE-1B alongside this).  
  
Headless notes  
--------------  
- Headless-agnostic; no browser operations.  
  
Dependencies  
------------  
- Standard library only: dataclasses, typing  
  
Common failure modes + mitigations  
----------------------------------  
- process_item raises -> fail-fast by default; set stop_on_error=False to continue.  
- cfg missing expected keys -> caller should initialize cfg; this module only injects loop vars.  
- work_items is a generator and you need total count -> this module materializes to list once.  
  
Security rule  
-------------  
- Never log secrets. This module does not handle credentials.  
  
Minimal usage example  
---------------------  
from LOOP.loop_1b_per_item import run_per_item_loop  
  
def process_one(item_id: str, cfg: dict) -> None:  
    # e.g., call your step runner here  
    cfg["CURRENT_ID"] = item_id  
    # run_steps(driver, steps, cfg)  
  
cfg = {}  
outcomes = run_per_item_loop(["A1", "A2"], cfg, process_one, stop_on_error=True)  
  
Testing Handoff Checklist  
-------------------------  
- [ ] Unit: injects id_var/index_var/total_var into cfg with correct values.  
- [ ] Unit: preserves and restores prior cfg values for injected keys after each item.  
- [ ] Unit: stop_on_error=True re-raises exception and stops further processing.  
- [ ] Unit: stop_on_error=False continues, returns outcomes with captured exceptions.  
- [ ] Unit: callbacks on_item_start/on_item_success/on_item_error invoked as expected.  
- [ ] Integration: works with a Selenium step-runner that reads cfg["CURRENT_ID"].
```

## NAV\nav_1a_selenium_helpers.py

**Module ID:** NAV-1A

```
NAV-1A — Selenium navigation and interaction helpers (pure helpers, no logging)
 
Purpose
-------
Provide small, reusable Selenium helper functions that encapsulate explicit-wait
patterns (WebDriverWait + expected_conditions) for common UI interactions in a
headless-safe way.
 
These helpers are intentionally:
- selector-based (no coordinate clicking)
- explicit-wait driven (no sleeps)  [NOTE: except wait_for_download, which must poll filesystem]
- pure utilities (no logging, no cfg coupling)
 
Inputs / Outputs
----------------
All helpers accept:
- driver: selenium WebDriver
- by: selenium.webdriver.common.by.By OR a string alias ("css", "xpath", "id", "name", ...)
- locator: selector string
 
Return values:
- wait_for_visible / wait_for_clickable -> WebElement
- click / type_text / switch_to_frame -> WebElement (or frame element for switch)
- switch_to_default_content -> None
- wait_for_download -> Path of detected stable downloaded file
 
Failure modes
-------------
- Timeout waiting for an element: raises TimeoutError with locator context.
- Click intercepted/stale: click() retries once on staleness and may fallback to JS click.
- Download wait timeout: raises TimeoutError with directory context.
 
Minimal usage example
---------------------
from ENTRY.entry_1a_webdriver_bootstrap import make_driver
from selenium.webdriver.common.by import By
from NAV.nav_1a_selenium_helpers import wait_for_visible, click
 
cfg = {"HEADLESS": "true"}
driver = make_driver(cfg)
try:
    driver.get("https://example.com")
    h1 = wait_for_visible(driver, By.CSS_SELECTOR, "h1", timeout=10)
    click(driver, "css", "a", timeout=10)
finally:
    driver.quit()
```

## OBS\obs_1a_run_timeline.py

**Module ID:** OBS-1A

```
OBS-1A — Run Observability Timeline  
  
Provides a structured execution timeline for workflow runs that can be consumed by humans,  
logs, or AI agents.  
  
Public API:  
- create_run_timeline(run_id: str, workflow_name: str) -> dict  
- record_step_event(timeline: dict, step_index: int, action: str, status: str, *,  
    selector: str|None=None, url: str|None=None, duration_ms: int|None=None, metadata: dict|None=None) -> None  
- finalize_timeline(timeline: dict) -> dict
```

## OUT\out_1a_download_wait.py

**Module ID:** OUT-1A

```
OUT-1A — Download wait/poll + directory management.  
  
Purpose  
-------  
Provide directory management and a polling-based "wait for download" helper.  
  
This module complements VAL-1B:  
- VAL-1B validates current state (exists, size threshold, name filtering)  
- OUT-1A waits/polls until validation succeeds and (optionally) the file stabilizes  
  
Public API  
----------  
ensure_download_dir(download_dir=None, cfg=None, create=True) -> str  
  
wait_for_download(  
    *,  
    download_dir=None,  
    file_path=None,  
    glob=None,  
    name_contains=None,  
    timeout_sec=60.0,  
    poll_sec=0.5,  
    min_size_bytes=1,  
    stable_sec=1.0,  
    clear_before=False,  
    cfg=None,  
) -> dict  
  
Config (env-friendly)  
---------------------  
DOWNLOAD_DIR  
DOWNLOAD_PATH  
DOWNLOAD_GLOB  
DOWNLOAD_NAME_CONTAINS  
TIMEOUT_SEC  
POLL_SEC  
MIN_SIZE_BYTES  
STABLE_SEC  
CLEAR_BEFORE  
  
Return contract  
---------------  
{  
  "ok": bool,  
  "path": str | None,  
  "size_bytes": int | None,  
  "elapsed_sec": float,  
  "matches": list[str],  
  "error": str | None  
}
```

## OUT\out_1b_artifact_manager.py

**Module ID:** OUT-1B

```
OUT-1B — Artifact Normalization (rename/move/archive, collision-safe).  
  
Filesystem-only helpers to normalize detected downloads (OUT-1A) into a predictable  
structure with stable names, per-run/per-item metadata, collision-safe policies,  
and optional archiving of prior outputs.  
  
Windows-safe, deterministic naming:  
- safe_slug() only uses [a-z0-9._-] and collapses runs.  
- build_artifact_name() composes base/run_id/item_id + extension.  
- move_artifact() handles overwrite policy, collision suffixing, and optional archive.
```

## PIPE\pipe_1a_run_orchestrator.py

**Module ID:** PIPE-1A

```
PIPE-1A — End-to-end per-run orchestrator (glue module)  
  
Purpose  
-------  
Run an end-to-end Selenium workflow by composing the already-validated modules:  
  
- INPUT-1B: read worklist IDs (source defined by cfg)  
- LOG-1A: initialize structured logging; bind run context (RUN_ID)  
- ENTRY-1A: create Selenium WebDriver  
- LOOP-1B: per-item iteration; inject CURRENT_ID / ITEM_INDEX / TOTAL_ITEMS into cfg  
- ACT-1B: execute steps with automatic step_start/step_success/step_error logs  
- STATE-1B: append per-item outcome to manifest (success/fail + error summary)  
- Always quit the WebDriver  
  
Inputs  
------  
- cfg: MutableMapping[str, Any]  
- steps: list[dict] (already loaded by the caller; e.g., from steps.json)  
  
Outputs  
-------  
Returns a simple summary dict:  
{  
  "run_id": str,  
  "total_items": int,  
  "success": int,  
  "failed": int,  
  "items": [{"item_id": str, "ok": bool, "error": str|None}],  
}  
  
Notes  
-----  
- STOP/CONTINUE behavior for step execution is controlled by cfg["STOP_ON_ERROR"]  
  via ACT-1B (default True). PIPE-1A continues to the next item even if one item  
  fails (it records the failure), unless a non-recoverable exception occurs.  
  
Minimal usage example  
---------------------  
from PIPE.pipe_1a_run_orchestrator import run_worklist  
cfg = {...}  # includes INPUT-1B config and LOG-1A/ENTRY-1A config  
steps = [{"action":"get","url":"https://example.com"}]  
summary = run_worklist(cfg, steps)  
print(summary)
```

## PIPE\pipe_1a_workflow_grammar_gate_pipeline.py

**Module ID:** PIPE-1A

```
PIPE-1A: Workflow grammar gate pipeline runner.  
  
Single responsibility:  
- Provide a CI/pipeline-friendly programmatic runner to:  
  - check workflows (no writes) and return an exit_code based on violations  
  - fix workflows (sanitize) with optional in-place or output-dir writes  
  - optionally write a deterministic JSON report  
  
Builds on:  
- DOCTOR-1A (check/fix orchestration + report dict)  
- REPORT-1A JSON text dumping
```

## PIPE\pipe_1b_worklist_config.py

**Module ID:** PIPE-1B

```
PIPE-1B — Worklist configuration adapter  
=======================================  
  
Purpose  
-------  
Provide a stable adapter between PIPE orchestrators and INPUT providers by:  
- Normalizing worklist configuration from `cfg`  
- Accepting multiple aliases for Excel sheet and ID column  
- Loading a list of work item IDs via INPUT-1B (Excel provider) using introspection  
  
Public API  
----------  
resolve_worklist_spec(cfg) -> {"path": str, "sheet": str, "id_column": str}  
load_ids(cfg) -> list[str]
```

## PIPE\pipe_1c_steps_loader.py

**Module ID:** PIPE-1C

```
PIPE-1C — Steps loader + template substitution (stdlib-only)  
  
Public API  
----------  
load_steps_file(path: str) -> list[dict]  
    Reads a JSON file containing either:  
      - a list of step dicts, OR  
      - an object like {"steps": [ ... ]}  
    Validates it returns list[dict]; raises ValueError with actionable messages.  
  
render_steps(steps: list[dict], cfg: MutableMapping[str, Any]) -> list[dict]  
    Deep-walk list/dict structures and substitutes ${VAR} placeholders in string  
    values using cfg. Missing vars are left unchanged. Does not mutate input.  
  
load_steps_from_cfg(cfg: MutableMapping[str, Any]) -> list[dict]  
    Looks for one of these config keys (priority):  
      1) STEPS_PATH  
      2) STEPS_JSON_PATH  
      3) STEPS_FILE  
    Loads and renders steps. If no path provided, raises ValueError listing keys.  
  
Auto behavior (Phase A + Auto-1)  
-------------------------------  
1) Worklist auto-provisioning:  
   Some orchestration paths load worklist IDs directly via INPUT-1B which requires  
   cfg['WORKLIST_XLSX'] (or INPUT_XLSX). If the caller does not provide a worklist  
   path, load_steps_from_cfg() will generate a tiny temporary .xlsx worklist  
   (stdlib-only OpenXML packaging) and populate the required cfg keys.  
  
2) Minimal step schema normalization (compat):  
   ACT-1A 'wait_for_element' expects step['selector'].  
   If steps provide {'by': ..., 'value': ...} and omit 'selector', we synthesize it.
```

## PIPE\pipe_1d_step_executor.py

**Module ID:** PIPE-1D

```
PIPE-1D — Step Execution Adapter  
  
Goal  
----  
Normalize step dictionaries from PIPE-1C and safely route them to the ACT engine.  
  
Public API  
----------  
execute_step(driver, step: dict, cfg: dict) -> dict  
    Returns:  
        {  
            "ok": bool,  
            "result": Any,  
            "error": str | None  
        }  
  
Notes  
-----  
- Does not duplicate ACT logic; delegates execution to ACT.act_1a_action_engine.run_actions  
  for supported actions.  
- Performs minimal normalization for common step shapes (e.g., by/value -> selector).
```

## PIPE\pipe_1e_runner.py

**Module ID:** PIPE-1E

```
PIPE-1E — Single runnable pipeline entrypoint.  
  
This module orchestrates an end-to-end run by *composing existing modules*:  
- Steps: PIPE-1C (load/render/normalize)  
- Worklist/driver/loop/actions/logging/state: delegated to PIPE-1A orchestrator  
  (which uses PIPE/INPUT/LOOP/ACT/NAV/STATE/LOG layers)  
  
Exit codes  
----------  
- 0: all items succeeded  
- 2: completed run with one or more item failures  
- 1: fatal error (exception / could not run)  
  
Env-friendly cfg keys supported  
-------------------------------  
WORKLIST_PATH / WORKLIST_XLSX, WORKLIST_SHEET, WORKLIST_ID_COLUMN,  
STEPS_PATH or STEPS (inline),  
MANIFEST_PATH, LOG_PATH,  
STOP_ON_ERROR, HEADLESS, BROWSER, EXPLICIT_WAIT.
```

## PIPE\pipe_1f_env_overrides.py

**Module ID:** PIPE-1F

```
PIPE-1F: Environment overrides applied to cfg.  
  
Purpose  
-------  
Ensure env vars (notably DRY_RUN) can deterministically override any cfg defaults  
coming from higher layers (CLI/RUN/etc).  
  
Design  
------  
- Additive: does not change behavior unless corresponding env var is present.  
- Writes both canonical + alias keys (e.g., DRY_RUN and dry_run) for compatibility.
```

## PIPE\pipe_1g_env_force_overrides.py

**Module ID:** PIPE-1G

```
PIPE-1G — Environment Force Overrides

Purpose
-------
Apply environment-variable overrides to runtime
configuration, ensuring deployment environments
can supersede CLI defaults and static configuration.

Public API
----------
apply_env_force_overrides(...)

Dependencies
------------
None

Status
------
Draft

Notes
-----
Override Priority:

Default Config
        ↓
CLI Arguments
        ↓
Environment Variables
        ↓
Runtime Configuration

Supported Overrides:

- LOG_PATH
- LOG_JSONL_PATH
- MANIFEST_PATH
- STATE_MANIFEST_PATH
- STOP_ON_ERROR
- FAIL_FAST
- BROWSER

Used by deployment, CI/CD, containerized execution,
and environment-specific runtime configuration.
```

## PIPE\pipe_1h_log_jsonl_path_policy.py

**Module ID:** PIPE-1H

```
PIPE-1H — JSONL Log Path Policy

Purpose
-------
Resolve runtime JSONL logging destinations using
a deterministic precedence model and manage
temporary log file lifecycle.

Public API
----------
select_log_jsonl_path(...)
maybe_cleanup_log_jsonl_path(...)

Dependencies
------------
None

Status
------
Draft

Notes
-----
Path Resolution Priority:

LOG_JSONL_PATH (env)
        ↓
LOG_PATH (env)
        ↓
LOG_JSONL_PATH (cfg)
        ↓
LOG_PATH (cfg)
        ↓
Temporary File

Temporary files created by the framework may be
cleaned up automatically.

User-provided log files are never automatically
deleted.
```

## PIPE\pipe_2a_var_aware_steps.py

**Module ID:** PIPE-2A

```
PIPE-2A — Variable-aware Step Execution (VAR-1A integration).  
  
Goal  
----  
Ensure ${VAR} substitution works end-to-end inside rendered steps at execution time:  
- URLs  
- selectors  
- expected text  
- JS script snippets (string substitution only)  
- output paths (manifest/log/download dirs) via optional cfg-key rendering  
  
This module is an additive, thin adapter:  
- imports and uses VAR-1A (does not duplicate it)  
- does not redefine ACT/VAL/NAV modules  
- renders every step (deep) prior to execution  
  
Public API  
----------  
render_step(step, cfg, *, step_index=None) -> Any  
render_cfg_inplace(cfg, *, keys=None) -> dict  
execute_step_var_aware(driver, step, cfg, *, step_index, executor=None) -> Any  
execute_steps_var_aware(driver, steps, cfg, *, executor=None, render_cfg_keys=None) -> list  
  
Missing-variable errors  
-----------------------  
If a variable is missing during rendering, raises a ValueError with:  
- step index  
- action  
- missing var name
```

## PIPE\pipe_2b_step_blocks.py

**Module ID:** PIPE-2B

```
PIPE-2B — Step Blocks & Branching (if/else + try blocks).  
  
Adds support for block steps expressed in steps.json without new Python code:  
- action: "if"  
- action: "group"  
- action: "try"  
  
Key requirements:  
- Uses VAR-1A rendering (via PIPE-2A render/execute adapter).  
- Uses ACT-1C conditional guard helpers for if conditions.  
- Leaf steps are executed through existing leaf-step executor via PIPE-2A wrapper.  
- Headless-safe, deterministic.  
- Must not mutate the original steps list.  
  
Public API  
----------  
run_steps(driver, steps: list[dict], cfg: dict) -> list[dict]
```

## PIPE\pipe_2c_error_plumbing.py

**Module ID:** PIPE-2C

```
PIPE-2C — Error Plumbing Integration (LOG-1B + LOG-1A + STATE).  
  
Additive wrapper to ensure any step/item failure produces:  
- normalized error dict (LOG-1B.classify_exception)  
- structured log event (LOG-1A, best-effort resolved emitter)  
- manifest row update (STATE writer, if provided)  
  
No changes required to existing modules for this milestone.
```

## PIPE\pipe_2d_artifact_integration.py

**Module ID:** PIPE-2D

```
PIPE-2D — Artifact + Manifest Integration.  
  
Automatically normalize and record downloaded artifacts during pipeline execution.  
  
Must use:  
- OUT-1A (best-effort validation hook if available; consumes its output Path)  
- OUT-1B (normalize_download)  
- STATE-1D (row_success/row_failure + write_row)  
- LOG-1A (structured event emission, best-effort resolved)  
  
No refactors required; additive helper only.
```

## PIPE\pipe_2e_run_summary.py

**Module ID:** PIPE-2E

```
PIPE-2E — Run Summary + Metrics.  
  
Standardized, additive run summary object to describe an automation run.  
No integration into existing runners yet; this module is meant to be attached later.  
  
Summary shape  
-------------  
{  
  "run_id": "...",  
  "start_time": "...",  
  "items_total": 0,  
  "items_success": 0,  
  "items_failed": 0,  
  "artifacts": [],  
  "errors": []  
}  
  
finish_run_summary adds:  
- end_time  
- duration_seconds
```

## PLAN\plan_1a_step_planner.py

**Module ID:** PLAN-1A

```
PLAN-1A — Workflow Step Planner / Skeleton Generator  
  
Generates a valid steps.json skeleton from a high-level workflow intent using  
SCHEMA-1A outputs as the single source of truth.  
  
Outputs:  
- workflows/generated_steps.json  
- workflows/generated_plan.md  
  
Constraints:  
- Do NOT import/execute project modules with side effects.  
- Only use actions present in SCHEMA/steps_schema.json.  
- Prefer templates from SCHEMA/steps_examples.json when available.
```

## REASON\reason_1a_diagnose.py

**Module ID:** REASON-1A

```
REASON-1A — Failure Diagnosis Engine (agent-friendly)  
  
Pure, deterministic, rule-based diagnosis helper.  
- No logging  
- No Selenium calls  
- No filesystem writes  
- No imports from project modules with side effects  
  
Public API:  
  diagnose_failure(...)
```

## REGISTRY\reg_12a_versioning_policy.py

**Module ID:** REG-12A

```
REG-12A: Versioning Policy (Milestone 12.2.1)  
  
Single responsibility:  
- Define a deterministic, reviewable versioning policy for:  
  - workflows  
  - selectors  
  - framework  
- Provide SemVer parsing/validation and optional release checks.  
- Provide deterministic renderers (Markdown/JSON) to support governance docs.  
  
This module does not modify any existing build/release pipeline behavior. It is a  
policy definition that can be invoked by CI/build tooling later.
```

## REGISTRY\reg_12b_promotion_gates.py

**Module ID:** REG-12B

```
REG-12B: Promotion Gates Policy (Milestone 12.2.3)  
  
Single responsibility:  
- Define deterministic promotion gates between environments (e.g., dev->stage->prod).  
- Provide a pure evaluator to decide if a promotion is allowed based on evidence.  
- Provide deterministic renderers (Markdown/JSON) for governance documentation.  
  
This module is policy-only: it does not execute CI, run workflows, or integrate with  
ticketing systems. It is intended to be called by BUILD/CLI/CI later.
```

## REGISTRY\registry_1a_generate.py

**Module ID:** REGISTRY-1A

```
REGISTRY-1A — Action/Step Registry Export (AI Capability Handshake)  
  
Authoritative registry mapping step actions to:  
- schema definition (required/optional fields)  
- implementation location (module path + option ID)  
- handler function name (if discoverable via static parsing)  
- available smoke tests  
  
Inputs (preferred):  
- DOC/library_index.json  
- SCHEMA/steps_schema.json  
- SCHEMA/steps_examples.json  
  
Outputs:  
- REGISTRY/action_registry.json  
- REGISTRY/action_registry.md  
  
Rules:  
- Do NOT execute project modules (no imports with side effects).  
- Prefer static parsing (ast) and existing generated artifacts.  
- Do not duplicate SCHEMA; reference it.  
- Output must be deterministic.
```

## REPLAY\replay_12a_index_verifier.py

**Module ID:** REPLAY-12A

```
REPLAY-12A: Replay Index Verifier (Milestone 12.5.4)  
  
Single responsibility:  
- Parse audit-log JSONL into events (dicts).  
- Verify (deterministically) that canonical event hashes match a ReplayIndex.  
  
This module does NOT execute a browser replay. It only verifies integrity/consistency  
of replay artifacts for audit and reproducibility.  
  
Dependencies:  
- Uses HISTORY.history_12a_audit_logging_replay_spec for canonicalization and hashing.  
  
Determinism:  
- No timestamps generated.  
- Stable event ordering and stable mismatch ordering.  
- JSON uses sort_keys=True.
```

## REPLAY\replay_1a_run_replay.py

**Module ID:** REPLAY-1A

```
REPLAY-1A — Deterministic Run Replayer  
  
Replays (or plans) a previous workflow run using SNAP-1A artifacts.  
  
Public API:  
  replay_run(run_id: str, *, artifacts_dir="artifacts", override_cfg=None, dry_run=False) -> dict
```

## REPORT\report_12a_release_manifest.py

**Module ID:** REPORT-12A

```
REPORT-12A: Release Manifest (Milestone 12.3.1)  
  
Single responsibility:  
- Build a deterministic release manifest describing a workflow release bundle:  
  - component versions  
  - artifact file hashes (sha256) and sizes  
- Provide deterministic renderers (Markdown/JSON) for auditability.  
  
Design constraints:  
- No timestamps are generated in this module (determinism). If a timestamp is  
  required, the caller should add it externally.
```

## REPORT\report_12b_bundle_fingerprint.py

**Module ID:** REPORT-12B

```
REPORT-12B: Bundle Fingerprint (Milestone 12.3.2)  
  
Single responsibility:  
- Compute a deterministic bundle fingerprint from a ReleaseManifest.  
- Render fingerprint records as Markdown/JSON for auditability.  
  
Design:  
- Fingerprint intentionally ignores artifact paths to remain stable across machines/dirs.  
- Inputs are component_id + version + artifact sha256 + artifact size_bytes (if present).  
- Output is sha256 hex of a canonical, line-based input string.
```

## REPORT\report_12c_promotion_record.py

**Module ID:** REPORT-12C

```
REPORT-12C: Promotion Record (Milestone 12.3.3)  
  
Single responsibility:  
- Create a deterministic promotion record that can be stored with release artifacts:  
  - from_env -> to_env  
  - promotion decision (allowed/failed/missing)  
  - release manifest (versions + artifact hashes)  
  - bundle fingerprint (immutable identity)  
  - evidence used for gating (optionally redacted)  
  
Determinism:  
- No timestamps generated in this module.  
- Evidence is normalized into JSON-safe, stable structures.
```

## REPORT\report_12d_artifact_retention_policy.py

**Module ID:** REPORT-12D

```
REPORT-12D: Artifact Retention Policy (Milestone 12.5.1)  
  
Single responsibility:  
- Define a canonical, deterministic artifact retention policy for production readiness.  
- Provide a pure evaluator that, given:  
    - env (e.g., "prod")  
    - artifacts metadata (kind, created_date, tags)  
    - now_date (caller supplied)  
  produces a deterministic keep/delete plan.  
- Provide deterministic Markdown/JSON renderers.  
  
Determinism:  
- No timestamps are generated.  
- Dates are handled as ISO strings (YYYY-MM-DD) and parsed deterministically.  
- Output ordering is stable.  
  
This module does NOT delete files. It only produces a plan.
```

## REPORT\report_12e_alerting_signals.py

**Module ID:** REPORT-12E

```
REPORT-12E: Alerting Signals From Run Outcomes (Milestone 12.5.2)  
  
Single responsibility:  
- Define a canonical, deterministic alerting policy (signal thresholds).  
- Provide a pure evaluator that turns run outcome metrics into triggered alerts.  
- Provide deterministic Markdown/JSON renderers.  
  
Determinism:  
- No timestamps generated.  
- Stable ordering of signals and triggered alerts.  
- JSON rendering uses sort_keys=True.  
  
This module does NOT send alerts. It only evaluates signals and returns an alert plan.
```

## REPORT\report_12f_incident_packet_manifest.py

**Module ID:** REPORT-12F

```
REPORT-12F: Incident Packet Manifest (Milestone 12.5.5)  
  
Single responsibility:  
- Define a canonical, deterministic "incident packet" manifest structure.  
- Provide pure validators.  
- Provide deterministic JSON/Markdown renderers.  
- Provide deterministic SHA256 fingerprinting over canonical JSON.  
  
Determinism:  
- No timestamps generated.  
- Stable ordering of artifacts (by kind, label, path).  
- JSON uses sort_keys=True and stable separators for canonical hashing.  
  
This module does NOT collect artifacts. It only describes them.
```

## REPORT\report_12g_evidence_bundle_assembler.py

**Module ID:** UNKNOWN

```
report_12g_evidence_bundle_assembler.py  
  
Milestone 12.5.7 — Evidence bundle assembler  
  
Deterministically assembles a single "evidence bundle" object from caller-supplied  
inputs (dicts/strings) that typically come from prior 12.5.x modules:  
- Alerting signals outputs (12.5.2)  
- Audit logging + replay spec/index (12.5.3)  
- Replay index verification result (12.5.4)  
- Incident packet manifest (12.5.5)  
- Release readiness gate policy/decision (12.5.6)  
  
Design goals:  
- Pure functions wherever practical.  
- Deterministic JSON and Markdown renderers.  
- Stable fingerprinting (sha256 over canonical JSON without timestamps).  
- Optional artifact inventory hashing for provided artifact *text* (sha256/size).
```

## REPORT\report_1a_generate.py

**Module ID:** REPORT-1A

```
REPORT-1A — Run Report Generator (HTML + JSON + MD)  
  
Adds:  
- report.json top-level: agent_next_actions (structured extraction only)  
  Derived from:  
    - REASON diagnosis["fixes"] (if present)  
    - HEAL patch presence (if patch present -> review; if missing but diagnosis present -> run HEAL)  
  
No Selenium required.
```

## REPORT\report_1a_run_report.py

**Module ID:** REPORT-1A

```
REPORT-1A — Run report aggregation (10.3.1)  
  
Single responsibility:  
- Read history artifacts (run manifest + step outcomes) and produce a deterministic  
  run report JSON under the run output directory.  
  
Inputs read (if present):  
- {run_output_dir}/history/run_manifest.json  
- {run_output_dir}/history/step_outcomes.jsonl  
  
Output written:  
- {run_output_dir}/report/run_report.json
```

## REPORT\report_1a_step_logs_from_jsonl.py

**Module ID:** REPORT-1A

```
REPORT-1A — Build step_logs from LOG JSONL events.  
  
Goal  
----  
Derive per-step statuses from the JSONL event stream:  
- step_success => status="success"  
- step_error   => status="failure" + error message  
  
Key rule (fixes the behavior you are seeing)  
--------------------------------------------  
If a step already has status "success", later "step_error" events for the same step_index  
are ignored (prevents item-level "step_error" noise from overwriting real success).  
  
This module is additive and does not require changes to ACT/PIPE internals to be useful.
```

## REPORT\report_1a_workflow_grammar_gate_report.py

**Module ID:** REPORT-1A

```
REPORT-1A: Workflow grammar gate reporting.  
  
Single responsibility:  
- Convert BUILD-2G WorkflowTreeGateResult (and its per-file results) into a  
  deterministic, JSON-serializable report dict + JSON text.  
  
This is additive and does not modify any BUILD modules.
```

## REPORT\report_1b_run_report_markdown.py

**Module ID:** REPORT-1B

```
REPORT-1B — Run report markdown renderer (10.3.2)  
  
Single responsibility:  
- Convert a REPORT-1A run report dict into deterministic Markdown text and write it to:  
  {run_output_dir}/report/run_report.md
```

## REPORT\report_1b_workflow_grammar_gate_report_text.py

**Module ID:** REPORT-1B

```
REPORT-1B: Deterministic text rendering for workflow grammar gate reports.  
  
Single responsibility:  
- Convert the REPORT-1A grammar gate report dict into a stable, human-readable text summary.  
- No I/O; formatting only.
```

## REPORT\report_1c_junit_xml.py

**Module ID:** REPORT-1C

```
REPORT-1C — JUnit XML renderer (10.3.3)  
  
Single responsibility:  
- Convert a REPORT-1A run report dict into deterministic JUnit XML and write it to:  
  {run_output_dir}/report/junit.xml  
  
Notes:  
- Attribute ordering in XML serializers can vary; we generate XML as a string with a fixed layout.  
- This is intended for CI consumption (tests = steps, failures = error steps).
```

## REPORT\report_1c_workflow_grammar_gate_report_summary.py

**Module ID:** REPORT-1C

```
REPORT-1C: Workflow grammar gate report summary.  
  
Single responsibility:  
- Provide a small, deterministic summary extractor + compact one-line formatter  
  for workflow grammar gate report dicts.  
  
This is intentionally tolerant of minor schema variations and uses best-effort  
fallbacks when summary fields are absent.
```

## REPORT\report_1d_generate_reports.py

**Module ID:** REPORT-1D

```
REPORT-1D — Generate standard report artifacts (10.4.1)  
  
Single responsibility:  
- Given a run_output_dir, generate the standard set of report artifacts by composing:  
  - REPORT-1A (JSON aggregation)  
  - REPORT-1B (Markdown)  
  - REPORT-1C (JUnit XML)  
  
Outputs:  
- {run_output_dir}/report/run_report.json  
- {run_output_dir}/report/run_report.md  
- {run_output_dir}/report/junit.xml
```

## RUN\run_12a_prod_smoke_pipeline.py

**Module ID:** UNKNOWN

```
run_12a_prod_smoke_pipeline.py  
  
Milestone 12.6.1 — Production readiness smoke: deploy-to-run-to-report pipeline (CI-safe)  
  
This module provides a deterministic harness that:  
- Constructs a minimal workflow + selectors bundle using only supported actions.  
- Validates that only allowed actions are used (including nested repeat steps).  
- Assembles an evidence bundle using REPORT/report_12g_evidence_bundle_assembler.py  
- Produces a deterministic "prod smoke pipeline report" artifact with JSON/Markdown renderers  
  and a stable SHA256 fingerprint over canonical JSON.  
  
No Selenium execution, no timestamps generated. Caller may provide created_date if desired.
```

## RUN\run_12b_rollback_rerun_determinism.py

**Module ID:** UNKNOWN

```
run_12b_rollback_rerun_determinism.py  
  
Milestone 12.6.2 — Production readiness smoke: rollback and re-run determinism (CI-safe)  
  
Deterministically simulates:  
  deploy(A) -> run(A1) -> deploy(B) -> run(B1) -> rollback(to A) -> run(A2)  
  
And produces a single report artifact proving:  
- A1 and A2 have identical deterministic "result signatures" given identical deployment inputs.  
- B1 differs from A1 when deployment inputs differ.  
  
Important note:  
Run records contain run identity (run_id) and evidence bundle ids; therefore  
A1 and A2 full canonical JSON will differ. Determinism is validated via a  
separate run_result_signature_sha256 that excludes run identity.
```

## RUN\run_12c_operational_gates_enforcement.py

**Module ID:** UNKNOWN

```
run_12c_operational_gates_enforcement.py  
  
Milestone 12.6.3 — Production readiness smoke: operational gates enforcement (CI-safe)  
  
Goal:  
- Exercise operational gates modules that should already exist from prior milestones:  
  - DOCTOR/doctor_12a_pre_run_checks.py  
  - GUARD/guard_12a_prod_defaults.py  
  - DOCTOR/doctor_12d_release_readiness_gate.py  
  
Harness behavior:  
- Deterministic discovery of evaluator callable  
- Deterministic discovery of policy (instance, dataclass class instantiated via cls(), or no-arg factory)  
- Signature-based calling: only pass supported kwargs  
- If evaluator requires a policy and none is discoverable, provide a deterministic fallback shim policy  
  that supplies commonly dereferenced attributes.  
  
Important compatibility behavior:  
- Different gate evaluators expect different *shapes* for "observations".  
  - pre-run checks commonly expect bools (e.g., {"check_a": True})  
  - release-readiness gate (doctor_12d) expects observation objects with `.passed` (and `.data`)  
- This harness keeps bool observations for general gates, but *adapts* the context for the  
  release-readiness module so that its "observations" parameter receives observation objects.  
  
Stability behavior:  
- Some gate modules may return non-boolean results or always-true results for simplified contexts.  
- To keep the 12.6.3 dev_smoke deterministic, if all interpretable gates have identical outcomes  
  (or none are interpretable), we append a deterministic synthetic gate that checks selector_ref  
  resolution (good passes; bad fails). This does not replace module gates; it only ensures the  
  smoke invariant can be satisfied in CI.  
  
No Selenium execution. No timestamps generated (caller may pass created_date).
```

## RUN\run_1a_workflow_grammar_gate.py

**Module ID:** RUN-1A

```
RUN-1A: Pre-run workflow grammar gate.  
  
Single responsibility:  
- Provide a RUN-layer wrapper to assert/sanitize workflow step actions before execution,  
  using BUILD-2E/2F logic (no duplication).  
  
This module does not execute workflows; it only gates them for safe execution.
```

## RUN\run_1a_workflow_grammar_gate_run.py

**Module ID:** RUN-1A

```
RUN-1A: Workflow grammar gate run orchestration.  
  
Single responsibility:  
- Orchestrate a single workflow-grammar-gate run by calling:  
  - DOCTOR-1B (pipeline-backed diagnosis)  
  - GUARD-1A (policy evaluation; optional baseline)  
  - HISTORY-1A (optional JSONL append)  
  
No CLI parsing here; callers supply arguments explicitly.
```

## RUN\run_1a_workflow_runner.py

**Module ID:** RUN-1A

```
RUN-1A — Unified Workflow Runner  
  
Single entry point that executes workflows produced by WORKFLOW-1A using the existing  
PIPE orchestration system.  
  
Execution flow:  
1) Load workflow via WORKFLOW-1A loader  
2) Validate steps using LINT-1A  
3) Merge cfg defaults + overrides  
4) Initialize VAR store (seeded from workflow vars)  
5) Call PIPE orchestrator/runner (no duplicated logic)  
6) Return structured summary
```

## RUN\run_1b_workflow_runner_with_snap.py

**Module ID:** RUN-1B

```
RUN-1B — Workflow Runner With Snapshot Capture

Purpose
-------
Wrap the canonical RUN-1A workflow runner and automatically
capture SNAP-1A failure artifacts whenever execution fails.

This module is additive only and does not modify
RUN-1A execution behavior.

Public API
----------
run_workflow_with_snap(...)

Dependencies
------------
RUN-1A
SNAP-1A

Status
------
Draft

Notes
-----
On workflow failure:
RUN-1A
    ↓
Capture SNAP-1A artifacts
    ↓
Re-raise original exception

Used for diagnostics, replay, healing, and audit workflows.
```

## RUN\run_1c_workflow_runner_with_guard.py

**Module ID:** RUN-1C

```
RUN-1C — Wrapper to enable GUARD-1A without refactoring RUN-1A.  
  
This wrapper is best-effort:  
- Calls existing RUN-1A run_workflow  
- If cfg['GUARD_ENABLED'] true and a step_runner_fn is provided (or supported by RUN-1A),  
  wraps it using GUARD.wrap_step_runner  
  
If RUN-1A does not accept a step runner override, this wrapper will still run (guard may be inactive).
```

## RUN\run_1d_runner_with_history.py

**Module ID:** RUN-1D

```
RUN-1D — Wrapper to append HISTORY-1A records after running RUN-1A / REPORT-1A.  
  
- Additive only (no RUN-1A refactors)  
- Best-effort: if run fails (exception), still attempts to append a failure record.  
- If DIFF fingerprint (overall_hash) is provided or computable, include it.
```

## RUN\run_1e_deploy_bundle_runner_adapter.py

**Module ID:** RUN-1E

```
RUN-1E — Deploy Bundle Runner Adapter

Purpose
-------
Execute DEPLOY_BUNDLE_1A artifacts by loading,
validating, extracting runnable workflow assets,
and delegating execution to the configured runtime runner.

This module provides the bridge between the
deployment pipeline and workflow execution layer.

Public API
----------
run_deploy_bundle_1a(...)
run_deploy_bundle_1a_with_meta(...)
resolve_default_workflow_runner_callable(...)

Dependencies
------------
WORKFLOWS-1G
RUN-1A
RUN-1B
RUN-1C
RUN-1D

Status
------
Draft

Notes
-----
Execution Flow:

DEPLOY_BUNDLE_1A
        ↓
Load & Validate
        ↓
Extract Workflow
        ↓
Resolve Runner
        ↓
Execute Workflow

This module does not execute Selenium actions directly.
It delegates execution to the resolved runtime runner.
```

## RUN\run_1e_post_run_reporting.py

**Module ID:** RUN-1E

```
RUN-1E — Post-run reporting hook (10.4.2)  
  
Single responsibility:  
- Provide an additive, runner-friendly hook that can be called at the end of a run  
  to generate standard report artifacts.  
  
This module does NOT modify existing runners; it is intended to be composed by RUN  
modules (or CLI) in later milestones.  
  
Outputs (when enabled=True):  
- {run_output_dir}/report/run_report.json  
- {run_output_dir}/report/run_report.md  
- {run_output_dir}/report/junit.xml
```

## SCHEMA\schema_1a_generate.py

**Module ID:** SCHEMA-1A

```
SCHEMA-1A — Step/Action Schema Export (AI-friendly)  
  
Generates:  
- SCHEMA/steps_schema.json  
- SCHEMA/steps_examples.json  
- (compat/alias) SCHEMA/schema_1a_steps.json  
  
Constraints:  
- Do NOT import/execute project modules with side effects.  
- Prefer DOC/library_index.json if present; otherwise statically scan ACT/, PIPE/, VAL/, NAV/.  
- Use static parsing (ast) to infer:  
  - action names  
  - required/optional fields  
  - basic field types (heuristics)  
  - allowed values (heuristics)  
  - examples (from literal dict/list literals in source)
```

## SELECTOR\selector_1a_registry.py

**Module ID:** SELECTOR-1A

```
SELECTOR-1A — Selector Registry / Resolver  
  
Centralizes UI selectors so workflows can reference stable selector IDs instead of raw selectors.  
  
Loads selectors from: data/selectors.json  
  
Example structure:  
{  
  "login": {  
    "username_input": {"css": "#username", "xpath": "//input[@name='username']"},  
    "password_input": {"css": "#password"},  
    "submit_button": {"css": "button[type='submit']"}  
  }  
}  
  
Public API:  
- load_selectors(...)  
- get_selector(path, ...)  
- resolve_selector(step_dict, ...)  
  
Rules:  
- Pure / side-effect free: no implicit IO at import time.  
- No modifications to ACT/NAV modules.
```

## SNAP\snap_1a_capture.py

**Module ID:** SNAP-1A

```
SNAP-1A — Evidence Capture on Failure (artifacts bundle)  
  
Selenium-safe utility:  
- May accept a driver, but must not create a driver.  
- Resilient: never raises due to artifact capture failures.  
- Writes compact evidence bundle to artifacts/<run_id>/.  
  
Public API:  
  capture_failure_artifacts(...)
```

## SNAP\snap_1a_failure_capture.py

**Module ID:** SNAP-1A

```
SNAP-1A — Failure capture (10.1.1)  
  
Single responsibility:  
- Build a minimal, JSON-serializable snapshot payload containing:  
  - browser state (URL, title, DOM/page_source, optional readyState)  
  - step context (redacted / minimal)  
  - error summary (class + message)  
  - optional workflow/step index context  
  
This module does NOT persist artifacts (10.1.3) and does NOT take screenshots (10.1.2).
```

## SNAP\snap_1b_screenshot_capture.py

**Module ID:** SNAP-1B

```
SNAP-1B — Screenshot capture (10.1.2)  
  
Single responsibility:  
- Capture a screenshot from a selenium-like driver (best-effort).  
- Return either PNG bytes, base64 PNG, or a small JSON-serializable payload.  
  
This module does NOT persist artifacts to disk (10.1.3) and does NOT attempt  
to capture DOM/URL context (10.1.1).
```

## SNAP\snap_1c_persist_artifacts.py

**Module ID:** SNAP-1C

```
SNAP-1C — Persist snapshot artifacts deterministically (10.1.3)  
  
Single responsibility:  
- Given snapshot payload(s) (from SNAP-1A and optionally SNAP-1B), write artifacts  
  under a provided run output directory in a deterministic layout.  
  
This module does NOT:  
- capture DOM/URL (10.1.1)  
- capture screenshots (10.1.2)
```

## STATE\state_1b_manifest_jsonl.py

**Module ID:** STATE-1B

```
STATE-1B — JSONL manifest state (queued/success/fail + metadata) — stdlib-only  
  
(Existing docstring preserved; content omitted here for brevity.)
```

## STATE\state_1c_retry_helpers.py

**Module ID:** STATE-1C

```
STATE-1C — Retry / Resume helpers (additive to STATE-1B).  
  
Implements small helpers to:  
- read JSONL manifest rows robustly  
- extract de-duped failed IDs in stable order  
- write a minimal retry manifest (JSONL) containing only failed IDs in queued state  
  
This module does NOT modify or redefine STATE-1B behavior; it only reads/writes  
JSONL in a compatible, minimal shape.
```

## STATE\state_1d_manifest_row_helpers.py

**Module ID:** STATE-1D

```
STATE-1D — Manifest Row Helpers (standardize queued/success/fail shapes).  
  
Additive helpers to produce consistent manifest JSONL rows and write them through  
an existing STATE-1B writer instance.  
  
Constraints  
-----------  
- Does NOT duplicate STATE-1B open_manifest/append logic; accepts a writer.  
- Never include secrets in rows (best-effort redaction for common patterns).
```

## tools\generate_python_library_index.py

**Module ID:** REPO-INTEL-1A

```
MODULE: REPO-INTEL-1A
PURPOSE:
    Generate repository intelligence artifacts from module docstrings.

OUTPUTS:
    docs/repository/PYTHON_LIBRARY_INDEX.md
    docs/repository/python_library_index.json

RULES:
    - Read first module docstring only.
    - Do not inspect implementation code.
    - Report files missing headers.
    - Report duplicate module IDs.
```

## VAL\val_1a_ui_state.py

**Module ID:** VAL-1A

```
VAL-1A — UI state validation via selector presence + text checks.  
  
Purpose  
-------  
Reusable validation layer to decide success/failure based on DOM state:  
- element present / visible  
- text equals / contains  
- attribute equals / contains  
  
Public API  
----------  
validate_ui_state(driver, checks, cfg=None) -> dict  
  
`checks` can be:  
- a single dict  
- a list[dict]  
  
Each check supports:  
  - by: "css"|"xpath"|"id"|"name"  (default "css")  
  - value: selector string (required)  
  - expect: "present"|"visible" (default "present")  
  - text_equals: str  
  - text_contains: str  
  - attr: str (attribute name)  
  - attr_equals: str  
  - attr_contains: str  
  - timeout_sec: float (optional; default from cfg EXPLICIT_WAIT/EXPLICIT_WAIT_SEC/WAIT_EXPLICIT_SEC, else 10)  
  
Return contract  
---------------  
{  
  "ok": bool,  
  "passed": int,  
  "failed": int,  
  "details": [ { "ok": bool, "check": {...}, "observed": {...}, "error": str|None } ]  
}  
  
Note on text_contains robustness  
-------------------------------  
Some pages (or network appliances) can rewrite visible copy. To reduce brittleness  
for smoke tests and lightweight validations, `text_contains` uses:  
  1) strict substring match on normalized text  
  2) fallback "partial token match" requiring >= half of the significant tokens  
     (tokens length >= 4) from the expected string to appear in the observed text
```

## VAL\val_1b_download_validation.py

**Module ID:** VAL-1B

```
VAL-1B — Download validation (file exists, size > 0, optional name patterns).  
  
Purpose  
-------  
Validate that a download artifact is present and non-empty, optionally selecting it  
from a directory by glob/name filters.  
  
This module intentionally does NOT implement polling/waiting; it validates current state.  
  
Public API  
----------  
validate_download(  
    *,  
    file_path: str | None = None,  
    download_dir: str | None = None,  
    glob: str | None = None,  
    name_contains: str | None = None,  
    min_size_bytes: int = 1,  
    cfg: dict | None = None,  
) -> dict  
  
Config (env-friendly)  
---------------------  
DOWNLOAD_PATH (explicit file)  
DOWNLOAD_DIR  
DOWNLOAD_GLOB  
DOWNLOAD_NAME_CONTAINS  
MIN_SIZE_BYTES  
  
Return contract  
---------------  
{  
  "ok": bool,  
  "path": str | None,  
  "size_bytes": int | None,  
  "matches": list[str],  
  "error": str | None  
}
```

## VAL\val_2a_deploy_bundle_validator.py

**Module ID:** VAL-2A

```
VAL-2A — Deploy Bundle Validator

Purpose
-------
Perform deterministic validation of DEPLOY_BUNDLE_1A
artifacts before runtime execution.

Ensures workflow structure, selector references,
versioning metadata, and bundle integrity meet
platform requirements.

Public API
----------
validate_deploy_bundle_1a(...)
assert_deploy_bundle_1a(...)

Dependencies
------------
BUILD-3A
SNAP-1A

Status
------
Draft

Notes
-----
Validation Areas:

DEPLOY_BUNDLE_1A
        ↓
Schema Validation
        ↓
Workflow Validation
        ↓
Selector Validation
        ↓
Version/Fingerprint Validation
        ↓
Deterministic Report

Supports both report-based validation and
fail-fast exception-based validation.

This module is the primary quality gate
before workflow execution.
```

## VAR\var_1a_runtime_store.py

**Module ID:** VAR-1A

```
VAR-1A — Runtime Variable Store.  
  
Goal  
----  
Allow steps/modules to store and retrieve runtime variables during execution,  
without side effects outside the provided cfg mapping.  
  
Design  
------  
- Variables live under cfg["_vars"] (a dict).  
- get_var / set_var access that store.  
- render_vars recursively renders strings/dicts/lists/tuples.  
- String interpolation supports ${var_name} patterns anywhere in a string.  
  
Errors  
------  
- Missing variable in render_vars raises KeyError with a clear message.
```

## WORKFLOW\workflow_1e_steps_normalizer.py

**Module ID:** WORKFLOW-1E

```
WORKFLOW-1E — Workflow Steps Normalizer

Purpose
-------
Convert workflow definitions into a deterministic
canonical representation suitable for validation,
diffing, fingerprinting, bundling, and execution.

Public API
----------
normalize_workflow_steps(...)
normalize_workflow_dict(...)
normalize_capture_bundle_workflow(...)

Dependencies
------------
SNAP-1A

Status
------
Draft

Notes
-----
Normalization Responsibilities:

Workflow
        ↓
Remove None Fields
        ↓
Trim Strings
        ↓
Normalize Repeat Structures
        ↓
Coerce Repeat Counts
        ↓
Validate (Optional)
        ↓
Deterministic Key Ordering

Produces stable workflow representations for
review, fingerprint generation, validation,
and deployment packaging.
```

## WORKFLOW\workflow_1f_selector_ref_first.py

**Module ID:** WORKFLOW-1F

```
WORKFLOW-1F — Selector Reference First Enforcement

Purpose
-------
Convert workflows from raw-selector usage to
selector-reference usage using the selector pack
as the authoritative source of selector metadata.

Public API
----------
selector_pack_selector_to_ref(...)
enforce_selector_ref_first_in_steps(...)
enforce_selector_ref_first_in_workflow(...)
enforce_selector_ref_first_in_bundle(...)

Dependencies
------------
SELECTOR_PACK_1A

Status
------
Draft

Notes
-----
Selector Policy:

Raw Selector
        ↓
Selector Reference
        ↓
Selector Pack

Responsibilities:

- Convert selectors to selector_ref values
- Remove raw selectors when configured
- Validate selector consistency
- Recurse through repeat blocks
- Produce deterministic workflows

This module is a key prerequisite for
deploy bundles, healing, replay, and
portable workflow execution.
```

## WORKFLOWS\workflow_1a_loader.py

**Module ID:** WORKFLOW-1A

```
WORKFLOW-1A — Workflow file loader + validator + normalizer  
  
Loads a workflow definition from JSON or YAML (YAML optional if PyYAML is available),  
validates basic structure + known actions, and normalizes common aliases into a  
canonical (workflow, cfg_out, steps_out) shape.  
  
Reads existing generated artifacts (DO NOT re-derive):  
- REGISTRY/action_registry.json (preferred for action allowlist)  
- SCHEMA/steps_schema.json (required-fields validation; fallback allowlist)  
  
Rules:  
- Pure helper: no logging/printing.  
- Raise ValueError with actionable messages.  
- Deterministic output.
```

## WORKFLOWS\workflow_1g_deploy_bundle_loader.py

**Module ID:** WORKFLOW-1G

```
WORKFLOW-1G — Deploy Bundle Loader

Purpose
-------
Load, normalize, validate, and extract runnable
workflow assets from DEPLOY_BUNDLE_1A artifacts.

Provides a stable bridge between deployment
artifacts and runtime execution.

Public API
----------
load_deploy_bundle_1a(...)
load_deploy_bundle_1a_from_path(...)
extract_runnable_from_deploy_bundle_1a(...)

Dependencies
------------
BUILD-3A
BUILD-3F
VAL-2A

Status
------
Draft

Notes
-----
Responsibilities:

DEPLOY_BUNDLE_1A
        ↓
Load
        ↓
Normalize
        ↓
Validate
        ↓
Extract
        ↓
Return:
    workflow
    selector_pack
    run_meta

Supports legacy bundle compatibility by
automatically normalizing older fingerprint formats.
```

# Missing Module Headers

- .dev_tmp\build_2c_smoke\dev\dev_smoke_open_example_com_and_verify_page_title.py
- .dev_tmp\cli_2b_smoke\dev\dev_smoke_open_example_com_and_verify_page_title.py
- ACT\__init__.py
- AGENT\__init__.py
- AUTH\__init__.py
- BUILD\__init__.py
- BUILD\build_1a_workflow_generator.py
- BUILD\build_1b_intake_questionnaire.py
- BUILD\build_1c_action_normalizer.py
- BUILD\build_1c_smoke_stub_generator.py
- BUILD\build_3a_deploy_bundle_format.py
- BUILD\build_3b_bundle_fingerprint.py
- BUILD\build_3c_deploy_bundle_builder.py
- BUILD\build_3d_doc_index_artifact_bundler.py
- BUILD\build_3e_bundle_build_manifest_integrator.py
- BUILD\build_3f_deploy_bundle_stamper.py
- BUILD\build_3g_deploy_bundle_writer.py
- BUILD\build_3h_capture_to_deploy_bundle_pipeline.py
- CAPTURE\__init__.py
- CAPTURE\capture_1a_step_recorder.py
- CLI\__init__.py
- CLI\cli_1a_capture_to_deploy_bundle.py
- CLI\cli_1b_capture_to_deploy_bundle.py
- CLI\cli_1c_capture_to_deploy_bundle.py
- CLI\cli_1d_capture_to_deploy_bundle_auto.py
- CLI\cli_1e_deploy_bundle_info.py
- CLI\cli_1e_run_deploy_bundle.py
- CLI\cli_1f_run_deploy_bundle_with_report.py
- CLI\cli_1g_run_deploy_bundle_with_report_fail_fast.py
- CLI\cli_1h_run_deploy_bundle_cli_resolver.py
- CLI\cli_1i_build_doc_index_artifact.py
- CLI\cli_1i_bundle_doc_index_and_manifest_cli.py
- dev\dev_smoke_10_1_1_failure_capture.py
- dev\dev_smoke_10_1_2_screenshot_capture.py
- dev\dev_smoke_10_1_3_snapshot_persistence.py
- dev\dev_smoke_10_2_1_run_manifest.py
- dev\dev_smoke_10_2_2_step_outcomes.py
- dev\dev_smoke_10_2_3_error_normalization.py
- dev\dev_smoke_10_3_1_run_report.py
- dev\dev_smoke_10_3_2_run_report_markdown.py
- dev\dev_smoke_10_3_3_junit_xml.py
- dev\dev_smoke_10_4_1_generate_reports.py
- dev\dev_smoke_10_4_2_post_run_reporting.py
- dev\dev_smoke_10_4_3_cli_generate_reports.py
- dev\dev_smoke_12_1_1_slos_success_criteria.py
- dev\dev_smoke_12_1_2_operator_runbooks.py
- dev\dev_smoke_12_1_3_support_escalation_paths.py
- dev\dev_smoke_12_2_1_versioning_policy.py
- dev\dev_smoke_12_2_2_reviewable_diffs.py
- dev\dev_smoke_12_2_3_promotion_gates.py
- dev\dev_smoke_12_3_1_release_manifest.py
- dev\dev_smoke_12_3_2_bundle_fingerprint.py
- dev\dev_smoke_12_3_3_promotion_record.py
- dev\dev_smoke_12_4_1_doctor_pre_run_checks.py
- dev\dev_smoke_12_4_2_guard_prod_defaults.py
- dev\dev_smoke_12_4_3_rollback_recovery_procedures.py
- dev\dev_smoke_12_5_1_artifact_retention_policy.py
- dev\dev_smoke_12_5_2_alerting_signals.py
- dev\dev_smoke_12_5_3_audit_logging_replay_spec.py
- dev\dev_smoke_12_5_4_replay_index_verifier.py
- dev\dev_smoke_12_5_5_incident_packet_manifest.py
- dev\dev_smoke_12_5_6_release_readiness_gate.py
- dev\dev_smoke_12_5_7_evidence_bundle_assembler.py
- dev\dev_smoke_12_6_1_prod_smoke_pipeline.py
- dev\dev_smoke_12_6_2_rollback_rerun_determinism.py
- dev\dev_smoke_12_6_3_operational_gates_enforcement.py
- dev\dev_smoke_9_4_3_deterministic_generation.py
- dev\dev_smoke_9_4_3_run_history_loader.py
- dev\dev_smoke_agent_1a_context_pack.py
- dev\dev_smoke_agent_2a.py
- dev\dev_smoke_agent_2b.py
- dev\dev_smoke_build_1a.py
- dev\dev_smoke_build_1a_workflow_grammar_gate_entrypoints.py
- dev\dev_smoke_build_1b.py
- dev\dev_smoke_build_1c.py
- dev\dev_smoke_build_2a.py
- dev\dev_smoke_build_2b.py
- dev\dev_smoke_build_2c.py
- dev\dev_smoke_build_2d.py
- dev\dev_smoke_build_2e.py
- dev\dev_smoke_build_2f.py
- dev\dev_smoke_build_2g.py
- dev\dev_smoke_build_3a_deploy_bundle_format.py
- dev\dev_smoke_build_3b_bundle_fingerprint.py
- dev\dev_smoke_build_3c_deploy_bundle_builder.py
- dev\dev_smoke_build_3d_doc_index_artifact_bundler.py
- dev\dev_smoke_build_3e_bundle_build_manifest_integrator.py
- dev\dev_smoke_capture_1a.py
- dev\dev_smoke_cli_1a_workflow_grammar_gate.py
- dev\dev_smoke_cli_1e_run_deploy_bundle.py
- dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py
- dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py
- dev\dev_smoke_cli_1g_workflow_grammar_gate.py
- dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py
- dev\dev_smoke_cli_1h_workflow_grammar_gate_pipeline.py
- dev\dev_smoke_cli_1i_build_doc_index_artifact.py
- dev\dev_smoke_cli_1i_bundle_doc_index_and_manifest_cli.py
- dev\dev_smoke_cli_2b.py
- dev\dev_smoke_deploy_1a.py
- dev\dev_smoke_diff_1a.py
- dev\dev_smoke_diff_1a_capture_edit_diff.py
- dev\dev_smoke_diff_1a_workflow_grammar_gate_report_diff.py
- dev\dev_smoke_doc_1a_library_index.py
- dev\dev_smoke_doc_1a_workflow_grammar_gate.py
- dev\dev_smoke_doc_1e_cli_run_deploy_bundle_cli_resolver_entry.py
- dev\dev_smoke_doc_1f_doc_index_aggregator.py
- dev\dev_smoke_doc_1g_doc_index_entry_contract.py
- dev\dev_smoke_doc_1h_doc_index_collect_validate.py
- dev\dev_smoke_doc_doc_index_entry_cli_1i_bundle_doc_index_and_manifest_cli.py
- dev\dev_smoke_doctor_1a.py
- dev\dev_smoke_doctor_1a_workflow_grammar_gate.py
- dev\dev_smoke_doctor_1b_workflow_grammar_gate.py
- dev\dev_smoke_entry_1a_workflow_grammar_gate.py
- dev\dev_smoke_go_to_google_search_for_something_click_result_then_go_back_and_search_again.py
- dev\dev_smoke_go_to_google_search_for_weather_click_first_result.py
- dev\dev_smoke_guard_1a.py
- dev\dev_smoke_guard_1a_workflow_grammar_gate_guard.py
- dev\dev_smoke_guard_1a_workflow_grammar_guard.py
- dev\dev_smoke_heal_1a.py
- dev\dev_smoke_history_1a.py
- dev\dev_smoke_history_1a_workflow_grammar_gate_history.py
- dev\dev_smoke_learn_1a.py
- dev\dev_smoke_learn_1b.py
- dev\dev_smoke_lint_1a.py
- dev\dev_smoke_log_1a.py
- dev\dev_smoke_login_to_a_site_and_download_a_report.py
- dev\dev_smoke_login_to_portal_and_export_report.py
- dev\dev_smoke_obs_1a.py
- dev\dev_smoke_open_a_slow_website_and_click_something_immediately.py
- dev\dev_smoke_open_example_com_and_click_login_button_that_does_not_exist.py
- dev\dev_smoke_open_example_com_click_login_and_verify_page_title.py
- dev\dev_smoke_open_google_and_click_search.py
- dev\dev_smoke_pack_1a.py
- dev\dev_smoke_phase_11_5_1_capture_to_workflow_validity.py
- dev\dev_smoke_phase_11_5_2_bundle_packaging_determinism.py
- dev\dev_smoke_phase_11_5_3_deploy_run_path_minimal.py
- dev\dev_smoke_pipe_1a_workflow_grammar_gate_pipeline.py
- dev\dev_smoke_plan_1a.py
- dev\dev_smoke_reason_1a.py
- dev\dev_smoke_registry_1a.py
- dev\dev_smoke_replay_1a.py
- dev\dev_smoke_report_1a.py
- dev\dev_smoke_report_1a_workflow_grammar_gate_report.py
- dev\dev_smoke_report_1b_workflow_grammar_gate_report_text.py
- dev\dev_smoke_report_1c_workflow_grammar_gate_report_summary.py
- dev\dev_smoke_report_1e_build_manifest_artifact.py
- dev\dev_smoke_report_1e_deploy_bundle_validation_report_writer.py
- dev\dev_smoke_run_1a.py
- dev\dev_smoke_run_1a_workflow_grammar_gate.py
- dev\dev_smoke_run_1a_workflow_grammar_gate_run.py
- dev\dev_smoke_run_1e_deploy_bundle_runner_adapter.py
- dev\dev_smoke_schema_1a.py
- dev\dev_smoke_selector_1a.py
- dev\dev_smoke_snap_1a.py
- dev\dev_smoke_snap_1a_workflow_capture.py
- dev\dev_smoke_snap_1b_selector_pack.py
- dev\dev_smoke_snap_1c_capture_bundle.py
- dev\dev_smoke_snap_1d_bundle_io.py
- dev\dev_smoke_snap_1e_bundle_export.py
- dev\dev_smoke_snap_1f_materialize_selectors.py
- dev\dev_smoke_val_2a_deploy_bundle_validator.py
- dev\dev_smoke_workflow_1a_loader.py
- dev\dev_smoke_workflow_1e_steps_normalizer.py
- dev\dev_smoke_workflow_1f_selector_ref_first.py
- dev\dev_smoke_workflow_1g_deploy_bundle_loader.py
- dev\dev_smoke_workflow_workflow_2a_capture_actions_to_schema_steps.py
- dev\dev_smoke_workflow_workflow_2b_capture_js_event_recorder.py
- dev\dev_smoke_workflow_workflow_2c_capture_events_to_schema_steps_encoder.py
- DIFF\__init__.py
- DIFF\diff_1a_capture_edit_diff.py
- DOC\__init__.py
- DOC\doc_1e_cli_run_deploy_bundle_cli_resolver_entry.py
- DOC\doc_1f_doc_index_aggregator.py
- DOC\doc_index_entry_cli_1i_bundle_doc_index_and_manifest_cli.py
- DOCTOR\__init__.py
- ENTRY\__init__.py
- GUARD\__init__.py
- HEAL\__init__.py
- HISTORY\__init__.py
- INPUT\__init__.py
- LEARN\__init__.py
- LINT\__init__.py
- LINT\lint_steps.py
- LOG\__init__.py
- LOG\log_1b_logger_reset.py
- LOOP\__init__.py
- NAV\__init__.py
- OBS\__init__.py
- OUT\__init__.py
- PIPE\__init__.py
- PLAN\__init__.py
- REASON\__init__.py
- REGISTRY\__init__.py
- REPLAY\__init__.py
- REPORT\__init__.py
- REPORT\report_1e_build_manifest_artifact.py
- REPORT\report_1e_deploy_bundle_validation_report_writer.py
- RUN\__init__.py
- RUN\dev_run_workflow.py
- SCHEMA\__init__.py
- SELECTOR\__init__.py
- SNAP\__init__.py
- SNAP\snap_1a_workflow_capture.py
- SNAP\snap_1b_selector_pack.py
- SNAP\snap_1c_capture_bundle.py
- SNAP\snap_1d_bundle_io.py
- SNAP\snap_1e_bundle_export.py
- SNAP\snap_1f_materialize_selectors.py
- STATE\__init__.py
- VAL\__init__.py
- VAR\__init__.py
- WORKFLOW\workflow_2a_capture_actions_to_schema_steps.py
- WORKFLOW\workflow_2b_capture_js_event_recorder.py
- WORKFLOW\workflow_2c_capture_events_to_schema_steps_encoder.py
- WORKFLOWS\__init__.py

# Duplicate Module IDs

- BUILD-2A: BUILD\build_2a_repeat_support.py
- CLI-1A: CLI\cli_1a_workflow_grammar_gate.py
- ACT-1B: dev\dev_smoke_act_1b_logging.py
- ACT-1A: dev\dev_smoke_act_action_engine.py
- INPUT-1B: dev\dev_smoke_state_input.py
- DIFF-1A: DIFF\diff_1a_workflow_grammar_gate_report_diff.py
- DOC-1A: DOC\doc_1a_workflow_grammar_gate.py
- DOCTOR-1A: DOCTOR\doctor_1a_workflow_grammar_gate.py
- ENTRY-1A: ENTRY\entry_1a_webdriver_bootstrap.py
- ENTRY-1A: ENTRY\entry_1a_workflow_grammar_gate.py
- GUARD-1A: GUARD\guard_1a_workflow_grammar_gate_guard.py
- GUARD-1A: GUARD\guard_1a_workflow_grammar_guard.py
- HISTORY-1A: HISTORY\history_1a_store.py
- HISTORY-1A: HISTORY\history_1a_workflow_grammar_gate_history.py
- HISTORY-1C: HISTORY\history_1c_run_history_loader.py
- INPUT-1B: INPUT\input_1b_excel_provider.py
- NAV-1A: NAV\nav_1a_selenium_helpers.py
- PIPE-1A: PIPE\pipe_1a_run_orchestrator.py
- PIPE-1A: PIPE\pipe_1a_workflow_grammar_gate_pipeline.py
- PIPE-1B: PIPE\pipe_1b_worklist_config.py
- PIPE-1C: PIPE\pipe_1c_steps_loader.py
- PIPE-1D: PIPE\pipe_1d_step_executor.py
- REPORT-1A: REPORT\report_1a_run_report.py
- REPORT-1A: REPORT\report_1a_step_logs_from_jsonl.py
- REPORT-1A: REPORT\report_1a_workflow_grammar_gate_report.py
- REPORT-1B: REPORT\report_1b_workflow_grammar_gate_report_text.py
- REPORT-1C: REPORT\report_1c_workflow_grammar_gate_report_summary.py
- RUN-1A: RUN\run_1a_workflow_grammar_gate_run.py
- RUN-1A: RUN\run_1a_workflow_runner.py
- RUN-1E: RUN\run_1e_post_run_reporting.py
- SNAP-1A: SNAP\snap_1a_failure_capture.py