# LIBRARY_INDEX

Generated at (UTC): `2026-05-07T17:56:22.170400+00:00`

## Reference: LIBRARY_MAP.md

_Included for convenience; authoritative source remains the file itself._

```text
# LIBRARY REGISTRY INDEX
 
This document is the authoritative registry for the RPA_LIBRARY knowledge base.
 
It defines:
- GLOBAL_MILESTONES (ENTRY, AUTH, INPUT, LOOP, NAV, ACT, VAL, OUT, LOG, STATE)
- GLOBAL_OPTION_IDS (e.g., AUTH-1A)
- CANONICAL_FILE_PATHS (where each option lives)
- ARCHIVE_RULES (how older modules are retained)
 
Use this file for:
- duplicate detection
- option ID collision checks
- canonical module lookup
 
GLOBAL_MILESTONES:
ENTRY
AUTH
INPUT
LOOP
NAV
ACT
VAL
OUT
LOG
STATE
 
GLOBAL_OPTION_IDS (current):
ENTRY-1A
AUTH-1A
INPUT-1A
INPUT-1B
INPUT-1C
LOOP-1A
LOOP-1B
NAV-1A
NAV-1B
ACT-1A
ACT-1B
VAL-1A
VAL-1B
OUT-1A
LOG-1A
LOG-1B
STATE-1A
STATE-1B
 
---
 
# RPA Library Map (Global Milestone Options)
 
This repository is a canonical library of reusable RPA building blocks.
Each building block is categorized by MILESTONE and assigned a GLOBAL OPTION ID.
Option IDs are stable: when referenced (e.g., AUTH-1A), they mean the same approach across all workflows.
 
## How to Use This Map
- Each milestone has one or more option IDs (A, B, C…).
- Each option ID maps to a canonical module file path.
- If a new script introduces a meaningfully different approach, the Library Builder Agent must propose a new option ID for approval.
- Deprecated implementations are moved to the milestone's `/archive/` folder, but option IDs are never reused.
 
---
 
# Milestones (Global)
 
## ENTRY — Initialization & Browser Startup
Purpose: start run context, configure webdriver, define headless behavior, establish directories.
 
- ENTRY-1A: Standard headless-first webdriver bootstrap (Chrome/Edge configurable)  
  Path: `ENTRY/entry_1a_webdriver_bootstrap.py`
 
## AUTH — Authentication & Session Establishment
Purpose: login, session checks, token/SSO flows, re-auth handling, guarded login.
 
- AUTH-1A: Standard username/password form login with guarded "already logged in" check  
  Path: `AUTH/auth_1a_form_login_guarded.py`
 
## INPUT — Inputs & Data Sources
Purpose: resolve work items (none/static/excel/csv/api/sharepoint) and normalize to a worklist.
 
- INPUT-1A: No input (single-run)  
  Path: `INPUT/input_1a_none_single_run.py`
 
- INPUT-1B: Excel provider (sheet + column -> list of IDs)  
  Path: `INPUT/input_1b_excel_provider.py`
 
- INPUT-1C: CSV provider  
  Path: `INPUT/input_1c_csv_provider.py`
 
## LOOP — Worklist / Loop Execution
Purpose: per-item loop, resume/retry semantics, per-item context injection.
 
- LOOP-1A: Single-run (no loop)  
  Path: `LOOP/loop_1a_single_run.py`
 
- LOOP-1B: Per-item loop (generic iterator over worklist)  
  Path: `LOOP/loop_1b_per_item.py`
 
## NAV — Navigation
Purpose: page transitions, menu clicks, route changes, tab management, iframe focus management.
 
- NAV-1A: Tab management helpers (open/switch/close/wait)  
  Path: `NAV/nav_1a_tabs.py`
 
- NAV-1B: Iframe discovery + document targeting pattern  
  Path: `NAV/nav_1b_iframe_targeting.py`
 
## ACT — Action Execution (DOM Interaction)
Purpose: stable click/type/select, JS injection, element readiness, anti-flake patterns.
 
- ACT-1A: Stable click + scroll + visibility rules (headless safe)  
  Path: `ACT/act_1a_stable_click.py`
 
- ACT-1B: JS execution wrapper + structured return contracts  
  Path: `ACT/act_1b_exec_js_contracts.py`
 
## VAL — Validation & Success Criteria
Purpose: how we decide success/failure; page state, file existence, expected UI state.
 
- VAL-1A: UI state validation via selector presence + text checks  
  Path: `VAL/val_1a_ui_state.py`
 
- VAL-1B: Download validation (file exists, size > 0, optional name patterns)  
  Path: `VAL/val_1b_download_validation.py`
 
## OUT — Output / Downloads / Artifacts
Purpose: download management, file naming, output directories, optional post-processing.
 
- OUT-1A: Download wait/poll + directory management  
  Path: `OUT/out_1a_download_wait.py`
 
## LOG — Logging, Errors, and Observability
Purpose: structured logs, step-level logging, error taxonomy, screenshots, artifact paths.
 
- LOG-1A: Standard structured logging + run_id + per-item context  
  Path: `LOG/log_1a_structured_logging.py`
 
- LOG-1B: Error taxonomy (frame/tab/selector/stale/auth/download)  
  Path: `LOG/log_1b_error_taxonomy.py`
 
## STATE — State / Retry (Optional)
Purpose: persistence of per-item outcomes, retry lists, manifests, resumability.
 
- STATE-1A: No state (stateless run)  
  Path: `STATE/state_1a_none.py`
 
- STATE-1B: JSONL manifest state (queued/success/fail + metadata)  
  Path: `STATE/state_1b_manifest_jsonl.py`
 
---
 
# Archive Policy
- Archived code lives under each milestone: `<MILESTONE>/archive/`
- Option IDs are never reused.
- Archive files must include a header comment explaining:
  - replaced by which module
  - reason
  - date
```

## Reference: NAMING_CONVENTIONS.md

_Included for convenience; authoritative source remains the file itself._

```text
# NAMING REGISTRY INDEX
 
This document is the authoritative naming and versioning standard for the RPA_LIBRARY knowledge base.
 
It defines:
- FILE_NAMING_PATTERN
- OPTION_ID_POLICY
- ARCHIVE_POLICY
- MODULE_REQUIREMENTS
- WORKFLOW_NAMING_RULES
 
Use this file for:
- deterministic filenames
- duplicate prevention
- consistent archives/sunset rules
 
---
 
# Naming Conventions — RPA Library (Global Options)
 
## Goals
- Make deduplication easy.
- Keep option IDs stable across workflows.
- Ensure the Library Builder Agent can infer where code belongs.
- Keep the library scalable and consistent as new options are added.
 
---
 
## Folder Structure
 
Each milestone has a folder at the library root:
 
`/<MILESTONE>/`
 
Each milestone folder contains:
- canonical option modules
- an `archive/` folder for deprecated versions
 
Example:
 
`/AUTH/`  
`/AUTH/archive/`
 
---
 
## FILE_NAMING_PATTERN (Canonical)
 
Canonical modules MUST use this filename pattern:
 
`<MILESTONE>/<milestone>_<option_id>_<short_slug>.py`
 
Where:
- `<MILESTONE>` is the folder name (e.g., AUTH)
- `<milestone>` is lowercase (e.g., auth)
- `<option_id>` is lowercase (e.g., 1a, 1b)
- `<short_slug>` is a short descriptive label
 
Examples (canonical):
- `AUTH/auth_1a_form_login_guarded.py`
- `INPUT/input_1b_excel_provider.py`
- `STATE/state_1b_manifest_jsonl.py`
 
---
 
## ARCHIVE_NAMING_PATTERN (Sunset)
 
Archived modules MUST use this filename pattern:
 
`<MILESTONE>/archive/<milestone>_<option_id>_<short_slug>__sunset_YYYYMMDD.py`
 
Examples (archive):
- `AUTH/archive/auth_1a_form_login_guarded__sunset_20260226.py`
 
---
 
## Option ID Rules (Global, Stable)
 
- Option IDs are global within each milestone: `1A, 1B, 1C...`
- Option IDs are never reused.
- A new option ID is created only when an approach is **meaningfully different**.
 
A new option must be proposed with:
- why it differs (X/Y/Z)
- when to use it
- when NOT to use it
- headless implications
- what it replaces (if anything)
 
The agent must wait for approval before minting a new option ID.
 
---
 
## Canonical vs New Option Decision Rule
 
Update canonical module (same option ID) when:
- the approach is the same
- changes are refactors, reliability improvements, cleanup
- backward compatibility remains mostly intact
 
Create a new option ID when:
- behavior changes materially
- authentication method changes (e.g., SSO vs form login)
- input strategy changes (e.g., Excel-based worklist vs API worklist)
- the approach is distinct enough that both should remain available
 
---
 
## File Content Requirements (every module)
 
Each module must include:
 
1) Module docstring containing:
- Purpose
- Inputs
- Outputs
- When to use
- When NOT to use
- Headless notes
- Dependencies
- Common failure modes + mitigations
 
2) Clear public API boundary:
- an obvious entry function (e.g., `login(driver, cfg, ctx)`)
  OR
- a clear class interface
 
3) Minimal usage example:
- in the docstring OR
- in a `if __name__ == "__main__":` guard (when appropriate)
 
4) Security rule:
- Never log secrets.
- Credentials are referenced via environment variable names or secret keys, not raw values.
 
---
 
## Sunset / Archive Rules
 
When a module is replaced:
 
1) Move old version to `archive/` using the sunset naming pattern.
2) Add a header comment at the top of the archived file explaining:
- replaced by: `<new_module_path>`
- reason: `<brief reason>`
- date: `YYYY-MM-DD`
 
Canonical modules remain in the milestone root folder.
 
---
 
## Workflow Naming (steps.json)
 
Workflows should be named by intent, not by portal/system name.
 
Pattern:
- `workflows/<intent>_<mode>.steps.json`
 
Examples:
- `workflows/export_catalog_single_run.steps.json`
- `workflows/export_catalog_per_item.steps.json`
```

## Summary

