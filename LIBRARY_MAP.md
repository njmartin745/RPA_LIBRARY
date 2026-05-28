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