| Milestone | Option ID | Module path |
|---|---|---|
| .DEV_TMP | .DEV_TMP-?? | `.dev_tmp\build_2c_smoke\dev\dev_smoke_open_example_com_and_verify_page_title.py` |
| .DEV_TMP | .DEV_TMP-?? | `.dev_tmp\cli_2b_smoke\dev\dev_smoke_open_example_com_and_verify_page_title.py` |
| ACT | ACT-1A | `ACT\act_1a_action_engine.py` |
| ACT | ACT-1B | `ACT\act_1b_logging_integration.py` |
| ACT | ACT-1C | `ACT\act_1c_conditional_guards.py` |
| ACT | ACT-?? | `ACT\__init__.py` |
| AGENT | AGENT-1A | `AGENT\agent_1a_context_pack.py` |
| AGENT | AGENT-2A | `AGENT\agent_2a_autonomous_loop.py` |
| AGENT | AGENT-2B | `AGENT\agent_2b_scheduler.py` |
| AGENT | AGENT-?? | `AGENT\__init__.py` |
| AUTH | AUTH-1A | `AUTH\auth_1a_form_login_guarded.py` |
| AUTH | AUTH-1B | `AUTH\auth_1b_session_restore.py` |
| AUTH | AUTH-?? | `AUTH\__init__.py` |
| BASE_APP.PY | BASE_APP.PY-?? | `base_app.py` |
| BUILD | BUILD-1A | `BUILD\build_1a_workflow_generator.py` |
| BUILD | BUILD-1A | `BUILD\build_1a_workflow_grammar_gate_entrypoints.py` |
| BUILD | BUILD-1B | `BUILD\build_1b_intake_questionnaire.py` |
| BUILD | BUILD-1C | `BUILD\build_1c_action_normalizer.py` |
| BUILD | BUILD-1C | `BUILD\build_1c_smoke_stub_generator.py` |
| BUILD | BUILD-2A | `BUILD\build_2a_nl_spec_generator.py` |
| BUILD | BUILD-2A | `BUILD\build_2a_repeat_support.py` |
| BUILD | BUILD-2B | `BUILD\build_2b_plan_optimizer.py` |
| BUILD | BUILD-2C | `BUILD\build_2c_full_bundle.py` |
| BUILD | BUILD-2D | `BUILD\build_2d_determinism.py` |
| BUILD | BUILD-2D | `BUILD\build_2d_step_grammar_gate.py` |
| BUILD | BUILD-2E | `BUILD\build_2e_workflow_grammar_gate.py` |
| BUILD | BUILD-2F | `BUILD\build_2f_workflow_file_grammar_gate.py` |
| BUILD | BUILD-2G | `BUILD\build_2g_workflow_tree_grammar_gate.py` |
| BUILD | BUILD-3A | `BUILD\build_3a_deploy_bundle_format.py` |
| BUILD | BUILD-3B | `BUILD\build_3b_bundle_fingerprint.py` |
| BUILD | BUILD-3C | `BUILD\build_3c_deploy_bundle_builder.py` |
| BUILD | BUILD-3D | `BUILD\build_3d_doc_index_artifact_bundler.py` |
| BUILD | BUILD-3E | `BUILD\build_3e_bundle_build_manifest_integrator.py` |
| BUILD | BUILD-3F | `BUILD\build_3f_deploy_bundle_stamper.py` |
| BUILD | BUILD-3G | `BUILD\build_3g_deploy_bundle_writer.py` |
| BUILD | BUILD-3H | `BUILD\build_3h_capture_to_deploy_bundle_pipeline.py` |
| BUILD | BUILD-?? | `BUILD\__init__.py` |
| CAPTURE | CAPTURE-1A | `CAPTURE\capture_1a_semi_auto.py` |
| CAPTURE | CAPTURE-1A | `CAPTURE\capture_1a_step_recorder.py` |
| CAPTURE | CAPTURE-?? | `CAPTURE\__init__.py` |
| CLI | CLI-1A | `CLI\cli_1a_capture_to_deploy_bundle.py` |
| CLI | CLI-1A | `CLI\cli_1a_run_pipeline.py` |
| CLI | CLI-1A | `CLI\cli_1a_workflow_grammar_gate.py` |
| CLI | CLI-1A | `CLI\cli_pack_1a.py` |
| CLI | CLI-1B | `CLI\cli_1b_capture_to_deploy_bundle.py` |
| CLI | CLI-1B | `CLI\cli_1b_config_loader.py` |
| CLI | CLI-1C | `CLI\cli_1c_args_overrides.py` |
| CLI | CLI-1C | `CLI\cli_1c_capture_to_deploy_bundle.py` |
| CLI | CLI-1D | `CLI\cli_1d_capture_to_deploy_bundle_auto.py` |
| CLI | CLI-1E | `CLI\cli_1e_deploy_bundle_info.py` |
| CLI | CLI-1E | `CLI\cli_1e_run_deploy_bundle.py` |
| CLI | CLI-1F | `CLI\cli_1f_generate_reports.py` |
| CLI | CLI-1F | `CLI\cli_1f_run_deploy_bundle_with_report.py` |
| CLI | CLI-1G | `CLI\cli_1g_run_deploy_bundle_with_report_fail_fast.py` |
| CLI | CLI-1G | `CLI\cli_1g_workflow_grammar_gate.py` |
| CLI | CLI-1H | `CLI\cli_1h_run_deploy_bundle_cli_resolver.py` |
| CLI | CLI-1H | `CLI\cli_1h_workflow_grammar_gate_pipeline.py` |
| CLI | CLI-1I | `CLI\cli_1i_build_doc_index_artifact.py` |
| CLI | CLI-1I | `CLI\cli_1i_bundle_doc_index_and_manifest_cli.py` |
| CLI | CLI-2B | `CLI\cli_2b_unified.py` |
| CLI | CLI-?? | `CLI\__init__.py` |
| DEPLOY | DEPLOY-1A | `DEPLOY\deploy_1a_service_runner.py` |
| DEV | DEV-1A | `dev\dev_smoke_agent_1a_context_pack.py` |
| DEV | DEV-1A | `dev\dev_smoke_auth_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_build_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_build_1a_workflow_grammar_gate_entrypoints.py` |
| DEV | DEV-1A | `dev\dev_smoke_capture_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_cli_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_cli_1a_workflow_grammar_gate.py` |
| DEV | DEV-1A | `dev\dev_smoke_deploy_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_diff_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_diff_1a_capture_edit_diff.py` |
| DEV | DEV-1A | `dev\dev_smoke_diff_1a_workflow_grammar_gate_report_diff.py` |
| DEV | DEV-1A | `dev\dev_smoke_doc_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_doc_1a_library_index.py` |
| DEV | DEV-1A | `dev\dev_smoke_doc_1a_workflow_grammar_gate.py` |
| DEV | DEV-1A | `dev\dev_smoke_doctor_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_doctor_1a_workflow_grammar_gate.py` |
| DEV | DEV-1A | `dev\dev_smoke_entry_1a_workflow_grammar_gate.py` |
| DEV | DEV-1A | `dev\dev_smoke_guard_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_guard_1a_workflow_grammar_gate_guard.py` |
| DEV | DEV-1A | `dev\dev_smoke_guard_1a_workflow_grammar_guard.py` |
| DEV | DEV-1A | `dev\dev_smoke_heal_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_history_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_history_1a_workflow_grammar_gate_history.py` |
| DEV | DEV-1A | `dev\dev_smoke_learn_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_lint_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_log_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_nav_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_obs_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_out_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_pack_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_pipe_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_pipe_1a_workflow_grammar_gate_pipeline.py` |
| DEV | DEV-1A | `dev\dev_smoke_plan_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_reason_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_registry_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_replay_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_report_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_report_1a_workflow_grammar_gate_report.py` |
| DEV | DEV-1A | `dev\dev_smoke_run_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_run_1a_workflow_grammar_gate.py` |
| DEV | DEV-1A | `dev\dev_smoke_run_1a_workflow_grammar_gate_run.py` |
| DEV | DEV-1A | `dev\dev_smoke_schema_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_selector_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_snap_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_snap_1a_workflow_capture.py` |
| DEV | DEV-1A | `dev\dev_smoke_val_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_var_1a.py` |
| DEV | DEV-1A | `dev\dev_smoke_workflow_1a_loader.py` |
| DEV | DEV-1B | `dev\dev_smoke_act_1b_logging.py` |
| DEV | DEV-1B | `dev\dev_smoke_auth_1b.py` |
| DEV | DEV-1B | `dev\dev_smoke_build_1b.py` |
| DEV | DEV-1B | `dev\dev_smoke_cli_1b.py` |
| DEV | DEV-1B | `dev\dev_smoke_cli_1b_config_loader.py` |
| DEV | DEV-1B | `dev\dev_smoke_doctor_1b_workflow_grammar_gate.py` |
| DEV | DEV-1B | `dev\dev_smoke_input_1b_excel_provider.py` |
| DEV | DEV-1B | `dev\dev_smoke_learn_1b.py` |
| DEV | DEV-1B | `dev\dev_smoke_log_1b.py` |
| DEV | DEV-1B | `dev\dev_smoke_out_1b.py` |
| DEV | DEV-1B | `dev\dev_smoke_pipe_1b.py` |
| DEV | DEV-1B | `dev\dev_smoke_report_1b_workflow_grammar_gate_report_text.py` |
| DEV | DEV-1B | `dev\dev_smoke_snap_1b_selector_pack.py` |
| DEV | DEV-1B | `dev\dev_smoke_val_1b.py` |
| DEV | DEV-1C | `dev\dev_smoke_act_1c.py` |
| DEV | DEV-1C | `dev\dev_smoke_build_1c.py` |
| DEV | DEV-1C | `dev\dev_smoke_cli_1c.py` |
| DEV | DEV-1C | `dev\dev_smoke_pipe_1c.py` |
| DEV | DEV-1C | `dev\dev_smoke_report_1c_workflow_grammar_gate_report_summary.py` |
| DEV | DEV-1C | `dev\dev_smoke_snap_1c_capture_bundle.py` |
| DEV | DEV-1C | `dev\dev_smoke_state_1c.py` |
| DEV | DEV-1D | `dev\dev_smoke_pipe_1d_a.py` |
| DEV | DEV-1D | `dev\dev_smoke_snap_1d_bundle_io.py` |
| DEV | DEV-1D | `dev\dev_smoke_state_1d.py` |
| DEV | DEV-1E | `dev\dev_smoke_cli_1e_run_deploy_bundle.py` |
| DEV | DEV-1E | `dev\dev_smoke_doc_1e_cli_run_deploy_bundle_cli_resolver_entry.py` |
| DEV | DEV-1E | `dev\dev_smoke_pipe_1e.py` |
| DEV | DEV-1E | `dev\dev_smoke_report_1e_build_manifest_artifact.py` |
| DEV | DEV-1E | `dev\dev_smoke_report_1e_deploy_bundle_validation_report_writer.py` |
| DEV | DEV-1E | `dev\dev_smoke_run_1e_deploy_bundle_runner_adapter.py` |
| DEV | DEV-1E | `dev\dev_smoke_snap_1e_bundle_export.py` |
| DEV | DEV-1E | `dev\dev_smoke_workflow_1e_steps_normalizer.py` |
| DEV | DEV-1F | `dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py` |
| DEV | DEV-1F | `dev\dev_smoke_doc_1f_doc_index_aggregator.py` |
| DEV | DEV-1F | `dev\dev_smoke_snap_1f_materialize_selectors.py` |
| DEV | DEV-1F | `dev\dev_smoke_workflow_1f_selector_ref_first.py` |
| DEV | DEV-1G | `dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py` |
| DEV | DEV-1G | `dev\dev_smoke_cli_1g_workflow_grammar_gate.py` |
| DEV | DEV-1G | `dev\dev_smoke_doc_1g_doc_index_entry_contract.py` |
| DEV | DEV-1G | `dev\dev_smoke_workflow_1g_deploy_bundle_loader.py` |
| DEV | DEV-1H | `dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py` |
| DEV | DEV-1H | `dev\dev_smoke_cli_1h_workflow_grammar_gate_pipeline.py` |
| DEV | DEV-1H | `dev\dev_smoke_doc_1h_doc_index_collect_validate.py` |
| DEV | DEV-1I | `dev\dev_smoke_cli_1i_build_doc_index_artifact.py` |
| DEV | DEV-1I | `dev\dev_smoke_cli_1i_bundle_doc_index_and_manifest_cli.py` |
| DEV | DEV-1I | `dev\dev_smoke_doc_doc_index_entry_cli_1i_bundle_doc_index_and_manifest_cli.py` |
| DEV | DEV-2A | `dev\dev_smoke_agent_2a.py` |
| DEV | DEV-2A | `dev\dev_smoke_build_2a.py` |
| DEV | DEV-2A | `dev\dev_smoke_pipe_2a.py` |
| DEV | DEV-2A | `dev\dev_smoke_val_2a_deploy_bundle_validator.py` |
| DEV | DEV-2A | `dev\dev_smoke_workflow_workflow_2a_capture_actions_to_schema_steps.py` |
| DEV | DEV-2B | `dev\dev_smoke_agent_2b.py` |
| DEV | DEV-2B | `dev\dev_smoke_build_2b.py` |
| DEV | DEV-2B | `dev\dev_smoke_cli_2b.py` |
| DEV | DEV-2B | `dev\dev_smoke_pipe_2b.py` |
| DEV | DEV-2B | `dev\dev_smoke_workflow_workflow_2b_capture_js_event_recorder.py` |
| DEV | DEV-2C | `dev\dev_smoke_build_2c.py` |
| DEV | DEV-2C | `dev\dev_smoke_pipe_2c.py` |
| DEV | DEV-2C | `dev\dev_smoke_workflow_workflow_2c_capture_events_to_schema_steps_encoder.py` |
| DEV | DEV-2D | `dev\dev_smoke_build_2d.py` |
| DEV | DEV-2D | `dev\dev_smoke_pipe_2d.py` |
| DEV | DEV-2E | `dev\dev_smoke_build_2e.py` |
| DEV | DEV-2E | `dev\dev_smoke_pipe_2e.py` |
| DEV | DEV-2F | `dev\dev_smoke_build_2f.py` |
| DEV | DEV-2G | `dev\dev_smoke_build_2g.py` |
| DEV | DEV-3A | `dev\dev_smoke_build_3a_deploy_bundle_format.py` |
| DEV | DEV-3B | `dev\dev_smoke_build_3b_bundle_fingerprint.py` |
| DEV | DEV-3C | `dev\dev_smoke_build_3c_deploy_bundle_builder.py` |
| DEV | DEV-3D | `dev\dev_smoke_build_3d_doc_index_artifact_bundler.py` |
| DEV | DEV-3E | `dev\dev_smoke_build_3e_bundle_build_manifest_integrator.py` |
| DEV | DEV-?? | `dev\dev_smoke_10_1_1_failure_capture.py` |
| DEV | DEV-?? | `dev\dev_smoke_10_1_2_screenshot_capture.py` |
| DEV | DEV-?? | `dev\dev_smoke_10_1_3_snapshot_persistence.py` |
| DEV | DEV-?? | `dev\dev_smoke_10_2_1_run_manifest.py` |
| DEV | DEV-?? | `dev\dev_smoke_10_2_2_step_outcomes.py` |
| DEV | DEV-?? | `dev\dev_smoke_10_2_3_error_normalization.py` |
| DEV | DEV-?? | `dev\dev_smoke_10_3_1_run_report.py` |
| DEV | DEV-?? | `dev\dev_smoke_10_3_2_run_report_markdown.py` |
| DEV | DEV-?? | `dev\dev_smoke_10_3_3_junit_xml.py` |
| DEV | DEV-?? | `dev\dev_smoke_10_4_1_generate_reports.py` |
| DEV | DEV-?? | `dev\dev_smoke_10_4_2_post_run_reporting.py` |
| DEV | DEV-?? | `dev\dev_smoke_10_4_3_cli_generate_reports.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_1_1_slos_success_criteria.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_1_2_operator_runbooks.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_1_3_support_escalation_paths.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_2_1_versioning_policy.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_2_2_reviewable_diffs.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_2_3_promotion_gates.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_3_1_release_manifest.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_3_2_bundle_fingerprint.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_3_3_promotion_record.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_4_1_doctor_pre_run_checks.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_4_2_guard_prod_defaults.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_4_3_rollback_recovery_procedures.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_5_1_artifact_retention_policy.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_5_2_alerting_signals.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_5_3_audit_logging_replay_spec.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_5_4_replay_index_verifier.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_5_5_incident_packet_manifest.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_5_6_release_readiness_gate.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_5_7_evidence_bundle_assembler.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_6_1_prod_smoke_pipeline.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_6_2_rollback_rerun_determinism.py` |
| DEV | DEV-?? | `dev\dev_smoke_12_6_3_operational_gates_enforcement.py` |
| DEV | DEV-?? | `dev\dev_smoke_9_4_3_deterministic_generation.py` |
| DEV | DEV-?? | `dev\dev_smoke_9_4_3_run_history_loader.py` |
| DEV | DEV-?? | `dev\dev_smoke_act_action_engine.py` |
| DEV | DEV-?? | `dev\dev_smoke_act_download_wait.py` |
| DEV | DEV-?? | `dev\dev_smoke_entry_bootstrap.py` |
| DEV | DEV-?? | `dev\dev_smoke_go_to_google_search_for_something_click_result_then_go_back_and_search_again.py` |
| DEV | DEV-?? | `dev\dev_smoke_go_to_google_search_for_weather_click_first_result.py` |
| DEV | DEV-?? | `dev\dev_smoke_login_to_a_site_and_download_a_report.py` |
| DEV | DEV-?? | `dev\dev_smoke_login_to_portal_and_export_report.py` |
| DEV | DEV-?? | `dev\dev_smoke_open_a_slow_website_and_click_something_immediately.py` |
| DEV | DEV-?? | `dev\dev_smoke_open_example_com_and_click_login_button_that_does_not_exist.py` |
| DEV | DEV-?? | `dev\dev_smoke_open_example_com_click_login_and_verify_page_title.py` |
| DEV | DEV-?? | `dev\dev_smoke_open_google_and_click_search.py` |
| DEV | DEV-?? | `dev\dev_smoke_phase_11_5_1_capture_to_workflow_validity.py` |
| DEV | DEV-?? | `dev\dev_smoke_phase_11_5_2_bundle_packaging_determinism.py` |
| DEV | DEV-?? | `dev\dev_smoke_phase_11_5_3_deploy_run_path_minimal.py` |
| DEV | DEV-?? | `dev\dev_smoke_state_input.py` |
| DEV | DEV-?? | `dev\sitecustomize.py` |
| DIFF | DIFF-12A | `DIFF\diff_12a_reviewable_diffs.py` |
| DIFF | DIFF-1A | `DIFF\diff_1a_capture_edit_diff.py` |
| DIFF | DIFF-1A | `DIFF\diff_1a_config_changes.py` |
| DIFF | DIFF-1A | `DIFF\diff_1a_workflow_grammar_gate_report_diff.py` |
| DIFF | DIFF-?? | `DIFF\__init__.py` |
| DOC | DOC-12A | `DOC\doc_12a_slos_success_criteria.py` |
| DOC | DOC-12B | `DOC\doc_12b_operator_runbooks.py` |
| DOC | DOC-12C | `DOC\doc_12c_support_escalation_paths.py` |
| DOC | DOC-12D | `DOC\doc_12d_rollback_recovery_procedures.py` |
| DOC | DOC-1A | `DOC\doc_1a_library_index.py` |
| DOC | DOC-1A | `DOC\doc_1a_workflow_grammar_gate.py` |
| DOC | DOC-1A | `DOC\runbook_1a_generator.py` |
| DOC | DOC-1E | `DOC\doc_1e_cli_run_deploy_bundle_cli_resolver_entry.py` |
| DOC | DOC-1F | `DOC\doc_1f_doc_index_aggregator.py` |
| DOC | DOC-1G | `DOC\doc_1g_doc_index_entry_contract.py` |
| DOC | DOC-1H | `DOC\doc_1h_doc_index_collect_validate.py` |
| DOC | DOC-1I | `DOC\doc_index_entry_cli_1i_bundle_doc_index_and_manifest_cli.py` |
| DOC | DOC-?? | `DOC\__init__.py` |
| DOCTOR | DOCTOR-12A | `DOCTOR\doctor_12a_pre_run_checks.py` |
| DOCTOR | DOCTOR-12D | `DOCTOR\doctor_12d_release_readiness_gate.py` |
| DOCTOR | DOCTOR-1A | `DOCTOR\doctor_1a_check.py` |
| DOCTOR | DOCTOR-1A | `DOCTOR\doctor_1a_workflow_grammar_gate.py` |
| DOCTOR | DOCTOR-1B | `DOCTOR\doctor_1b_workflow_grammar_gate.py` |
| DOCTOR | DOCTOR-?? | `DOCTOR\__init__.py` |
| ENTRY | ENTRY-1A | `ENTRY\entry_1a_webdriver_bootstrap.py` |
| ENTRY | ENTRY-1A | `ENTRY\entry_1a_workflow_grammar_gate.py` |
| ENTRY | ENTRY-?? | `ENTRY\__init__.py` |
| GUARD | GUARD-12A | `GUARD\guard_12a_prod_defaults.py` |
| GUARD | GUARD-1A | `GUARD\guard_1a_runtime.py` |
| GUARD | GUARD-1A | `GUARD\guard_1a_workflow_grammar_gate_guard.py` |
| GUARD | GUARD-1A | `GUARD\guard_1a_workflow_grammar_guard.py` |
| GUARD | GUARD-?? | `GUARD\__init__.py` |
| HEAL | HEAL-1A | `HEAL\heal_1a_patch_workflow.py` |
| HEAL | HEAL-?? | `HEAL\__init__.py` |
| HISTORY | HISTORY-12A | `HISTORY\history_12a_audit_logging_replay_spec.py` |
| HISTORY | HISTORY-1A | `HISTORY\history_1a_run_manifest.py` |
| HISTORY | HISTORY-1A | `HISTORY\history_1a_store.py` |
| HISTORY | HISTORY-1A | `HISTORY\history_1a_workflow_grammar_gate_history.py` |
| HISTORY | HISTORY-1B | `HISTORY\history_1b_step_outcomes.py` |
| HISTORY | HISTORY-1C | `HISTORY\history_1c_error_normalization.py` |
| HISTORY | HISTORY-1C | `HISTORY\history_1c_run_history_loader.py` |
| HISTORY | HISTORY-?? | `HISTORY\__init__.py` |
| INPUT | INPUT-1B | `INPUT\input_1b_excel_provider.py` |
| INPUT | INPUT-?? | `INPUT\__init__.py` |
| LEARN | LEARN-1A | `LEARN\learn_1a_failure_patterns.py` |
| LEARN | LEARN-1B | `LEARN\learn_1b_selector_intelligence.py` |
| LEARN | LEARN-?? | `LEARN\__init__.py` |
| LINT | LINT-1A | `LINT\lint_1a_steps_validator.py` |
| LINT | LINT-?? | `LINT\__init__.py` |
| LINT | LINT-?? | `LINT\lint_steps.py` |
| LOG | LOG-1A | `LOG\log_1a_structured_logging.py` |
| LOG | LOG-1B | `LOG\log_1b_error_taxonomy.py` |
| LOG | LOG-1B | `LOG\log_1b_logger_reset.py` |
| LOG | LOG-?? | `LOG\__init__.py` |
| LOOP | LOOP-1B | `LOOP\loop_1b_per_item.py` |
| LOOP | LOOP-?? | `LOOP\__init__.py` |
| NAV | NAV-1A | `NAV\nav_1a_selenium_helpers.py` |
| NAV | NAV-?? | `NAV\__init__.py` |
| OBS | OBS-1A | `OBS\obs_1a_run_timeline.py` |
| OBS | OBS-?? | `OBS\__init__.py` |
| OUT | OUT-1A | `OUT\out_1a_download_wait.py` |
| OUT | OUT-1B | `OUT\out_1b_artifact_manager.py` |
| OUT | OUT-?? | `OUT\__init__.py` |
| PIPE | PIPE-1A | `PIPE\pipe_1a_run_orchestrator.py` |
| PIPE | PIPE-1A | `PIPE\pipe_1a_workflow_grammar_gate_pipeline.py` |
| PIPE | PIPE-1B | `PIPE\pipe_1b_worklist_config.py` |
| PIPE | PIPE-1C | `PIPE\pipe_1c_steps_loader.py` |
| PIPE | PIPE-1D | `PIPE\pipe_1d_step_executor.py` |
| PIPE | PIPE-1E | `PIPE\pipe_1e_runner.py` |
| PIPE | PIPE-1F | `PIPE\pipe_1f_env_overrides.py` |
| PIPE | PIPE-1G | `PIPE\pipe_1g_env_force_overrides.py` |
| PIPE | PIPE-1H | `PIPE\pipe_1h_log_jsonl_path_policy.py` |
| PIPE | PIPE-2A | `PIPE\pipe_2a_var_aware_steps.py` |
| PIPE | PIPE-2B | `PIPE\pipe_2b_step_blocks.py` |
| PIPE | PIPE-2C | `PIPE\pipe_2c_error_plumbing.py` |
| PIPE | PIPE-2D | `PIPE\pipe_2d_artifact_integration.py` |
| PIPE | PIPE-2E | `PIPE\pipe_2e_run_summary.py` |
| PIPE | PIPE-?? | `PIPE\__init__.py` |
| PLAN | PLAN-1A | `PLAN\plan_1a_step_planner.py` |
| PLAN | PLAN-?? | `PLAN\__init__.py` |
| REASON | REASON-1A | `REASON\reason_1a_diagnose.py` |
| REASON | REASON-?? | `REASON\__init__.py` |
| REGISTRY | REGISTRY-12A | `REGISTRY\reg_12a_versioning_policy.py` |
| REGISTRY | REGISTRY-12B | `REGISTRY\reg_12b_promotion_gates.py` |
| REGISTRY | REGISTRY-1A | `REGISTRY\registry_1a_generate.py` |
| REGISTRY | REGISTRY-?? | `REGISTRY\__init__.py` |
| REPLAY | REPLAY-12A | `REPLAY\replay_12a_index_verifier.py` |
| REPLAY | REPLAY-1A | `REPLAY\replay_1a_run_replay.py` |
| REPLAY | REPLAY-?? | `REPLAY\__init__.py` |
| REPORT | REPORT-12A | `REPORT\report_12a_release_manifest.py` |
| REPORT | REPORT-12B | `REPORT\report_12b_bundle_fingerprint.py` |
| REPORT | REPORT-12C | `REPORT\report_12c_promotion_record.py` |
| REPORT | REPORT-12D | `REPORT\report_12d_artifact_retention_policy.py` |
| REPORT | REPORT-12E | `REPORT\report_12e_alerting_signals.py` |
| REPORT | REPORT-12F | `REPORT\report_12f_incident_packet_manifest.py` |
| REPORT | REPORT-12G | `REPORT\report_12g_evidence_bundle_assembler.py` |
| REPORT | REPORT-1A | `REPORT\report_1a_generate.py` |
| REPORT | REPORT-1A | `REPORT\report_1a_run_report.py` |
| REPORT | REPORT-1A | `REPORT\report_1a_step_logs_from_jsonl.py` |
| REPORT | REPORT-1A | `REPORT\report_1a_workflow_grammar_gate_report.py` |
| REPORT | REPORT-1B | `REPORT\report_1b_run_report_markdown.py` |
| REPORT | REPORT-1B | `REPORT\report_1b_workflow_grammar_gate_report_text.py` |
| REPORT | REPORT-1C | `REPORT\report_1c_junit_xml.py` |
| REPORT | REPORT-1C | `REPORT\report_1c_workflow_grammar_gate_report_summary.py` |
| REPORT | REPORT-1D | `REPORT\report_1d_generate_reports.py` |
| REPORT | REPORT-1E | `REPORT\report_1e_build_manifest_artifact.py` |
| REPORT | REPORT-1E | `REPORT\report_1e_deploy_bundle_validation_report_writer.py` |
| REPORT | REPORT-?? | `REPORT\__init__.py` |
| RUN | RUN-12A | `RUN\run_12a_prod_smoke_pipeline.py` |
| RUN | RUN-12B | `RUN\run_12b_rollback_rerun_determinism.py` |
| RUN | RUN-12C | `RUN\run_12c_operational_gates_enforcement.py` |
| RUN | RUN-1A | `RUN\run_1a_workflow_grammar_gate.py` |
| RUN | RUN-1A | `RUN\run_1a_workflow_grammar_gate_run.py` |
| RUN | RUN-1A | `RUN\run_1a_workflow_runner.py` |
| RUN | RUN-1B | `RUN\run_1b_workflow_runner_with_snap.py` |
| RUN | RUN-1C | `RUN\run_1c_workflow_runner_with_guard.py` |
| RUN | RUN-1D | `RUN\run_1d_runner_with_history.py` |
| RUN | RUN-1E | `RUN\run_1e_deploy_bundle_runner_adapter.py` |
| RUN | RUN-1E | `RUN\run_1e_post_run_reporting.py` |
| RUN | RUN-?? | `RUN\__init__.py` |
| RUN | RUN-?? | `RUN\dev_run_workflow.py` |
| SCHEMA | SCHEMA-1A | `SCHEMA\schema_1a_generate.py` |
| SCHEMA | SCHEMA-?? | `SCHEMA\__init__.py` |
| SELECTOR | SELECTOR-1A | `SELECTOR\selector_1a_registry.py` |
| SELECTOR | SELECTOR-?? | `SELECTOR\__init__.py` |
| SNAP | SNAP-1A | `SNAP\snap_1a_capture.py` |
| SNAP | SNAP-1A | `SNAP\snap_1a_failure_capture.py` |
| SNAP | SNAP-1A | `SNAP\snap_1a_workflow_capture.py` |
| SNAP | SNAP-1B | `SNAP\snap_1b_screenshot_capture.py` |
| SNAP | SNAP-1B | `SNAP\snap_1b_selector_pack.py` |
| SNAP | SNAP-1C | `SNAP\snap_1c_capture_bundle.py` |
| SNAP | SNAP-1C | `SNAP\snap_1c_persist_artifacts.py` |
| SNAP | SNAP-1D | `SNAP\snap_1d_bundle_io.py` |
| SNAP | SNAP-1E | `SNAP\snap_1e_bundle_export.py` |
| SNAP | SNAP-1F | `SNAP\snap_1f_materialize_selectors.py` |
| SNAP | SNAP-?? | `SNAP\__init__.py` |
| STATE | STATE-1B | `STATE\state_1b_manifest_jsonl.py` |
| STATE | STATE-1C | `STATE\state_1c_retry_helpers.py` |
| STATE | STATE-1D | `STATE\state_1d_manifest_row_helpers.py` |
| STATE | STATE-?? | `STATE\__init__.py` |
| VAL | VAL-1A | `VAL\val_1a_ui_state.py` |
| VAL | VAL-1B | `VAL\val_1b_download_validation.py` |
| VAL | VAL-2A | `VAL\val_2a_deploy_bundle_validator.py` |
| VAL | VAL-?? | `VAL\__init__.py` |
| VAR | VAR-1A | `VAR\var_1a_runtime_store.py` |
| VAR | VAR-?? | `VAR\__init__.py` |
| WORKFLOW | WORKFLOW-1E | `WORKFLOW\workflow_1e_steps_normalizer.py` |
| WORKFLOW | WORKFLOW-1F | `WORKFLOW\workflow_1f_selector_ref_first.py` |
| WORKFLOW | WORKFLOW-2A | `WORKFLOW\workflow_2a_capture_actions_to_schema_steps.py` |
| WORKFLOW | WORKFLOW-2B | `WORKFLOW\workflow_2b_capture_js_event_recorder.py` |
| WORKFLOW | WORKFLOW-2C | `WORKFLOW\workflow_2c_capture_events_to_schema_steps_encoder.py` |
| WORKFLOWS | WORKFLOWS-1A | `WORKFLOWS\workflow_1a_loader.py` |
| WORKFLOWS | WORKFLOWS-1G | `WORKFLOWS\workflow_1g_deploy_bundle_loader.py` |
| WORKFLOWS | WORKFLOWS-?? | `WORKFLOWS\__init__.py` |

## Modules

### `.dev_tmp\build_2c_smoke\dev\dev_smoke_open_example_com_and_verify_page_title.py`

- **Milestone:** `.DEV_TMP`
- **Option ID:** `.DEV_TMP-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `.dev_tmp\cli_2b_smoke\dev\dev_smoke_open_example_com_and_verify_page_title.py`

- **Milestone:** `.DEV_TMP`
- **Option ID:** `.DEV_TMP-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `ACT\act_1a_action_engine.py`

- **Milestone:** `ACT`
- **Option ID:** `ACT-1A`
- **Exports (`__all__`):** `StepOutcome`, `ActionEngineError`, `run_actions`, `outcomes_as_dicts`, `outcomes_all_ok`, `dev_smoke`
- **Doc summary:** ACT-1A — Canonical Action Execution Layer (standard action surface)
- **Smoke tests:** `dev\dev_smoke_act_1b_logging.py`, `dev\dev_smoke_act_action_engine.py`, `dev\dev_smoke_act_download_wait.py`

### `ACT\act_1b_logging_integration.py`

- **Milestone:** `ACT`
- **Option ID:** `ACT-1B`
- **Exports (`__all__`):** `run_actions_logged`, `dev_smoke`
- **Doc summary:** ACT-1B — Structured logging integration wrapper for ACT-1A
- **Smoke tests:** `dev\dev_smoke_act_1b_logging.py`

### `ACT\act_1c_conditional_guards.py`

- **Milestone:** `ACT`
- **Option ID:** `ACT-1C`
- **Exports (`__all__`):** `element_exists`, `text_equals`, `text_contains`, `attribute_equals`, `should_run_step`
- **Doc summary:** ACT-1C — Conditional Step Guards.
- **Smoke tests:** `dev\dev_smoke_act_1c.py`

### `ACT\__init__.py`

- **Milestone:** `ACT`
- **Option ID:** `ACT-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `AGENT\agent_1a_context_pack.py`

- **Milestone:** `AGENT`
- **Option ID:** `AGENT-1A`
- **Exports (`__all__`):** `generate_agent_context_pack`, `main`
- **Doc summary:** AGENT-1A — Agent Context Pack Exporter (single pasteable bundle)
- **Smoke tests:** `dev\dev_smoke_agent_1a_context_pack.py`

### `AGENT\agent_2a_autonomous_loop.py`

- **Milestone:** `AGENT`
- **Option ID:** `AGENT-2A`
- **Exports (`__all__`):** `run_autonomous`
- **Doc summary:** AGENT-2A — Autonomous Execution Loop (orchestration only)
- **Smoke tests:** `dev\dev_smoke_agent_2a.py`

### `AGENT\agent_2b_scheduler.py`

- **Milestone:** `AGENT`
- **Option ID:** `AGENT-2B`
- **Exports (`__all__`):** `run_continuous`, `run_once_with_delay`
- **Doc summary:** AGENT-2B — Continuous / Scheduled Execution (timing + orchestration only)
- **Smoke tests:** `dev\dev_smoke_agent_2b.py`

### `AGENT\__init__.py`

- **Milestone:** `AGENT`
- **Option ID:** `AGENT-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `AUTH\auth_1a_form_login_guarded.py`

- **Milestone:** `AUTH`
- **Option ID:** `AUTH-1A`
- **Exports (`__all__`):** `ensure_logged_in`, `login`
- **Doc summary:** AUTH-1A — Standard username/password form login with guarded "already logged in" check.
- **Smoke tests:** `dev\dev_smoke_auth_1a.py`

### `AUTH\auth_1b_session_restore.py`

- **Milestone:** `AUTH`
- **Option ID:** `AUTH-1B`
- **Exports (`__all__`):** `session_paths`, `save_cookies`, `load_cookies`, `restore_or_login`
- **Doc summary:** AUTH-1B — Session Restore (cookies/local storage) + guarded fallback to AUTH-1A.
- **Smoke tests:** `dev\dev_smoke_auth_1b.py`

### `AUTH\__init__.py`

- **Milestone:** `AUTH`
- **Option ID:** `AUTH-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `base_app.py`

- **Milestone:** `BASE_APP.PY`
- **Option ID:** `BASE_APP.PY-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** app.py — Simplified Selenium RPA runner
- **Smoke tests:** _(none found)_

### `BUILD\build_1a_workflow_generator.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-1A`
- **Exports (`__all__`):** `generate_workflow`, `validate_spec`, `normalize_spec`, `suggest_missing_fields`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_build_1a.py`, `dev\dev_smoke_build_1a_workflow_grammar_gate_entrypoints.py`, `dev\dev_smoke_build_1b.py`

### `BUILD\build_1a_workflow_grammar_gate_entrypoints.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-1A`
- **Exports (`__all__`):** `get_workflow_grammar_gate_entrypoints`, `get_workflow_grammar_gate_console_scripts`
- **Doc summary:** BUILD-1A: workflow grammar gate entrypoints spec.
- **Smoke tests:** `dev\dev_smoke_build_1a.py`, `dev\dev_smoke_build_1a_workflow_grammar_gate_entrypoints.py`, `dev\dev_smoke_build_1b.py`

### `BUILD\build_1b_intake_questionnaire.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-1B`
- **Exports (`__all__`):** `default_questions`, `run_intake`, `build_spec_from_answers`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_build_1b.py`

### `BUILD\build_1c_action_normalizer.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-1C`
- **Exports (`__all__`):** `ACTION_ALIASES`, `normalize_action_name`, `normalize_step_actions`, `normalize_steps_actions`, `normalize_workflow_actions`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_build_1c.py`

### `BUILD\build_1c_smoke_stub_generator.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-1C`
- **Exports (`__all__`):** `generate_smoke_stub`, `load_workflow_metadata`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_build_1c.py`

### `BUILD\build_2a_nl_spec_generator.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-2A`
- **Exports (`__all__`):** `SUPPORTED_ACTIONS`, `nl_to_build_spec`, `validate_generated_steps`
- **Doc summary:** BUILD-2A — Natural Language → Build Spec Generator
- **Smoke tests:** `dev\dev_smoke_build_2a.py`

### `BUILD\build_2a_repeat_support.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-2A`
- **Exports (`__all__`):** `normalized_allowed_actions`, `normalize_and_filter_steps_keep_repeat`, `validate_steps_allow_repeat`, `dev_smoke`
- **Doc summary:** BUILD-2A — Repeat Support (Milestone 12.5.7)
- **Smoke tests:** `dev\dev_smoke_build_2a.py`

### `BUILD\build_2b_plan_optimizer.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-2B`
- **Exports (`__all__`):** `analyze_spec`, `apply_optimizations`, `optimize_spec`
- **Doc summary:** BUILD-2B — Workflow Plan Optimizer (pure transformation)
- **Smoke tests:** `dev\dev_smoke_build_2b.py`

### `BUILD\build_2c_full_bundle.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-2C`
- **Exports (`__all__`):** `build_from_nl`
- **Doc summary:** BUILD-2C — Full Automation Bundle Generator (orchestration only)
- **Smoke tests:** `dev\dev_smoke_build_2c.py`

### `BUILD\build_2d_determinism.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-2D`
- **Exports (`__all__`):** `canonicalize_for_json`, `stable_json_dumps`, `stable_fingerprint_sha256`, `dev_smoke`
- **Doc summary:** Deterministic canonicalization / serialization utilities.
- **Smoke tests:** `dev\dev_smoke_9_4_3_deterministic_generation.py`, `dev\dev_smoke_build_2d.py`

### `BUILD\build_2d_step_grammar_gate.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-2D`
- **Exports (`__all__`):** `ALLOWED_ACTIONS`, `GrammarViolation`, `find_unsupported_actions`, `assert_supported_actions`, `strip_unsupported_actions`
- **Doc summary:** BUILD-2D: Step grammar enforcement / gating.
- **Smoke tests:** `dev\dev_smoke_9_4_3_deterministic_generation.py`, `dev\dev_smoke_build_2d.py`

### `BUILD\build_2e_workflow_grammar_gate.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-2E`
- **Exports (`__all__`):** `WorkflowGateResult`, `find_workflow_unsupported_actions`, `assert_workflow_supported_actions`, `sanitize_workflow_steps`
- **Doc summary:** BUILD-2E: Workflow-level wrapper around BUILD-2D step grammar enforcement.
- **Smoke tests:** `dev\dev_smoke_build_2e.py`

### `BUILD\build_2f_workflow_file_grammar_gate.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-2F`
- **Exports (`__all__`):** `WorkflowFileGateResult`, `load_workflow_json_file`, `dump_workflow_json_text`, `gate_workflow_file_assert`, `gate_workflow_file_sanitize`
- **Doc summary:** BUILD-2F: File-level workflow grammar gating.
- **Smoke tests:** `dev\dev_smoke_build_2f.py`

### `BUILD\build_2g_workflow_tree_grammar_gate.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-2G`
- **Exports (`__all__`):** `WorkflowTreeGateResult`, `list_workflow_json_files`, `gate_workflow_tree_assert`, `gate_workflow_tree_sanitize`
- **Doc summary:** BUILD-2G: Directory/tree-level workflow grammar gating.
- **Smoke tests:** `dev\dev_smoke_build_2g.py`, `dev\dev_smoke_cli_1h_workflow_grammar_gate_pipeline.py`, `dev\dev_smoke_doctor_1a_workflow_grammar_gate.py`, `dev\dev_smoke_doctor_1b_workflow_grammar_gate.py`, `dev\dev_smoke_pipe_1a_workflow_grammar_gate_pipeline.py`, `dev\dev_smoke_report_1a_workflow_grammar_gate_report.py`, `dev\dev_smoke_report_1b_workflow_grammar_gate_report_text.py`

### `BUILD\build_3a_deploy_bundle_format.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-3A`
- **Exports (`__all__`):** `DEPLOY_BUNDLE_SCHEMA_ID`, `build_deploy_bundle_from_capture_bundle`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_build_3a_deploy_bundle_format.py`, `dev\dev_smoke_val_2a_deploy_bundle_validator.py`

### `BUILD\build_3b_bundle_fingerprint.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-3B`
- **Exports (`__all__`):** `DEFAULT_FINGERPRINT_DROP_TOP_LEVEL_KEYS`, `canonical_bytes_for_fingerprint`, `compute_sha256_hex`, `compute_bundle_fingerprint`, `stamp_bundle_version_and_fingerprint`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_build_3b_bundle_fingerprint.py`, `dev\dev_smoke_val_2a_deploy_bundle_validator.py`

### `BUILD\build_3c_deploy_bundle_builder.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-3C`
- **Exports (`__all__`):** `build_stamp_validate_deploy_bundle_1a`, `build_stamp_validate_deploy_bundle_1a_with_report`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_build_3c_deploy_bundle_builder.py`, `dev\dev_smoke_cli_1e_run_deploy_bundle.py`, `dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py`, `dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py`, `dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py`, `dev\dev_smoke_report_1e_deploy_bundle_validation_report_writer.py`, `dev\dev_smoke_run_1e_deploy_bundle_runner_adapter.py`, `dev\dev_smoke_workflow_1g_deploy_bundle_loader.py`

### `BUILD\build_3d_doc_index_artifact_bundler.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-3D`
- **Exports (`__all__`):** `write_doc_index_artifact_to_bundle_out_dir_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_build_3d_doc_index_artifact_bundler.py`, `dev\dev_smoke_doc_doc_index_entry_cli_1i_bundle_doc_index_and_manifest_cli.py`, `dev\dev_smoke_report_1e_build_manifest_artifact.py`

### `BUILD\build_3e_bundle_build_manifest_integrator.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-3E`
- **Exports (`__all__`):** `discover_bundle_artifact_rel_paths_1a`, `build_bundle_out_dir_doc_index_and_manifest_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_build_3e_bundle_build_manifest_integrator.py`

### `BUILD\build_3f_deploy_bundle_stamper.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-3F`
- **Exports (`__all__`):** `ensure_deploy_bundle_version_fingerprint_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `BUILD\build_3g_deploy_bundle_writer.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-3G`
- **Exports (`__all__`):** `dumps_deploy_bundle_1a_json`, `write_deploy_bundle_1a_to_path`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `BUILD\build_3h_capture_to_deploy_bundle_pipeline.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-3H`
- **Exports (`__all__`):** `load_json_mapping_from_path`, `build_write_deploy_bundle_1a_from_capture_bundle`, `build_write_deploy_bundle_1a_from_capture_bundle_path`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `BUILD\__init__.py`

- **Milestone:** `BUILD`
- **Option ID:** `BUILD-??`
- **Exports (`__all__`):** `generate_workflow`, `validate_spec`, `normalize_spec`, `suggest_missing_fields`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `CAPTURE\capture_1a_semi_auto.py`

- **Milestone:** `CAPTURE`
- **Option ID:** `CAPTURE-1A`
- **Exports (`__all__`):** `capture_session`
- **Doc summary:** CAPTURE-1A — Semi-Automatic Selector Capture (headed capture session)
- **Smoke tests:** `dev\dev_smoke_capture_1a.py`

### `CAPTURE\capture_1a_step_recorder.py`

- **Milestone:** `CAPTURE`
- **Option ID:** `CAPTURE-1A`
- **Exports (`__all__`):** `SUPPORTED_STEP_ACTIONS`, `Capture1AStepRecorder`, `event_to_schema_step`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_capture_1a.py`

### `CAPTURE\__init__.py`

- **Milestone:** `CAPTURE`
- **Option ID:** `CAPTURE-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `CLI\cli_1a_capture_to_deploy_bundle.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1A`
- **Exports (`__all__`):** `build_arg_parser_1a`, `main`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_cli_1a.py`, `dev\dev_smoke_cli_1a_workflow_grammar_gate.py`

### `CLI\cli_1a_run_pipeline.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1A`
- **Exports (`__all__`):** `run_pipeline`
- **Doc summary:** CLI-1A — Command Line Pipeline Runner.
- **Smoke tests:** `dev\dev_smoke_cli_1a.py`, `dev\dev_smoke_cli_1a_workflow_grammar_gate.py`

### `CLI\cli_1a_workflow_grammar_gate.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1A`
- **Exports (`__all__`):** `cli_workflow_grammar_gate`
- **Doc summary:** CLI-1A: Workflow grammar gate CLI.
- **Smoke tests:** `dev\dev_smoke_cli_1a.py`, `dev\dev_smoke_cli_1a_workflow_grammar_gate.py`

### `CLI\cli_pack_1a.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1A`
- **Exports (`__all__`):** `main`
- **Doc summary:** PACK-1A — Golden-Path CLI (one-command framework usage)
- **Smoke tests:** `dev\dev_smoke_cli_1a.py`, `dev\dev_smoke_cli_1a_workflow_grammar_gate.py`

### `CLI\cli_1b_capture_to_deploy_bundle.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1B`
- **Exports (`__all__`):** `build_arg_parser_1a`, `main`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_cli_1b.py`, `dev\dev_smoke_cli_1b_config_loader.py`

### `CLI\cli_1b_config_loader.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1B`
- **Exports (`__all__`):** `load_config`
- **Doc summary:** CLI-1B — Configuration Loader.
- **Smoke tests:** `dev\dev_smoke_cli_1b.py`, `dev\dev_smoke_cli_1b_config_loader.py`

### `CLI\cli_1c_args_overrides.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1C`
- **Exports (`__all__`):** `build_arg_parser`, `apply_overrides`
- **Doc summary:** CLI-1C — CLI Flags + Overrides
- **Smoke tests:** `dev\dev_smoke_cli_1c.py`

### `CLI\cli_1c_capture_to_deploy_bundle.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1C`
- **Exports (`__all__`):** `build_arg_parser_1a`, `main`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_cli_1c.py`

### `CLI\cli_1d_capture_to_deploy_bundle_auto.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1D`
- **Exports (`__all__`):** `discover_capture_bundle_1a_path`, `build_arg_parser_1d`, `main`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `CLI\cli_1e_deploy_bundle_info.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1E`
- **Exports (`__all__`):** `build_arg_parser_1e`, `summarize_deploy_bundle_1a`, `main`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_cli_1e_run_deploy_bundle.py`

### `CLI\cli_1e_run_deploy_bundle.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1E`
- **Exports (`__all__`):** `run_deploy_bundle_path_1a`, `build_arg_parser`, `main`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_cli_1e_run_deploy_bundle.py`

### `CLI\cli_1f_generate_reports.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1F`
- **Exports (`__all__`):** `build_arg_parser`, `run_cli_generate_reports`, `main`, `dev_smoke`
- **Doc summary:** CLI-1F — Generate reports for a run output directory (10.4.3)
- **Smoke tests:** `dev\dev_smoke_10_4_3_cli_generate_reports.py`, `dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py`

### `CLI\cli_1f_run_deploy_bundle_with_report.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1F`
- **Exports (`__all__`):** `run_deploy_bundle_path_1a_with_optional_validation_report`, `build_arg_parser`, `main`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_10_4_3_cli_generate_reports.py`, `dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py`

### `CLI\cli_1g_run_deploy_bundle_with_report_fail_fast.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1G`
- **Exports (`__all__`):** `build_arg_parser`, `main`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py`, `dev\dev_smoke_cli_1g_workflow_grammar_gate.py`

### `CLI\cli_1g_workflow_grammar_gate.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1G`
- **Exports (`__all__`):** `build_arg_parser`, `run_cli`, `main`
- **Doc summary:** CLI-1G: Workflow grammar gate CLI.
- **Smoke tests:** `dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py`, `dev\dev_smoke_cli_1g_workflow_grammar_gate.py`

### `CLI\cli_1h_run_deploy_bundle_cli_resolver.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1H`
- **Exports (`__all__`):** `resolve_latest_run_deploy_bundle_cli_module`, `resolve_latest_run_deploy_bundle_main`, `main`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py`, `dev\dev_smoke_cli_1h_workflow_grammar_gate_pipeline.py`

### `CLI\cli_1h_workflow_grammar_gate_pipeline.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1H`
- **Exports (`__all__`):** `build_arg_parser`, `cli_main`
- **Doc summary:** CLI-1H: Workflow grammar gate pipeline CLI.
- **Smoke tests:** `dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py`, `dev\dev_smoke_cli_1h_workflow_grammar_gate_pipeline.py`

### `CLI\cli_1i_build_doc_index_artifact.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1I`
- **Exports (`__all__`):** `build_arg_parser`, `build_doc_index_artifact_from_repo_1a`, `main`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_cli_1i_build_doc_index_artifact.py`, `dev\dev_smoke_cli_1i_bundle_doc_index_and_manifest_cli.py`

### `CLI\cli_1i_bundle_doc_index_and_manifest_cli.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-1I`
- **Exports (`__all__`):** `build_arg_parser_1a`, `run_cli_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_cli_1i_build_doc_index_artifact.py`, `dev\dev_smoke_cli_1i_bundle_doc_index_and_manifest_cli.py`

### `CLI\cli_2b_unified.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-2B`
- **Exports (`__all__`):** `main`
- **Doc summary:** CLI-2B — Unified Automation Command Interface (orchestration only)
- **Smoke tests:** `dev\dev_smoke_cli_2b.py`

### `CLI\__init__.py`

- **Milestone:** `CLI`
- **Option ID:** `CLI-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `DEPLOY\deploy_1a_service_runner.py`

- **Milestone:** `DEPLOY`
- **Option ID:** `DEPLOY-1A`
- **Exports (`__all__`):** `run_service`, `run_single_job`
- **Doc summary:** DEPLOY-1A — Runtime Service + Packaging (service runner)
- **Smoke tests:** `dev\dev_smoke_deploy_1a.py`

### `dev\dev_smoke_agent_1a_context_pack.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_auth_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_1a_workflow_grammar_gate_entrypoints.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_capture_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1a_workflow_grammar_gate.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_deploy_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_diff_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_diff_1a_capture_edit_diff.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_diff_1a_workflow_grammar_gate_report_diff.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_doc_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_doc_1a_library_index.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_doc_1a_workflow_grammar_gate.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_doctor_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_doctor_1a_workflow_grammar_gate.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_entry_1a_workflow_grammar_gate.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_guard_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_guard_1a_workflow_grammar_gate_guard.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_guard_1a_workflow_grammar_guard.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_heal_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_history_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_history_1a_workflow_grammar_gate_history.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_learn_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_lint_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_log_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_nav_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** Dev smoke test for NAV-1A Selenium helpers.
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_obs_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_out_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_pack_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_pipe_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** Dev smoke test for PIPE-1A run orchestrator.
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_pipe_1a_workflow_grammar_gate_pipeline.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_plan_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_reason_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_registry_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_replay_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_report_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_report_1a_workflow_grammar_gate_report.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_run_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_run_1a_workflow_grammar_gate.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_run_1a_workflow_grammar_gate_run.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_schema_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_selector_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_snap_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_snap_1a_workflow_capture.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_val_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_var_1a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_workflow_1a_loader.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_act_1b_logging.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** Dev smoke test for ACT-1B logging integration.
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_auth_1b.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_1b.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1b.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1b_config_loader.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_doctor_1b_workflow_grammar_gate.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_input_1b_excel_provider.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** Smoke test for top-level INPUT-1B shim: input_1b_excel_provider.py
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_learn_1b.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_log_1b.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_out_1b.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_pipe_1b.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** Dev smoke test — PIPE-1B (worklist configuration adapter)
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_report_1b_workflow_grammar_gate_report_text.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_snap_1b_selector_pack.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_val_1b.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_act_1c.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1C`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_1c.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1C`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1c.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1C`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_pipe_1c.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1C`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** Dev smoke test — PIPE-1C (steps loader + template substitution)
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_report_1c_workflow_grammar_gate_report_summary.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1C`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_snap_1c_capture_bundle.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1C`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_state_1c.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1C`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_pipe_1d_a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1D`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** Dev smoke test — PIPE-1D (step execution adapter)
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_snap_1d_bundle_io.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1D`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_state_1d.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1D`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1e_run_deploy_bundle.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1E`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_doc_1e_cli_run_deploy_bundle_cli_resolver_entry.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1E`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_pipe_1e.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1E`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_report_1e_build_manifest_artifact.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1E`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_report_1e_deploy_bundle_validation_report_writer.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1E`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_run_1e_deploy_bundle_runner_adapter.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1E`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_snap_1e_bundle_export.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1E`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_workflow_1e_steps_normalizer.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1E`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1F`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_doc_1f_doc_index_aggregator.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1F`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_snap_1f_materialize_selectors.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1F`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_workflow_1f_selector_ref_first.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1F`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1G`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1g_workflow_grammar_gate.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1G`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_doc_1g_doc_index_entry_contract.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1G`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_workflow_1g_deploy_bundle_loader.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1G`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1H`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1h_workflow_grammar_gate_pipeline.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1H`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_doc_1h_doc_index_collect_validate.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1H`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1i_build_doc_index_artifact.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1I`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_1i_bundle_doc_index_and_manifest_cli.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1I`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_doc_doc_index_entry_cli_1i_bundle_doc_index_and_manifest_cli.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-1I`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_agent_2a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_2a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_pipe_2a.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2A`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_val_2a_deploy_bundle_validator.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2A`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_workflow_workflow_2a_capture_actions_to_schema_steps.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2A`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_agent_2b.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_2b.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_cli_2b.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_pipe_2b.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2B`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_workflow_workflow_2b_capture_js_event_recorder.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2B`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_2c.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2C`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_pipe_2c.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2C`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_workflow_workflow_2c_capture_events_to_schema_steps_encoder.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2C`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_2d.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2D`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_pipe_2d.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2D`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_2e.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2E`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_pipe_2e.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2E`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** How to run:
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_2f.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2F`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_2g.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-2G`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_3a_deploy_bundle_format.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-3A`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_3b_bundle_fingerprint.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-3B`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_3c_deploy_bundle_builder.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-3C`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_3d_doc_index_artifact_bundler.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-3D`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_build_3e_bundle_build_manifest_integrator.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-3E`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_10_1_1_failure_capture.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_10_1_2_screenshot_capture.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_10_1_3_snapshot_persistence.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_10_2_1_run_manifest.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_10_2_2_step_outcomes.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_10_2_3_error_normalization.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_10_3_1_run_report.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_10_3_2_run_report_markdown.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_10_3_3_junit_xml.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_10_4_1_generate_reports.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_10_4_2_post_run_reporting.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_10_4_3_cli_generate_reports.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_1_1_slos_success_criteria.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_1_2_operator_runbooks.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_1_3_support_escalation_paths.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_2_1_versioning_policy.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_2_2_reviewable_diffs.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_2_3_promotion_gates.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_3_1_release_manifest.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_3_2_bundle_fingerprint.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_3_3_promotion_record.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_4_1_doctor_pre_run_checks.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_4_2_guard_prod_defaults.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_4_3_rollback_recovery_procedures.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_5_1_artifact_retention_policy.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_5_2_alerting_signals.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_5_3_audit_logging_replay_spec.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_5_4_replay_index_verifier.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_5_5_incident_packet_manifest.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_5_6_release_readiness_gate.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_5_7_evidence_bundle_assembler.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_6_1_prod_smoke_pipeline.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_6_2_rollback_rerun_determinism.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_12_6_3_operational_gates_enforcement.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_9_4_3_deterministic_generation.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_9_4_3_run_history_loader.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `main`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_act_action_engine.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** Dev smoke test for ACT-1A action engine.
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_act_download_wait.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** Dev smoke test for ACT download_wait integration.
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_entry_bootstrap.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** Smoke Test: ENTRY-1A webdriver bootstrap (Edge + Chrome)
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_go_to_google_search_for_something_click_result_then_go_back_and_search_again.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_go_to_google_search_for_weather_click_first_result.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_login_to_a_site_and_download_a_report.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_login_to_portal_and_export_report.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_open_a_slow_website_and_click_something_immediately.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_open_example_com_and_click_login_button_that_does_not_exist.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_open_example_com_click_login_and_verify_page_title.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_open_google_and_click_search.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_phase_11_5_1_capture_to_workflow_validity.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_phase_11_5_2_bundle_packaging_determinism.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_phase_11_5_3_deploy_run_path_minimal.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `dev\dev_smoke_state_input.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** Smoke test for:
- **Smoke tests:** _(none found)_

### `dev\sitecustomize.py`

- **Milestone:** `DEV`
- **Option ID:** `DEV-??`
- **Exports (`__all__`):** `ensure_repo_root_on_syspath`, `dev_smoke`
- **Doc summary:** Dev bootstrap: ensure repo root is on sys.path.
- **Smoke tests:** _(none found)_

### `DIFF\diff_12a_reviewable_diffs.py`

- **Milestone:** `DIFF`
- **Option ID:** `DIFF-12A`
- **Exports (`__all__`):** `DiffKind`, `DiffResult`, `read_text_file`, `normalize_newlines`, `canonicalize_text`, `unified_diff_text`, `diff_texts_reviewable`, `diff_files_reviewable`, `check_reviewable_diff_required`, `write_text_file`
- **Doc summary:** DIFF-12A: Reviewable Diffs (Milestone 12.2.2)
- **Smoke tests:** `dev\dev_smoke_12_2_2_reviewable_diffs.py`

### `DIFF\diff_1a_capture_edit_diff.py`

- **Milestone:** `DIFF`
- **Option ID:** `DIFF-1A`
- **Exports (`__all__`):** `canonical_json_dumps`, `compute_json_changes`, `render_unified_json_diff`, `diff_capture_edit`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_diff_1a.py`, `dev\dev_smoke_diff_1a_capture_edit_diff.py`, `dev\dev_smoke_diff_1a_workflow_grammar_gate_report_diff.py`

### `DIFF\diff_1a_config_changes.py`

- **Milestone:** `DIFF`
- **Option ID:** `DIFF-1A`
- **Exports (`__all__`):** `compute_fingerprint`, `write_fingerprint`, `diff_fingerprints`, `write_diff_report`
- **Doc summary:** DIFF-1A — Workflow & Selector Change Diff + Version Stamp
- **Smoke tests:** `dev\dev_smoke_diff_1a.py`, `dev\dev_smoke_diff_1a_capture_edit_diff.py`, `dev\dev_smoke_diff_1a_workflow_grammar_gate_report_diff.py`

### `DIFF\diff_1a_workflow_grammar_gate_report_diff.py`

- **Milestone:** `DIFF`
- **Option ID:** `DIFF-1A`
- **Exports (`__all__`):** `DIFF_SCHEMA_ID`, `diff_workflow_grammar_gate_reports`
- **Doc summary:** DIFF-1A: Workflow grammar gate report diff.
- **Smoke tests:** `dev\dev_smoke_diff_1a.py`, `dev\dev_smoke_diff_1a_capture_edit_diff.py`, `dev\dev_smoke_diff_1a_workflow_grammar_gate_report_diff.py`

### `DIFF\__init__.py`

- **Milestone:** `DIFF`
- **Option ID:** `DIFF-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `DOC\doc_12a_slos_success_criteria.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-12A`
- **Exports (`__all__`):** `SLO`, `SuccessCriterion`, `get_slos`, `get_success_criteria`, `render_slos_markdown`, `render_success_criteria_markdown`, `render_operational_standards_markdown`, `slos_to_json`, `success_criteria_to_json`, `write_text_file`, `write_operational_standards_markdown`
- **Doc summary:** DOC-12A: SLOs and Success Criteria (Milestone 12.1.1)
- **Smoke tests:** `dev\dev_smoke_12_1_1_slos_success_criteria.py`

### `DOC\doc_12b_operator_runbooks.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-12B`
- **Exports (`__all__`):** `RunbookStep`, `Runbook`, `get_operator_runbooks`, `render_runbooks_markdown`, `runbooks_to_json`, `write_text_file`, `write_operator_runbooks_markdown`
- **Doc summary:** DOC-12B: Operator Runbooks (Milestone 12.1.2)
- **Smoke tests:** `dev\dev_smoke_12_1_2_operator_runbooks.py`

### `DOC\doc_12c_support_escalation_paths.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-12C`
- **Exports (`__all__`):** `SupportRole`, `SeverityLevel`, `ResponseTarget`, `EscalationRule`, `IncidentTicketRequirements`, `get_support_roles`, `get_severity_levels`, `get_response_targets`, `get_escalation_matrix`, `get_incident_ticket_requirements`, `render_support_escalation_markdown`, `support_escalation_to_json`, `write_text_file`, `write_support_escalation_markdown`
- **Doc summary:** DOC-12C: Support and Escalation Paths (Milestone 12.1.3)
- **Smoke tests:** `dev\dev_smoke_12_1_3_support_escalation_paths.py`

### `DOC\doc_12d_rollback_recovery_procedures.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-12D`
- **Exports (`__all__`):** `PlaybookStep`, `Procedure`, `RollbackRecoveryPlaybook`, `get_rollback_recovery_playbook`, `validate_playbook`, `playbook_to_json`, `render_playbook_markdown`, `write_text_file`, `write_playbook_json`, `write_playbook_markdown`
- **Doc summary:** DOC-12D: Rollback and Recovery Procedures (Milestone 12.4.3)
- **Smoke tests:** `dev\dev_smoke_12_4_3_rollback_recovery_procedures.py`

### `DOC\doc_1a_library_index.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-1A`
- **Exports (`__all__`):** `generate_library_index`
- **Doc summary:** DOC-1A — Library Index Generator
- **Smoke tests:** `dev\dev_smoke_doc_1a.py`, `dev\dev_smoke_doc_1a_library_index.py`, `dev\dev_smoke_doc_1a_workflow_grammar_gate.py`

### `DOC\doc_1a_workflow_grammar_gate.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-1A`
- **Exports (`__all__`):** `build_workflow_grammar_gate_markdown`
- **Doc summary:** DOC-1A: Workflow grammar gate documentation builder.
- **Smoke tests:** `dev\dev_smoke_doc_1a.py`, `dev\dev_smoke_doc_1a_library_index.py`, `dev\dev_smoke_doc_1a_workflow_grammar_gate.py`

### `DOC\runbook_1a_generator.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-1A`
- **Exports (`__all__`):** `generate_runbook`
- **Doc summary:** RUNBOOK-1A — Operational Playbook Generator
- **Smoke tests:** `dev\dev_smoke_doc_1a.py`, `dev\dev_smoke_doc_1a_library_index.py`, `dev\dev_smoke_doc_1a_workflow_grammar_gate.py`

### `DOC\doc_1e_cli_run_deploy_bundle_cli_resolver_entry.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-1E`
- **Exports (`__all__`):** `DOC_INDEX_ENTRY_1A`, `get_doc_index_entry_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_doc_1e_cli_run_deploy_bundle_cli_resolver_entry.py`

### `DOC\doc_1f_doc_index_aggregator.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-1F`
- **Exports (`__all__`):** `iter_doc_module_names_in_dir_1a`, `load_doc_index_entry_from_module_1a`, `collect_doc_index_entries_1a`, `merge_doc_index_entries_1a`, `build_doc_index_artifact_1a`, `write_doc_index_artifact_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_doc_1f_doc_index_aggregator.py`, `dev\dev_smoke_doc_doc_index_entry_cli_1i_bundle_doc_index_and_manifest_cli.py`

### `DOC\doc_1g_doc_index_entry_contract.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-1G`
- **Exports (`__all__`):** `DOC_INDEX_ENTRY_KIND_1A`, `DOC_INDEX_LAYERS_1A`, `validate_doc_index_entry_1a`, `validate_doc_index_entries_1a`, `dev_smoke`
- **Doc summary:** DOC-1G — Doc Index Entry Contract (Validator)
- **Smoke tests:** `dev\dev_smoke_doc_1g_doc_index_entry_contract.py`

### `DOC\doc_1h_doc_index_collect_validate.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-1H`
- **Exports (`__all__`):** `format_doc_index_validation_errors_1a`, `collect_and_validate_doc_index_entries_1a`, `dev_smoke`
- **Doc summary:** DOC-1H — Doc Index Collect + Validate Wrapper
- **Smoke tests:** `dev\dev_smoke_doc_1h_doc_index_collect_validate.py`

### `DOC\doc_index_entry_cli_1i_bundle_doc_index_and_manifest_cli.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-1I`
- **Exports (`__all__`):** `DOC_INDEX_ENTRY_1A`, `DOC_INDEX_ENTRY`, `DOC_INDEX_ENTRIES_1A`, `DOC_INDEX_ENTRIES`, `get_doc_index_entries_1a`, `get_doc_index_entries`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_doc_doc_index_entry_cli_1i_bundle_doc_index_and_manifest_cli.py`

### `DOC\__init__.py`

- **Milestone:** `DOC`
- **Option ID:** `DOC-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `DOCTOR\doctor_12a_pre_run_checks.py`

- **Milestone:** `DOCTOR`
- **Option ID:** `DOCTOR-12A`
- **Exports (`__all__`):** `DoctorCheck`, `DoctorPolicy`, `DoctorDecision`, `get_doctor_policy`, `evaluate_doctor_policy`, `policy_to_json`, `render_policy_markdown`, `decision_to_json`, `render_decision_markdown`, `write_text_file`, `write_policy_json`, `write_policy_markdown`, `write_decision_json`, `write_decision_markdown`
- **Doc summary:** DOCTOR-12A: Pre-run DOCTOR Checks Policy (Milestone 12.4.1)
- **Smoke tests:** `dev\dev_smoke_12_4_1_doctor_pre_run_checks.py`

### `DOCTOR\doctor_12d_release_readiness_gate.py`

- **Milestone:** `DOCTOR`
- **Option ID:** `DOCTOR-12D`
- **Exports (`__all__`):** `CheckSpec`, `ReadinessPolicy`, `CheckObservation`, `CheckResult`, `ReadinessDecision`, `get_readiness_policy`, `validate_readiness_policy`, `evaluate_readiness`, `policy_to_json`, `render_policy_markdown`, `decision_to_json`, `render_decision_markdown`, `write_text_file`, `write_policy_json`, `write_policy_markdown`, `write_decision_json`, `write_decision_markdown`
- **Doc summary:** DOCTOR-12D: Release Readiness Gate (Milestone 12.5.6)
- **Smoke tests:** `dev\dev_smoke_12_5_6_release_readiness_gate.py`

### `DOCTOR\doctor_1a_check.py`

- **Milestone:** `DOCTOR`
- **Option ID:** `DOCTOR-1A`
- **Exports (`__all__`):** `run_preflight`, `format_preflight_report`
- **Doc summary:** DOCTOR-1A — Environment Self-Check (“preflight”)
- **Smoke tests:** `dev\dev_smoke_doctor_1a.py`, `dev\dev_smoke_doctor_1a_workflow_grammar_gate.py`

### `DOCTOR\doctor_1a_workflow_grammar_gate.py`

- **Milestone:** `DOCTOR`
- **Option ID:** `DOCTOR-1A`
- **Exports (`__all__`):** `DoctorWorkflowGrammarGateOutcome`, `doctor_check_workflow_grammar`, `doctor_fix_workflow_grammar`
- **Doc summary:** DOCTOR-1A: Workflow grammar gate (programmatic check/fix).
- **Smoke tests:** `dev\dev_smoke_doctor_1a.py`, `dev\dev_smoke_doctor_1a_workflow_grammar_gate.py`

### `DOCTOR\doctor_1b_workflow_grammar_gate.py`

- **Milestone:** `DOCTOR`
- **Option ID:** `DOCTOR-1B`
- **Exports (`__all__`):** `WorkflowGrammarGateDiagnosis`, `doctor_workflow_grammar_gate_diagnosis`
- **Doc summary:** DOCTOR-1B: Workflow grammar gate diagnosis (PIPE-backed).
- **Smoke tests:** `dev\dev_smoke_cli_1a_workflow_grammar_gate.py`, `dev\dev_smoke_diff_1a_workflow_grammar_gate_report_diff.py`, `dev\dev_smoke_doctor_1b_workflow_grammar_gate.py`, `dev\dev_smoke_guard_1a_workflow_grammar_gate_guard.py`, `dev\dev_smoke_history_1a_workflow_grammar_gate_history.py`, `dev\dev_smoke_report_1c_workflow_grammar_gate_report_summary.py`, `dev\dev_smoke_run_1a_workflow_grammar_gate_run.py`

### `DOCTOR\__init__.py`

- **Milestone:** `DOCTOR`
- **Option ID:** `DOCTOR-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `ENTRY\entry_1a_webdriver_bootstrap.py`

- **Milestone:** `ENTRY`
- **Option ID:** `ENTRY-1A`
- **Exports (`__all__`):** `parse_headless`, `default_download_dir`, `resolve_driver_path`, `make_driver`, `dev_smoke`
- **Doc summary:** ENTRY-1A — Standard headless-first webdriver bootstrap (Chrome/Edge configurable)
- **Smoke tests:** `dev\dev_smoke_act_1b_logging.py`, `dev\dev_smoke_act_action_engine.py`, `dev\dev_smoke_act_download_wait.py`, `dev\dev_smoke_entry_1a_workflow_grammar_gate.py`, `dev\dev_smoke_entry_bootstrap.py`, `dev\dev_smoke_nav_1a.py`

### `ENTRY\entry_1a_workflow_grammar_gate.py`

- **Milestone:** `ENTRY`
- **Option ID:** `ENTRY-1A`
- **Exports (`__all__`):** `main`
- **Doc summary:** ENTRY-1A: Workflow grammar gate entry point.
- **Smoke tests:** `dev\dev_smoke_act_1b_logging.py`, `dev\dev_smoke_act_action_engine.py`, `dev\dev_smoke_act_download_wait.py`, `dev\dev_smoke_entry_1a_workflow_grammar_gate.py`, `dev\dev_smoke_entry_bootstrap.py`, `dev\dev_smoke_nav_1a.py`

### `ENTRY\__init__.py`

- **Milestone:** `ENTRY`
- **Option ID:** `ENTRY-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `GUARD\guard_12a_prod_defaults.py`

- **Milestone:** `GUARD`
- **Option ID:** `GUARD-12A`
- **Exports (`__all__`):** `GuardProfile`, `GuardPolicy`, `GuardViolation`, `GuardDecision`, `get_guard_policy`, `evaluate_guard_policy`, `policy_to_json`, `render_policy_markdown`, `decision_to_json`, `render_decision_markdown`, `write_text_file`, `write_policy_json`, `write_policy_markdown`, `write_decision_json`, `write_decision_markdown`
- **Doc summary:** GUARD-12A: Production-default GUARD Policy (Milestone 12.4.2)
- **Smoke tests:** `dev\dev_smoke_12_4_2_guard_prod_defaults.py`

### `GUARD\guard_1a_runtime.py`

- **Milestone:** `GUARD`
- **Option ID:** `GUARD-1A`
- **Exports (`__all__`):** `wrap_step_runner`, `guarded_call`, `normalize_guard_cfg`
- **Doc summary:** GUARD-1A — Runtime Guardrails (stability layer)
- **Smoke tests:** `dev\dev_smoke_guard_1a.py`, `dev\dev_smoke_guard_1a_workflow_grammar_gate_guard.py`, `dev\dev_smoke_guard_1a_workflow_grammar_guard.py`

### `GUARD\guard_1a_workflow_grammar_gate_guard.py`

- **Milestone:** `GUARD`
- **Option ID:** `GUARD-1A`
- **Exports (`__all__`):** `WorkflowGrammarGateGuardDecision`, `guard_workflow_grammar_gate_report`
- **Doc summary:** GUARD-1A: Workflow grammar gate guard.
- **Smoke tests:** `dev\dev_smoke_guard_1a.py`, `dev\dev_smoke_guard_1a_workflow_grammar_gate_guard.py`, `dev\dev_smoke_guard_1a_workflow_grammar_guard.py`

### `GUARD\guard_1a_workflow_grammar_guard.py`

- **Milestone:** `GUARD`
- **Option ID:** `GUARD-1A`
- **Exports (`__all__`):** `GuardOnViolationMode`, `WorkflowGrammarGuardConfig`, `format_grammar_violations_summary`, `guard_workflow_dict_for_execution`, `guard_workflow_path_for_execution`
- **Doc summary:** GUARD-1A: Workflow grammar guard.
- **Smoke tests:** `dev\dev_smoke_guard_1a.py`, `dev\dev_smoke_guard_1a_workflow_grammar_gate_guard.py`, `dev\dev_smoke_guard_1a_workflow_grammar_guard.py`

### `GUARD\__init__.py`

- **Milestone:** `GUARD`
- **Option ID:** `GUARD-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `HEAL\heal_1a_patch_workflow.py`

- **Milestone:** `HEAL`
- **Option ID:** `HEAL-1A`
- **Exports (`__all__`):** `apply_diagnosis_patch`
- **Doc summary:** HEAL-1A — Auto-fix Suggestion Applier (workflow patch generator)
- **Smoke tests:** `dev\dev_smoke_heal_1a.py`

### `HEAL\__init__.py`

- **Milestone:** `HEAL`
- **Option ID:** `HEAL-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `HISTORY\history_12a_audit_logging_replay_spec.py`

- **Milestone:** `HISTORY`
- **Option ID:** `HISTORY-12A`
- **Exports (`__all__`):** `AuditLogSpec`, `AuditEvent`, `ReplayIndex`, `get_audit_log_spec`, `validate_audit_event`, `validate_replay_index`, `canonical_event_dict`, `event_to_canonical_json`, `events_to_jsonl`, `sha256_hex`, `build_replay_index`, `spec_to_json`, `render_spec_markdown`, `replay_index_to_json`, `render_replay_index_markdown`, `write_text_file`, `write_jsonl_file`
- **Doc summary:** HISTORY-12A: Audit-Friendly Logging + Replay Spec (Milestone 12.5.3)
- **Smoke tests:** `dev\dev_smoke_12_5_3_audit_logging_replay_spec.py`, `dev\dev_smoke_12_5_4_replay_index_verifier.py`

### `HISTORY\history_1a_run_manifest.py`

- **Milestone:** `HISTORY`
- **Option ID:** `HISTORY-1A`
- **Exports (`__all__`):** `build_run_manifest`, `write_run_manifest`, `dev_smoke`
- **Doc summary:** HISTORY-1A — Run manifest (10.2.1)
- **Smoke tests:** `dev\dev_smoke_10_2_1_run_manifest.py`, `dev\dev_smoke_cli_1a_workflow_grammar_gate.py`, `dev\dev_smoke_history_1a.py`, `dev\dev_smoke_history_1a_workflow_grammar_gate_history.py`, `dev\dev_smoke_run_1a_workflow_grammar_gate_run.py`

### `HISTORY\history_1a_store.py`

- **Milestone:** `HISTORY`
- **Option ID:** `HISTORY-1A`
- **Exports (`__all__`):** `sanitize_run_record`, `append_run_history`, `read_run_history`, `summarize_history`
- **Doc summary:** HISTORY-1A — Run History Store (append-only JSONL)
- **Smoke tests:** `dev\dev_smoke_10_2_1_run_manifest.py`, `dev\dev_smoke_cli_1a_workflow_grammar_gate.py`, `dev\dev_smoke_history_1a.py`, `dev\dev_smoke_history_1a_workflow_grammar_gate_history.py`, `dev\dev_smoke_run_1a_workflow_grammar_gate_run.py`

### `HISTORY\history_1a_workflow_grammar_gate_history.py`

- **Milestone:** `HISTORY`
- **Option ID:** `HISTORY-1A`
- **Exports (`__all__`):** `HISTORY_SCHEMA_ID`, `derive_run_id_workflow_grammar_gate`, `build_workflow_grammar_gate_history_record`, `append_workflow_grammar_gate_history_jsonl`, `read_workflow_grammar_gate_history_jsonl`
- **Doc summary:** HISTORY-1A: Workflow grammar gate history.
- **Smoke tests:** `dev\dev_smoke_10_2_1_run_manifest.py`, `dev\dev_smoke_cli_1a_workflow_grammar_gate.py`, `dev\dev_smoke_history_1a.py`, `dev\dev_smoke_history_1a_workflow_grammar_gate_history.py`, `dev\dev_smoke_run_1a_workflow_grammar_gate_run.py`

### `HISTORY\history_1b_step_outcomes.py`

- **Milestone:** `HISTORY`
- **Option ID:** `HISTORY-1B`
- **Exports (`__all__`):** `build_step_outcome`, `append_step_outcome`, `dev_smoke`
- **Doc summary:** HISTORY-1B — Step outcomes recorder (10.2.2)
- **Smoke tests:** `dev\dev_smoke_10_2_2_step_outcomes.py`

### `HISTORY\history_1c_error_normalization.py`

- **Milestone:** `HISTORY`
- **Option ID:** `HISTORY-1C`
- **Exports (`__all__`):** `normalize_exception`, `dev_smoke`
- **Doc summary:** HISTORY-1C — Error normalization (10.2.3)
- **Smoke tests:** `dev\dev_smoke_10_2_3_error_normalization.py`, `dev\dev_smoke_9_4_3_run_history_loader.py`

### `HISTORY\history_1c_run_history_loader.py`

- **Milestone:** `HISTORY`
- **Option ID:** `HISTORY-1C`
- **Exports (`__all__`):** `load_run_history`, `dev_smoke`
- **Doc summary:** HISTORY-1C — Run history loader (9.4.3)
- **Smoke tests:** `dev\dev_smoke_10_2_3_error_normalization.py`, `dev\dev_smoke_9_4_3_run_history_loader.py`

### `HISTORY\__init__.py`

- **Milestone:** `HISTORY`
- **Option ID:** `HISTORY-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `INPUT\input_1b_excel_provider.py`

- **Milestone:** `INPUT`
- **Option ID:** `INPUT-1B`
- **Exports (`__all__`):** `ExcelIdSpec`, `extract_ids_from_excel`, `load_worklist_ids`, `iter_worklist_ids`, `write_manifest_jsonl`, `build_manifest_from_excel`, `read_ids_from_excel`, `excel_to_ids`, `dev_smoke`
- **Doc summary:** INPUT-1B — Excel provider (sheet + column -> list of IDs) + optional manifest writer
- **Smoke tests:** `dev\dev_smoke_input_1b_excel_provider.py`

### `INPUT\__init__.py`

- **Milestone:** `INPUT`
- **Option ID:** `INPUT-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `LEARN\learn_1a_failure_patterns.py`

- **Milestone:** `LEARN`
- **Option ID:** `LEARN-1A`
- **Exports (`__all__`):** `load_history`, `extract_failure_patterns`, `rank_patterns`, `generate_recommendations`
- **Doc summary:** LEARN-1A — Failure Pattern Analytics (pure, deterministic)
- **Smoke tests:** `dev\dev_smoke_learn_1a.py`

### `LEARN\learn_1b_selector_intelligence.py`

- **Milestone:** `LEARN`
- **Option ID:** `LEARN-1B`
- **Exports (`__all__`):** `analyze_selector_stability`, `score_selector`, `generate_selector_recommendations`
- **Doc summary:** LEARN-1B — Selector Intelligence & Stability Scoring (pure analysis)
- **Smoke tests:** `dev\dev_smoke_learn_1b.py`

### `LEARN\__init__.py`

- **Milestone:** `LEARN`
- **Option ID:** `LEARN-??`
- **Exports (`__all__`):** `load_history`, `extract_failure_patterns`, `rank_patterns`, `generate_recommendations`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `LINT\lint_1a_steps_validator.py`

- **Milestone:** `LINT`
- **Option ID:** `LINT-1A`
- **Exports (`__all__`):** `load_steps_schema`, `validate_steps_data`, `validate_steps_file`, `format_report_text`
- **Doc summary:** LINT-1A — Step Validation Engine
- **Smoke tests:** `dev\dev_smoke_lint_1a.py`, `dev\dev_smoke_plan_1a.py`

### `LINT\__init__.py`

- **Milestone:** `LINT`
- **Option ID:** `LINT-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `LINT\lint_steps.py`

- **Milestone:** `LINT`
- **Option ID:** `LINT-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `LOG\log_1a_structured_logging.py`

- **Milestone:** `LOG`
- **Option ID:** `LOG-1A`
- **Exports (`__all__`):** `setup_logging`, `get_logger`, `bind_context`, `clear_context`, `redact`, `log_event`, `log_exception`
- **Doc summary:** LOG-1A — Standard structured logging + run_id + per-item context (stdlib only)
- **Smoke tests:** `dev\dev_smoke_act_1b_logging.py`, `dev\dev_smoke_log_1a.py`

### `LOG\log_1b_error_taxonomy.py`

- **Milestone:** `LOG`
- **Option ID:** `LOG-1B`
- **Exports (`__all__`):** `AUTH_ERROR`, `TIMEOUT`, `SELECTOR_NOT_FOUND`, `STALE_ELEMENT`, `CLICK_INTERCEPTED`, `JS_ERROR`, `DOWNLOAD_TIMEOUT`, `FILESYSTEM_ERROR`, `CONFIG_ERROR`, `UNKNOWN_ERROR`, `classify_exception`, `format_error_for_manifest`
- **Doc summary:** LOG-1B — Error Taxonomy + Exception Normalization.
- **Smoke tests:** `dev\dev_smoke_log_1b.py`, `dev\dev_smoke_pipe_2c.py`, `dev\dev_smoke_state_1d.py`

### `LOG\log_1b_logger_reset.py`

- **Milestone:** `LOG`
- **Option ID:** `LOG-1B`
- **Exports (`__all__`):** `reset_logger`, `setup_logging_force`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_log_1b.py`, `dev\dev_smoke_pipe_2c.py`, `dev\dev_smoke_state_1d.py`

### `LOG\__init__.py`

- **Milestone:** `LOG`
- **Option ID:** `LOG-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `LOOP\loop_1b_per_item.py`

- **Milestone:** `LOOP`
- **Option ID:** `LOOP-1B`
- **Exports (`__all__`):** `ItemOutcome`, `run_per_item_loop`, `iterate_items`
- **Doc summary:** LOOP-1B — Per-item loop (generic iterator over worklist)
- **Smoke tests:** _(none found)_

### `LOOP\__init__.py`

- **Milestone:** `LOOP`
- **Option ID:** `LOOP-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `NAV\nav_1a_selenium_helpers.py`

- **Milestone:** `NAV`
- **Option ID:** `NAV-1A`
- **Exports (`__all__`):** `wait_for_visible`, `wait_for_clickable`, `click`, `type_text`, `switch_to_frame`, `switch_to_default_content`, `wait_for_download`
- **Doc summary:** NAV-1A — Selenium navigation and interaction helpers (pure helpers, no logging)
- **Smoke tests:** `dev\dev_smoke_nav_1a.py`

### `NAV\__init__.py`

- **Milestone:** `NAV`
- **Option ID:** `NAV-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `OBS\obs_1a_run_timeline.py`

- **Milestone:** `OBS`
- **Option ID:** `OBS-1A`
- **Exports (`__all__`):** `create_run_timeline`, `record_step_event`, `finalize_timeline`
- **Doc summary:** OBS-1A — Run Observability Timeline
- **Smoke tests:** `dev\dev_smoke_obs_1a.py`

### `OBS\__init__.py`

- **Milestone:** `OBS`
- **Option ID:** `OBS-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `OUT\out_1a_download_wait.py`

- **Milestone:** `OUT`
- **Option ID:** `OUT-1A`
- **Exports (`__all__`):** `ensure_download_dir`, `wait_for_download`
- **Doc summary:** OUT-1A — Download wait/poll + directory management.
- **Smoke tests:** `dev\dev_smoke_out_1a.py`

### `OUT\out_1b_artifact_manager.py`

- **Milestone:** `OUT`
- **Option ID:** `OUT-1B`
- **Exports (`__all__`):** `ensure_dir`, `safe_slug`, `build_artifact_name`, `move_artifact`, `normalize_download`
- **Doc summary:** OUT-1B — Artifact Normalization (rename/move/archive, collision-safe).
- **Smoke tests:** `dev\dev_smoke_out_1b.py`

### `OUT\__init__.py`

- **Milestone:** `OUT`
- **Option ID:** `OUT-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `PIPE\pipe_1a_run_orchestrator.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-1A`
- **Exports (`__all__`):** `run_worklist`, `manifest_append`, `ManifestWriter`, `open_manifest`, `dev_smoke`
- **Doc summary:** PIPE-1A — End-to-end per-run orchestrator (glue module)
- **Smoke tests:** `dev\dev_smoke_pipe_1a.py`, `dev\dev_smoke_pipe_1a_workflow_grammar_gate_pipeline.py`, `dev\dev_smoke_pipe_1c.py`

### `PIPE\pipe_1a_workflow_grammar_gate_pipeline.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-1A`
- **Exports (`__all__`):** `PipelineMode`, `WorkflowGrammarGatePipelineResult`, `run_workflow_grammar_gate_pipeline`
- **Doc summary:** PIPE-1A: Workflow grammar gate pipeline runner.
- **Smoke tests:** `dev\dev_smoke_pipe_1a.py`, `dev\dev_smoke_pipe_1a_workflow_grammar_gate_pipeline.py`, `dev\dev_smoke_pipe_1c.py`

### `PIPE\pipe_1b_worklist_config.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-1B`
- **Exports (`__all__`):** `resolve_worklist_spec`, `load_ids`
- **Doc summary:** PIPE-1B — Worklist configuration adapter
- **Smoke tests:** `dev\dev_smoke_pipe_1b.py`

### `PIPE\pipe_1c_steps_loader.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-1C`
- **Exports (`__all__`):** `load_steps_file`, `render_steps`, `load_steps_from_cfg`
- **Doc summary:** PIPE-1C — Steps loader + template substitution (stdlib-only)
- **Smoke tests:** `dev\dev_smoke_pipe_1c.py`, `dev\dev_smoke_pipe_1d_a.py`

### `PIPE\pipe_1d_step_executor.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-1D`
- **Exports (`__all__`):** `execute_step`
- **Doc summary:** PIPE-1D — Step Execution Adapter
- **Smoke tests:** `dev\dev_smoke_pipe_1d_a.py`

### `PIPE\pipe_1e_runner.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-1E`
- **Exports (`__all__`):** `run_pipeline`, `exit_code_for_summary`, `main`
- **Doc summary:** PIPE-1E — Single runnable pipeline entrypoint.
- **Smoke tests:** `dev\dev_smoke_pipe_1e.py`

### `PIPE\pipe_1f_env_overrides.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-1F`
- **Exports (`__all__`):** `apply_env_overrides`, `dev_smoke`
- **Doc summary:** PIPE-1F: Environment overrides applied to cfg.
- **Smoke tests:** _(none found)_

### `PIPE\pipe_1g_env_force_overrides.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-1G`
- **Exports (`__all__`):** `apply_env_force_overrides`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `PIPE\pipe_1h_log_jsonl_path_policy.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-1H`
- **Exports (`__all__`):** `select_log_jsonl_path`, `maybe_cleanup_log_jsonl_path`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `PIPE\pipe_2a_var_aware_steps.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-2A`
- **Exports (`__all__`):** `render_step`, `render_cfg_inplace`, `execute_step_var_aware`, `execute_steps_var_aware`
- **Doc summary:** PIPE-2A — Variable-aware Step Execution (VAR-1A integration).
- **Smoke tests:** `dev\dev_smoke_pipe_2a.py`

### `PIPE\pipe_2b_step_blocks.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-2B`
- **Exports (`__all__`):** `run_steps`
- **Doc summary:** PIPE-2B — Step Blocks & Branching (if/else + try blocks).
- **Smoke tests:** `dev\dev_smoke_pipe_2b.py`, `dev\dev_smoke_pipe_2c.py`

### `PIPE\pipe_2c_error_plumbing.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-2C`
- **Exports (`__all__`):** `run_with_error_plumbing`
- **Doc summary:** PIPE-2C — Error Plumbing Integration (LOG-1B + LOG-1A + STATE).
- **Smoke tests:** `dev\dev_smoke_pipe_2c.py`

### `PIPE\pipe_2d_artifact_integration.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-2D`
- **Exports (`__all__`):** `handle_download_artifact`
- **Doc summary:** PIPE-2D — Artifact + Manifest Integration.
- **Smoke tests:** `dev\dev_smoke_pipe_2d.py`

### `PIPE\pipe_2e_run_summary.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-2E`
- **Exports (`__all__`):** `start_run_summary`, `record_item_success`, `record_item_failure`, `record_artifact`, `finish_run_summary`
- **Doc summary:** PIPE-2E — Run Summary + Metrics.
- **Smoke tests:** `dev\dev_smoke_pipe_2e.py`

### `PIPE\__init__.py`

- **Milestone:** `PIPE`
- **Option ID:** `PIPE-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `PLAN\plan_1a_step_planner.py`

- **Milestone:** `PLAN`
- **Option ID:** `PLAN-1A`
- **Exports (`__all__`):** `load_schema_and_examples`, `plan_from_intent`, `write_plan_outputs`, `generate_workflow_skeleton`, `main`
- **Doc summary:** PLAN-1A — Workflow Step Planner / Skeleton Generator
- **Smoke tests:** `dev\dev_smoke_plan_1a.py`

### `PLAN\__init__.py`

- **Milestone:** `PLAN`
- **Option ID:** `PLAN-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `REASON\reason_1a_diagnose.py`

- **Milestone:** `REASON`
- **Option ID:** `REASON-1A`
- **Exports (`__all__`):** `diagnose_failure`
- **Doc summary:** REASON-1A — Failure Diagnosis Engine (agent-friendly)
- **Smoke tests:** `dev\dev_smoke_reason_1a.py`

### `REASON\__init__.py`

- **Milestone:** `REASON`
- **Option ID:** `REASON-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `REGISTRY\reg_12a_versioning_policy.py`

- **Milestone:** `REGISTRY`
- **Option ID:** `REGISTRY-12A`
- **Exports (`__all__`):** `SemVer`, `ComponentPolicy`, `VersioningPolicy`, `parse_semver`, `is_valid_semver`, `compare_semver`, `bump_semver`, `get_versioning_policy`, `check_release_versions`, `render_versioning_policy_markdown`, `versioning_policy_to_json`, `write_text_file`, `write_versioning_policy_markdown`
- **Doc summary:** REG-12A: Versioning Policy (Milestone 12.2.1)
- **Smoke tests:** `dev\dev_smoke_12_2_1_versioning_policy.py`

### `REGISTRY\reg_12b_promotion_gates.py`

- **Milestone:** `REGISTRY`
- **Option ID:** `REGISTRY-12B`
- **Exports (`__all__`):** `Gate`, `PromotionPath`, `PromotionPolicy`, `PromotionDecision`, `get_promotion_policy`, `evaluate_promotion`, `render_promotion_policy_markdown`, `promotion_policy_to_json`, `write_text_file`, `write_promotion_policy_markdown`
- **Doc summary:** REG-12B: Promotion Gates Policy (Milestone 12.2.3)
- **Smoke tests:** `dev\dev_smoke_12_2_3_promotion_gates.py`, `dev\dev_smoke_12_3_3_promotion_record.py`

### `REGISTRY\registry_1a_generate.py`

- **Milestone:** `REGISTRY`
- **Option ID:** `REGISTRY-1A`
- **Exports (`__all__`):** `generate_action_registry`, `main`
- **Doc summary:** REGISTRY-1A — Action/Step Registry Export (AI Capability Handshake)
- **Smoke tests:** `dev\dev_smoke_registry_1a.py`

### `REGISTRY\__init__.py`

- **Milestone:** `REGISTRY`
- **Option ID:** `REGISTRY-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `REPLAY\replay_12a_index_verifier.py`

- **Milestone:** `REPLAY`
- **Option ID:** `REPLAY-12A`
- **Exports (`__all__`):** `ReplayMismatch`, `ReplayVerificationResult`, `parse_events_jsonl`, `events_to_canonical_hashes`, `verify_events_against_replay_index`, `result_to_json`, `render_result_markdown`, `write_text_file`
- **Doc summary:** REPLAY-12A: Replay Index Verifier (Milestone 12.5.4)
- **Smoke tests:** `dev\dev_smoke_12_5_4_replay_index_verifier.py`

### `REPLAY\replay_1a_run_replay.py`

- **Milestone:** `REPLAY`
- **Option ID:** `REPLAY-1A`
- **Exports (`__all__`):** `replay_run`
- **Doc summary:** REPLAY-1A — Deterministic Run Replayer
- **Smoke tests:** `dev\dev_smoke_replay_1a.py`

### `REPLAY\__init__.py`

- **Milestone:** `REPLAY`
- **Option ID:** `REPLAY-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `REPORT\report_12a_release_manifest.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-12A`
- **Exports (`__all__`):** `ArtifactRef`, `ManifestComponent`, `ReleaseManifest`, `read_bytes_file`, `sha256_bytes_hex`, `artifact_ref_from_path`, `build_release_manifest`, `manifest_to_json`, `render_manifest_markdown`, `write_text_file`, `write_manifest_json`, `write_manifest_markdown`
- **Doc summary:** REPORT-12A: Release Manifest (Milestone 12.3.1)
- **Smoke tests:** `dev\dev_smoke_12_3_1_release_manifest.py`, `dev\dev_smoke_12_3_2_bundle_fingerprint.py`, `dev\dev_smoke_12_3_3_promotion_record.py`

### `REPORT\report_12b_bundle_fingerprint.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-12B`
- **Exports (`__all__`):** `BundleFingerprint`, `canonical_fingerprint_input`, `compute_bundle_fingerprint`, `fingerprint_to_json`, `render_fingerprint_markdown`, `write_text_file`, `write_fingerprint_json`, `write_fingerprint_markdown`
- **Doc summary:** REPORT-12B: Bundle Fingerprint (Milestone 12.3.2)
- **Smoke tests:** `dev\dev_smoke_12_3_2_bundle_fingerprint.py`, `dev\dev_smoke_12_3_3_promotion_record.py`

### `REPORT\report_12c_promotion_record.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-12C`
- **Exports (`__all__`):** `PromotionRecord`, `normalize_evidence_for_json`, `redact_evidence`, `build_promotion_record`, `promotion_record_to_json`, `render_promotion_record_markdown`, `write_text_file`, `write_promotion_record_json`, `write_promotion_record_markdown`
- **Doc summary:** REPORT-12C: Promotion Record (Milestone 12.3.3)
- **Smoke tests:** `dev\dev_smoke_12_3_3_promotion_record.py`

### `REPORT\report_12d_artifact_retention_policy.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-12D`
- **Exports (`__all__`):** `RetentionRule`, `RetentionPolicy`, `ArtifactMeta`, `RetentionAction`, `RetentionDecision`, `get_retention_policy`, `validate_retention_policy`, `parse_date_iso`, `evaluate_retention_policy`, `policy_to_json`, `render_policy_markdown`, `decision_to_json`, `render_decision_markdown`, `write_text_file`, `write_policy_json`, `write_policy_markdown`, `write_decision_json`, `write_decision_markdown`
- **Doc summary:** REPORT-12D: Artifact Retention Policy (Milestone 12.5.1)
- **Smoke tests:** `dev\dev_smoke_12_5_1_artifact_retention_policy.py`

### `REPORT\report_12e_alerting_signals.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-12E`
- **Exports (`__all__`):** `SignalThresholds`, `AlertPolicy`, `TriggeredAlert`, `AlertDecision`, `get_alert_policy`, `validate_alert_policy`, `evaluate_alert_policy`, `policy_to_json`, `render_policy_markdown`, `decision_to_json`, `render_decision_markdown`, `write_text_file`, `write_policy_json`, `write_policy_markdown`, `write_decision_json`, `write_decision_markdown`
- **Doc summary:** REPORT-12E: Alerting Signals From Run Outcomes (Milestone 12.5.2)
- **Smoke tests:** `dev\dev_smoke_12_5_2_alerting_signals.py`

### `REPORT\report_12f_incident_packet_manifest.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-12F`
- **Exports (`__all__`):** `ArtifactRef`, `IncidentPacket`, `get_incident_packet_template`, `validate_incident_packet`, `canonical_packet_dict`, `packet_to_json`, `render_packet_markdown`, `sha256_hex`, `packet_fingerprint_sha256`, `write_text_file`, `write_packet_json`, `write_packet_markdown`
- **Doc summary:** REPORT-12F: Incident Packet Manifest (Milestone 12.5.5)
- **Smoke tests:** `dev\dev_smoke_12_5_5_incident_packet_manifest.py`

### `REPORT\report_12g_evidence_bundle_assembler.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-12G`
- **Exports (`__all__`):** `EVIDENCE_BUNDLE_SCHEMA_ID`, `canonical_json_dumps`, `sha256_hex_of_text`, `build_artifact_text_inventory`, `compute_bundle_fingerprint_sha256`, `assemble_evidence_bundle`, `render_evidence_bundle_markdown`, `validate_evidence_bundle_basic`
- **Doc summary:** report_12g_evidence_bundle_assembler.py
- **Smoke tests:** `dev\dev_smoke_12_5_7_evidence_bundle_assembler.py`, `dev\dev_smoke_12_6_1_prod_smoke_pipeline.py`, `dev\dev_smoke_12_6_2_rollback_rerun_determinism.py`, `dev\dev_smoke_12_6_3_operational_gates_enforcement.py`

### `REPORT\report_1a_generate.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-1A`
- **Exports (`__all__`):** `generate_report`
- **Doc summary:** REPORT-1A — Run Report Generator (HTML + JSON + MD)
- **Smoke tests:** `dev\dev_smoke_10_3_1_run_report.py`, `dev\dev_smoke_report_1a.py`, `dev\dev_smoke_report_1a_workflow_grammar_gate_report.py`, `dev\dev_smoke_report_1b_workflow_grammar_gate_report_text.py`

### `REPORT\report_1a_run_report.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-1A`
- **Exports (`__all__`):** `load_json_file`, `load_jsonl_file`, `build_run_report`, `write_run_report`, `dev_smoke`
- **Doc summary:** REPORT-1A — Run report aggregation (10.3.1)
- **Smoke tests:** `dev\dev_smoke_10_3_1_run_report.py`, `dev\dev_smoke_report_1a.py`, `dev\dev_smoke_report_1a_workflow_grammar_gate_report.py`, `dev\dev_smoke_report_1b_workflow_grammar_gate_report_text.py`

### `REPORT\report_1a_step_logs_from_jsonl.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-1A`
- **Exports (`__all__`):** `build_step_logs_from_jsonl`, `dev_smoke`
- **Doc summary:** REPORT-1A — Build step_logs from LOG JSONL events.
- **Smoke tests:** `dev\dev_smoke_10_3_1_run_report.py`, `dev\dev_smoke_report_1a.py`, `dev\dev_smoke_report_1a_workflow_grammar_gate_report.py`, `dev\dev_smoke_report_1b_workflow_grammar_gate_report_text.py`

### `REPORT\report_1a_workflow_grammar_gate_report.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-1A`
- **Exports (`__all__`):** `build_grammar_gate_report`, `dump_grammar_gate_report_json_text`
- **Doc summary:** REPORT-1A: Workflow grammar gate reporting.
- **Smoke tests:** `dev\dev_smoke_10_3_1_run_report.py`, `dev\dev_smoke_report_1a.py`, `dev\dev_smoke_report_1a_workflow_grammar_gate_report.py`, `dev\dev_smoke_report_1b_workflow_grammar_gate_report_text.py`

### `REPORT\report_1b_run_report_markdown.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-1B`
- **Exports (`__all__`):** `build_run_report_markdown`, `write_run_report_markdown`, `dev_smoke`
- **Doc summary:** REPORT-1B — Run report markdown renderer (10.3.2)
- **Smoke tests:** `dev\dev_smoke_10_3_2_run_report_markdown.py`, `dev\dev_smoke_report_1b_workflow_grammar_gate_report_text.py`

### `REPORT\report_1b_workflow_grammar_gate_report_text.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-1B`
- **Exports (`__all__`):** `format_grammar_gate_report_text`
- **Doc summary:** REPORT-1B: Deterministic text rendering for workflow grammar gate reports.
- **Smoke tests:** `dev\dev_smoke_10_3_2_run_report_markdown.py`, `dev\dev_smoke_report_1b_workflow_grammar_gate_report_text.py`

### `REPORT\report_1c_junit_xml.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-1C`
- **Exports (`__all__`):** `build_junit_xml`, `write_junit_xml`, `dev_smoke`
- **Doc summary:** REPORT-1C — JUnit XML renderer (10.3.3)
- **Smoke tests:** `dev\dev_smoke_10_3_3_junit_xml.py`, `dev\dev_smoke_report_1c_workflow_grammar_gate_report_summary.py`

### `REPORT\report_1c_workflow_grammar_gate_report_summary.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-1C`
- **Exports (`__all__`):** `build_grammar_gate_report_summary`, `format_grammar_gate_summary_line`
- **Doc summary:** REPORT-1C: Workflow grammar gate report summary.
- **Smoke tests:** `dev\dev_smoke_10_3_3_junit_xml.py`, `dev\dev_smoke_report_1c_workflow_grammar_gate_report_summary.py`

### `REPORT\report_1d_generate_reports.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-1D`
- **Exports (`__all__`):** `generate_standard_reports`, `dev_smoke`
- **Doc summary:** REPORT-1D — Generate standard report artifacts (10.4.1)
- **Smoke tests:** `dev\dev_smoke_10_4_1_generate_reports.py`

### `REPORT\report_1e_build_manifest_artifact.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-1E`
- **Exports (`__all__`):** `sha256_file_1a`, `build_build_manifest_artifact_1a`, `write_build_manifest_artifact_1a`, `build_and_write_build_manifest_for_bundle_out_dir_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py`, `dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py`, `dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py`, `dev\dev_smoke_report_1e_build_manifest_artifact.py`, `dev\dev_smoke_report_1e_deploy_bundle_validation_report_writer.py`

### `REPORT\report_1e_deploy_bundle_validation_report_writer.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-1E`
- **Exports (`__all__`):** `derive_deploy_bundle_validation_report_path_1a`, `build_deploy_bundle_validation_report_1a`, `write_deploy_bundle_validation_report_1a`, `write_deploy_bundle_validation_report_alongside_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py`, `dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py`, `dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py`, `dev\dev_smoke_report_1e_build_manifest_artifact.py`, `dev\dev_smoke_report_1e_deploy_bundle_validation_report_writer.py`

### `REPORT\__init__.py`

- **Milestone:** `REPORT`
- **Option ID:** `REPORT-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `RUN\run_12a_prod_smoke_pipeline.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-12A`
- **Exports (`__all__`):** `PROD_SMOKE_PIPELINE_SCHEMA_ID`, `ALLOWED_WORKFLOW_ACTIONS`, `build_minimal_smoke_workflow_bundle`, `validate_workflow_allowed_actions`, `assemble_prod_smoke_pipeline_report`, `render_prod_smoke_pipeline_report_markdown`, `validate_prod_smoke_pipeline_report_basic`, `compute_prod_smoke_pipeline_report_fingerprint_sha256`
- **Doc summary:** run_12a_prod_smoke_pipeline.py
- **Smoke tests:** `dev\dev_smoke_12_6_1_prod_smoke_pipeline.py`

### `RUN\run_12b_rollback_rerun_determinism.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-12B`
- **Exports (`__all__`):** `ROLLBACK_RERUN_SCHEMA_ID`, `build_versioned_workflow_bundle`, `assemble_deployment_record`, `assemble_run_record`, `assemble_rollback_record`, `assemble_rollback_rerun_determinism_report`, `render_rollback_rerun_determinism_report_markdown`, `validate_rollback_rerun_determinism_report_basic`
- **Doc summary:** run_12b_rollback_rerun_determinism.py
- **Smoke tests:** `dev\dev_smoke_12_6_2_rollback_rerun_determinism.py`

### `RUN\run_12c_operational_gates_enforcement.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-12C`
- **Exports (`__all__`):** `OP_GATES_ENFORCEMENT_SCHEMA_ID`, `GateInvocationError`, `assemble_operational_gates_enforcement_report`, `render_operational_gates_enforcement_report_markdown`, `validate_operational_gates_enforcement_report_basic`
- **Doc summary:** run_12c_operational_gates_enforcement.py
- **Smoke tests:** `dev\dev_smoke_12_6_3_operational_gates_enforcement.py`

### `RUN\run_1a_workflow_grammar_gate.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-1A`
- **Exports (`__all__`):** `RunWorkflowGateOutcome`, `gate_workflow_dict_for_run`, `gate_workflow_path_for_run`
- **Doc summary:** RUN-1A: Pre-run workflow grammar gate.
- **Smoke tests:** `dev\dev_smoke_run_1a.py`, `dev\dev_smoke_run_1a_workflow_grammar_gate.py`, `dev\dev_smoke_run_1a_workflow_grammar_gate_run.py`

### `RUN\run_1a_workflow_grammar_gate_run.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-1A`
- **Exports (`__all__`):** `WorkflowGrammarGateRunResult`, `run_workflow_grammar_gate`
- **Doc summary:** RUN-1A: Workflow grammar gate run orchestration.
- **Smoke tests:** `dev\dev_smoke_run_1a.py`, `dev\dev_smoke_run_1a_workflow_grammar_gate.py`, `dev\dev_smoke_run_1a_workflow_grammar_gate_run.py`

### `RUN\run_1a_workflow_runner.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-1A`
- **Exports (`__all__`):** `run_workflow`
- **Doc summary:** RUN-1A — Unified Workflow Runner
- **Smoke tests:** `dev\dev_smoke_run_1a.py`, `dev\dev_smoke_run_1a_workflow_grammar_gate.py`, `dev\dev_smoke_run_1a_workflow_grammar_gate_run.py`

### `RUN\run_1b_workflow_runner_with_snap.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-1B`
- **Exports (`__all__`):** `run_workflow_with_snap`
- **Doc summary:** Thin wrapper around RUN-1A runner to capture SNAP-1A artifacts on failure.
- **Smoke tests:** _(none found)_

### `RUN\run_1c_workflow_runner_with_guard.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-1C`
- **Exports (`__all__`):** `run_workflow_with_guard`
- **Doc summary:** RUN-1C — Wrapper to enable GUARD-1A without refactoring RUN-1A.
- **Smoke tests:** _(none found)_

### `RUN\run_1d_runner_with_history.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-1D`
- **Exports (`__all__`):** `run_workflow_with_history`
- **Doc summary:** RUN-1D — Wrapper to append HISTORY-1A records after running RUN-1A / REPORT-1A.
- **Smoke tests:** _(none found)_

### `RUN\run_1e_deploy_bundle_runner_adapter.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-1E`
- **Exports (`__all__`):** `resolve_default_workflow_runner_callable`, `run_deploy_bundle_1a`, `run_deploy_bundle_1a_with_meta`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_10_4_2_post_run_reporting.py`, `dev\dev_smoke_run_1e_deploy_bundle_runner_adapter.py`

### `RUN\run_1e_post_run_reporting.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-1E`
- **Exports (`__all__`):** `maybe_generate_post_run_reports`, `dev_smoke`
- **Doc summary:** RUN-1E — Post-run reporting hook (10.4.2)
- **Smoke tests:** `dev\dev_smoke_10_4_2_post_run_reporting.py`, `dev\dev_smoke_run_1e_deploy_bundle_runner_adapter.py`

### `RUN\__init__.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `RUN\dev_run_workflow.py`

- **Milestone:** `RUN`
- **Option ID:** `RUN-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `SCHEMA\schema_1a_generate.py`

- **Milestone:** `SCHEMA`
- **Option ID:** `SCHEMA-1A`
- **Exports (`__all__`):** `generate_steps_schema`, `main`
- **Doc summary:** SCHEMA-1A — Step/Action Schema Export (AI-friendly)
- **Smoke tests:** `dev\dev_smoke_schema_1a.py`

### `SCHEMA\__init__.py`

- **Milestone:** `SCHEMA`
- **Option ID:** `SCHEMA-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `SELECTOR\selector_1a_registry.py`

- **Milestone:** `SELECTOR`
- **Option ID:** `SELECTOR-1A`
- **Exports (`__all__`):** `load_selectors`, `get_selector`, `resolve_selector`
- **Doc summary:** SELECTOR-1A — Selector Registry / Resolver
- **Smoke tests:** `dev\dev_smoke_capture_1a.py`, `dev\dev_smoke_selector_1a.py`

### `SELECTOR\__init__.py`

- **Milestone:** `SELECTOR`
- **Option ID:** `SELECTOR-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `SNAP\snap_1a_capture.py`

- **Milestone:** `SNAP`
- **Option ID:** `SNAP-1A`
- **Exports (`__all__`):** `capture_failure_artifacts`
- **Doc summary:** SNAP-1A — Evidence Capture on Failure (artifacts bundle)
- **Smoke tests:** `dev\dev_smoke_10_1_1_failure_capture.py`, `dev\dev_smoke_build_3a_deploy_bundle_format.py`, `dev\dev_smoke_build_3c_deploy_bundle_builder.py`, `dev\dev_smoke_cli_1e_run_deploy_bundle.py`, `dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py`, `dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py`, `dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py`, `dev\dev_smoke_phase_11_5_1_capture_to_workflow_validity.py`, `dev\dev_smoke_phase_11_5_2_bundle_packaging_determinism.py`, `dev\dev_smoke_phase_11_5_3_deploy_run_path_minimal.py`, `dev\dev_smoke_report_1e_deploy_bundle_validation_report_writer.py`, `dev\dev_smoke_run_1e_deploy_bundle_runner_adapter.py`, `dev\dev_smoke_snap_1a.py`, `dev\dev_smoke_snap_1a_workflow_capture.py`, `dev\dev_smoke_snap_1b_selector_pack.py`, `dev\dev_smoke_snap_1c_capture_bundle.py`, `dev\dev_smoke_snap_1d_bundle_io.py`, `dev\dev_smoke_snap_1e_bundle_export.py`, `dev\dev_smoke_snap_1f_materialize_selectors.py`, `dev\dev_smoke_val_2a_deploy_bundle_validator.py`, `dev\dev_smoke_workflow_1g_deploy_bundle_loader.py`

### `SNAP\snap_1a_failure_capture.py`

- **Milestone:** `SNAP`
- **Option ID:** `SNAP-1A`
- **Exports (`__all__`):** `capture_failure_snapshot`, `dev_smoke`
- **Doc summary:** SNAP-1A — Failure capture (10.1.1)
- **Smoke tests:** `dev\dev_smoke_10_1_1_failure_capture.py`, `dev\dev_smoke_build_3a_deploy_bundle_format.py`, `dev\dev_smoke_build_3c_deploy_bundle_builder.py`, `dev\dev_smoke_cli_1e_run_deploy_bundle.py`, `dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py`, `dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py`, `dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py`, `dev\dev_smoke_phase_11_5_1_capture_to_workflow_validity.py`, `dev\dev_smoke_phase_11_5_2_bundle_packaging_determinism.py`, `dev\dev_smoke_phase_11_5_3_deploy_run_path_minimal.py`, `dev\dev_smoke_report_1e_deploy_bundle_validation_report_writer.py`, `dev\dev_smoke_run_1e_deploy_bundle_runner_adapter.py`, `dev\dev_smoke_snap_1a.py`, `dev\dev_smoke_snap_1a_workflow_capture.py`, `dev\dev_smoke_snap_1b_selector_pack.py`, `dev\dev_smoke_snap_1c_capture_bundle.py`, `dev\dev_smoke_snap_1d_bundle_io.py`, `dev\dev_smoke_snap_1e_bundle_export.py`, `dev\dev_smoke_snap_1f_materialize_selectors.py`, `dev\dev_smoke_val_2a_deploy_bundle_validator.py`, `dev\dev_smoke_workflow_1g_deploy_bundle_loader.py`

### `SNAP\snap_1a_workflow_capture.py`

- **Milestone:** `SNAP`
- **Option ID:** `SNAP-1A`
- **Exports (`__all__`):** `ALLOWED_WORKFLOW_ACTIONS`, `CapturedEvent`, `capture_install_js`, `install_capture_listeners`, `fetch_captured_events`, `captured_events_to_steps`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_10_1_1_failure_capture.py`, `dev\dev_smoke_build_3a_deploy_bundle_format.py`, `dev\dev_smoke_build_3c_deploy_bundle_builder.py`, `dev\dev_smoke_cli_1e_run_deploy_bundle.py`, `dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py`, `dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py`, `dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py`, `dev\dev_smoke_phase_11_5_1_capture_to_workflow_validity.py`, `dev\dev_smoke_phase_11_5_2_bundle_packaging_determinism.py`, `dev\dev_smoke_phase_11_5_3_deploy_run_path_minimal.py`, `dev\dev_smoke_report_1e_deploy_bundle_validation_report_writer.py`, `dev\dev_smoke_run_1e_deploy_bundle_runner_adapter.py`, `dev\dev_smoke_snap_1a.py`, `dev\dev_smoke_snap_1a_workflow_capture.py`, `dev\dev_smoke_snap_1b_selector_pack.py`, `dev\dev_smoke_snap_1c_capture_bundle.py`, `dev\dev_smoke_snap_1d_bundle_io.py`, `dev\dev_smoke_snap_1e_bundle_export.py`, `dev\dev_smoke_snap_1f_materialize_selectors.py`, `dev\dev_smoke_val_2a_deploy_bundle_validator.py`, `dev\dev_smoke_workflow_1g_deploy_bundle_loader.py`

### `SNAP\snap_1b_screenshot_capture.py`

- **Milestone:** `SNAP`
- **Option ID:** `SNAP-1B`
- **Exports (`__all__`):** `capture_screenshot_png_bytes`, `capture_screenshot_b64`, `capture_screenshot_payload`, `dev_smoke`
- **Doc summary:** SNAP-1B — Screenshot capture (10.1.2)
- **Smoke tests:** `dev\dev_smoke_10_1_2_screenshot_capture.py`, `dev\dev_smoke_phase_11_5_1_capture_to_workflow_validity.py`, `dev\dev_smoke_phase_11_5_2_bundle_packaging_determinism.py`, `dev\dev_smoke_phase_11_5_3_deploy_run_path_minimal.py`, `dev\dev_smoke_snap_1b_selector_pack.py`

### `SNAP\snap_1b_selector_pack.py`

- **Milestone:** `SNAP`
- **Option ID:** `SNAP-1B`
- **Exports (`__all__`):** `SELECTOR_PACK_SCHEMA_ID`, `selectors_from_captured_events`, `build_selector_ref_map`, `build_selector_pack`, `selector_pack_from_captured_events`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_10_1_2_screenshot_capture.py`, `dev\dev_smoke_phase_11_5_1_capture_to_workflow_validity.py`, `dev\dev_smoke_phase_11_5_2_bundle_packaging_determinism.py`, `dev\dev_smoke_phase_11_5_3_deploy_run_path_minimal.py`, `dev\dev_smoke_snap_1b_selector_pack.py`

### `SNAP\snap_1c_capture_bundle.py`

- **Milestone:** `SNAP`
- **Option ID:** `SNAP-1C`
- **Exports (`__all__`):** `CAPTURE_BUNDLE_SCHEMA_ID`, `emit_capture_bundle`, `build_capture_bundle_from_events`, `validate_capture_bundle`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_10_1_3_snapshot_persistence.py`, `dev\dev_smoke_build_3a_deploy_bundle_format.py`, `dev\dev_smoke_build_3c_deploy_bundle_builder.py`, `dev\dev_smoke_cli_1e_run_deploy_bundle.py`, `dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py`, `dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py`, `dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py`, `dev\dev_smoke_report_1e_deploy_bundle_validation_report_writer.py`, `dev\dev_smoke_run_1e_deploy_bundle_runner_adapter.py`, `dev\dev_smoke_snap_1c_capture_bundle.py`, `dev\dev_smoke_snap_1d_bundle_io.py`, `dev\dev_smoke_snap_1e_bundle_export.py`, `dev\dev_smoke_snap_1f_materialize_selectors.py`, `dev\dev_smoke_val_2a_deploy_bundle_validator.py`, `dev\dev_smoke_workflow_1g_deploy_bundle_loader.py`

### `SNAP\snap_1c_persist_artifacts.py`

- **Milestone:** `SNAP`
- **Option ID:** `SNAP-1C`
- **Exports (`__all__`):** `persist_snapshot_artifacts`, `dev_smoke`
- **Doc summary:** SNAP-1C — Persist snapshot artifacts deterministically (10.1.3)
- **Smoke tests:** `dev\dev_smoke_10_1_3_snapshot_persistence.py`, `dev\dev_smoke_build_3a_deploy_bundle_format.py`, `dev\dev_smoke_build_3c_deploy_bundle_builder.py`, `dev\dev_smoke_cli_1e_run_deploy_bundle.py`, `dev\dev_smoke_cli_1f_run_deploy_bundle_with_report.py`, `dev\dev_smoke_cli_1g_run_deploy_bundle_with_report_fail_fast.py`, `dev\dev_smoke_cli_1h_run_deploy_bundle_cli_resolver.py`, `dev\dev_smoke_report_1e_deploy_bundle_validation_report_writer.py`, `dev\dev_smoke_run_1e_deploy_bundle_runner_adapter.py`, `dev\dev_smoke_snap_1c_capture_bundle.py`, `dev\dev_smoke_snap_1d_bundle_io.py`, `dev\dev_smoke_snap_1e_bundle_export.py`, `dev\dev_smoke_snap_1f_materialize_selectors.py`, `dev\dev_smoke_val_2a_deploy_bundle_validator.py`, `dev\dev_smoke_workflow_1g_deploy_bundle_loader.py`

### `SNAP\snap_1d_bundle_io.py`

- **Milestone:** `SNAP`
- **Option ID:** `SNAP-1D`
- **Exports (`__all__`):** `capture_bundle_to_json`, `capture_bundle_from_json`, `save_capture_bundle_json`, `load_capture_bundle_json`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_snap_1d_bundle_io.py`, `dev\dev_smoke_snap_1e_bundle_export.py`

### `SNAP\snap_1e_bundle_export.py`

- **Milestone:** `SNAP`
- **Option ID:** `SNAP-1E`
- **Exports (`__all__`):** `export_capture_bundle_assets`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_snap_1e_bundle_export.py`

### `SNAP\snap_1f_materialize_selectors.py`

- **Milestone:** `SNAP`
- **Option ID:** `SNAP-1F`
- **Exports (`__all__`):** `selector_pack_ref_to_selector`, `materialize_selector_refs_in_steps`, `materialize_selector_refs_in_bundle`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_snap_1f_materialize_selectors.py`

### `SNAP\__init__.py`

- **Milestone:** `SNAP`
- **Option ID:** `SNAP-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `STATE\state_1b_manifest_jsonl.py`

- **Milestone:** `STATE`
- **Option ID:** `STATE-1B`
- **Exports (`__all__`):** `utc_ts`, `append_jsonl_line`, `write_audit`, `load_ids_from_manifest`, `choose_active_manifest`, `manifest_append`, `ManifestWriter`, `open_manifest`
- **Doc summary:** STATE-1B — JSONL manifest state (queued/success/fail + metadata) — stdlib-only
- **Smoke tests:** `dev\dev_smoke_state_input.py`

### `STATE\state_1c_retry_helpers.py`

- **Milestone:** `STATE`
- **Option ID:** `STATE-1C`
- **Exports (`__all__`):** `read_manifest_rows`, `extract_failed_ids`, `write_retry_manifest`
- **Doc summary:** STATE-1C — Retry / Resume helpers (additive to STATE-1B).
- **Smoke tests:** `dev\dev_smoke_state_1c.py`

### `STATE\state_1d_manifest_row_helpers.py`

- **Milestone:** `STATE`
- **Option ID:** `STATE-1D`
- **Exports (`__all__`):** `now_utc_ts`, `build_row_base`, `row_queued`, `row_success`, `row_failure`, `write_row`
- **Doc summary:** STATE-1D — Manifest Row Helpers (standardize queued/success/fail shapes).
- **Smoke tests:** `dev\dev_smoke_state_1d.py`

### `STATE\__init__.py`

- **Milestone:** `STATE`
- **Option ID:** `STATE-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `VAL\val_1a_ui_state.py`

- **Milestone:** `VAL`
- **Option ID:** `VAL-1A`
- **Exports (`__all__`):** `validate_ui_state`
- **Doc summary:** VAL-1A — UI state validation via selector presence + text checks.
- **Smoke tests:** `dev\dev_smoke_val_1a.py`

### `VAL\val_1b_download_validation.py`

- **Milestone:** `VAL`
- **Option ID:** `VAL-1B`
- **Exports (`__all__`):** `validate_download`
- **Doc summary:** VAL-1B — Download validation (file exists, size > 0, optional name patterns).
- **Smoke tests:** `dev\dev_smoke_val_1b.py`

### `VAL\val_2a_deploy_bundle_validator.py`

- **Milestone:** `VAL`
- **Option ID:** `VAL-2A`
- **Exports (`__all__`):** `ValidationIssue`, `validate_deploy_bundle_1a`, `assert_deploy_bundle_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_val_2a_deploy_bundle_validator.py`

### `VAL\__init__.py`

- **Milestone:** `VAL`
- **Option ID:** `VAL-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `VAR\var_1a_runtime_store.py`

- **Milestone:** `VAR`
- **Option ID:** `VAR-1A`
- **Exports (`__all__`):** `get_var`, `set_var`, `render_vars`
- **Doc summary:** VAR-1A — Runtime Variable Store.
- **Smoke tests:** `dev\dev_smoke_pipe_2a.py`, `dev\dev_smoke_pipe_2b.py`, `dev\dev_smoke_var_1a.py`

### `VAR\__init__.py`

- **Milestone:** `VAR`
- **Option ID:** `VAR-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

### `WORKFLOW\workflow_1e_steps_normalizer.py`

- **Milestone:** `WORKFLOW`
- **Option ID:** `WORKFLOW-1E`
- **Exports (`__all__`):** `normalize_workflow_steps`, `normalize_workflow_dict`, `normalize_capture_bundle_workflow`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_workflow_1e_steps_normalizer.py`

### `WORKFLOW\workflow_1f_selector_ref_first.py`

- **Milestone:** `WORKFLOW`
- **Option ID:** `WORKFLOW-1F`
- **Exports (`__all__`):** `selector_pack_selector_to_ref`, `enforce_selector_ref_first_in_steps`, `enforce_selector_ref_first_in_workflow`, `enforce_selector_ref_first_in_bundle`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_workflow_1f_selector_ref_first.py`

### `WORKFLOW\workflow_2a_capture_actions_to_schema_steps.py`

- **Milestone:** `WORKFLOW`
- **Option ID:** `WORKFLOW-2A`
- **Exports (`__all__`):** `ALLOWED_CAPTURE_ACTIONS_1A`, `load_steps_schema_1a`, `find_step_variant_schema_by_action_1a`, `infer_discriminator_key_for_action_1a`, `make_step_open_1a`, `make_step_click_selector_1a`, `make_step_wait_for_selector_1a`, `make_step_type_selector_secret_1a`, `make_step_by_action_1a`, `make_steps_by_actions_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_workflow_workflow_2a_capture_actions_to_schema_steps.py`

### `WORKFLOW\workflow_2b_capture_js_event_recorder.py`

- **Milestone:** `WORKFLOW`
- **Option ID:** `WORKFLOW-2B`
- **Exports (`__all__`):** `CAPTURE_QUEUE_GLOBAL_1A`, `CAPTURE_EVENT_KINDS_1A`, `SUPPORTED_STEP_ACTIONS_1A`, `js_install_capture_listeners_1a`, `js_drain_capture_events_1a`, `install_capture_listeners_in_page_1a`, `drain_capture_events_from_page_1a`, `normalize_capture_event_1a`, `capture_events_to_schema_steps_1a`, `drain_capture_steps_from_page_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_workflow_workflow_2b_capture_js_event_recorder.py`

### `WORKFLOW\workflow_2c_capture_events_to_schema_steps_encoder.py`

- **Milestone:** `WORKFLOW`
- **Option ID:** `WORKFLOW-2C`
- **Exports (`__all__`):** `capture_events_to_action_payloads_1a`, `encode_capture_events_to_schema_steps_1a`, `drain_capture_schema_steps_from_page_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_workflow_workflow_2c_capture_events_to_schema_steps_encoder.py`

### `WORKFLOWS\workflow_1a_loader.py`

- **Milestone:** `WORKFLOWS`
- **Option ID:** `WORKFLOWS-1A`
- **Exports (`__all__`):** `load_workflow_file`, `load_validate_normalize_workflow`, `normalize_workflow`, `validate_workflow`
- **Doc summary:** WORKFLOW-1A — Workflow file loader + validator + normalizer
- **Smoke tests:** `dev\dev_smoke_workflow_1a_loader.py`

### `WORKFLOWS\workflow_1g_deploy_bundle_loader.py`

- **Milestone:** `WORKFLOWS`
- **Option ID:** `WORKFLOWS-1G`
- **Exports (`__all__`):** `load_json_mapping_from_path`, `load_deploy_bundle_1a`, `load_deploy_bundle_1a_from_path`, `extract_runnable_from_deploy_bundle_1a`, `dev_smoke`
- **Doc summary:** _(none)_
- **Smoke tests:** `dev\dev_smoke_workflow_1g_deploy_bundle_loader.py`

### `WORKFLOWS\__init__.py`

- **Milestone:** `WORKFLOWS`
- **Option ID:** `WORKFLOWS-??`
- **Exports (`__all__`):** _(none or not parseable)_
- **Doc summary:** _(none)_
- **Smoke tests:** _(none found)_

## How to run smoke tests

Standard pattern:

```bash
python dev/dev_smoke_<milestone>_<option>.py
# examples:
python dev/dev_smoke_cli_1a.py
python dev/dev_smoke_pipe_2e.py
```

## Add new module checklist

- Pick the correct **milestone folder** (e.g., `CLI/`, `PIPE/`, `AUTH/`).
- Use the **Option ID naming pattern** in the filename (e.g., `cli_1d_...py` => `CLI-1D`).
- Define `__all__` explicitly for the new module.
- Add/extend a `dev/dev_smoke_<milestone>_<option>.py` smoke test.
- Keep modules additive; avoid breaking existing imports/contracts.
- If replacing/deprecating, follow your repo’s archive policy (retain old modules or provide compatible shims).
