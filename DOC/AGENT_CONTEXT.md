# AGENT_CONTEXT.md
AI Agent Context for Modular Selenium RPA Framework
 
This file provides high-level architectural context so that AI agents
(ChatGPT, Copilot, Claude, etc.) can reason about the repository
without needing to ingest the entire codebase.
 
Agents should read this file before generating new modules.
 
---
 
# Framework Purpose
 
This repository implements a **modular Selenium RPA framework**
designed to support:
 
• JSON-driven automation workflows  
• reusable Selenium interaction helpers  
• resumable execution pipelines  
• AI-assisted workflow generation  
• debugging, replay, and healing of automation runs  
 
The architecture is intentionally **layered and additive** so that
new capabilities can be introduced without modifying existing modules.
 
---
 
# Core Design Principles
 
1. **Modules are additive**
   - Existing modules should never be rewritten unless explicitly requested.
 
2. **Public interfaces are explicit**
   - All modules must define `__all__`.
 
3. **Smoke tests required**
   - Every module must have a corresponding `dev_smoke_*` test.
 
4. **Separation of concerns**
   - Each layer has a single responsibility.
 
5. **AI-friendly architecture**
   - Module names encode capability.
   - Naming conventions are predictable.
 
6. **Pure helpers when possible**
   - Utility functions should not depend on global state.
 
---
 
# Layered Architecture
 
The framework is divided into logical layers.
 
## ENTRY
Driver bootstrap and environment setup.
 
Example:
ENTRY/entry_1a_webdriver_bootstrap.py
 
Responsibilities:
 
• WebDriver creation  
• browser configuration  
• headless configuration  
 
---
 
## NAV
Low-level Selenium interaction helpers.
 
Example:
NAV/nav_1a_selenium_helpers.py
 
Responsibilities:
 
• waits  
• clicking  
• typing  
• frame switching  
• download detection  
 
NAV functions are **pure Selenium utilities**.
 
---
 
## ACT
Step execution engine.
 
Example:
ACT/act_1a_action_engine.py
 
Responsibilities:
 
• execute JSON steps  
• dispatch step handlers  
• call NAV helpers  
 
ACT translates workflow steps into browser actions.
 
---
 
## PIPE
Workflow orchestration.
 
Example:
PIPE/pipe_1a_pipeline_runner.py
 
Responsibilities:
 
• workflow execution loop  
• step sequencing  
• runtime configuration  
 
PIPE coordinates the overall automation process.
 
---
 
## STATE
Persistence and manifest tracking.
 
Example:
STATE/state_1b_manifest_jsonl.py
 
Responsibilities:
 
• run state  
• retry/resume support  
• manifest file management  
 
---
 
## VAR
Runtime variable storage.
 
Example:
VAR/var_1a_runtime_store.py
 
Responsibilities:
 
• store runtime variables  
• share data between steps  
 
---
 
## VAL
UI validation helpers.
 
Example:
VAL/val_1a_ui_validation.py
 
Responsibilities:
 
• element validation  
• text checks  
• state assertions  
 
---
 
## OUT
Output handling.
 
Example:
OUT/out_1a_download_manager.py
 
Responsibilities:
 
• download detection  
• output file management  
 
---
 
## AUTH
Authentication helpers.
 
Example:
AUTH/auth_1a_form_login_guarded.py
 
Responsibilities:
 
• login flows  
• credential submission  
 
---
 
## DOC
Repository documentation utilities.
 
Example:
DOC/doc_1a_library_index.py
 
Responsibilities:
 
• module inventory  
• documentation generation  
 
---
 
## REGISTRY
Framework capability registry.
 
Example:
REGISTRY/registry_1a_capabilities.py
 
Responsibilities:
 
• register available modules  
• expose capabilities to AI agents  
 
---
 
## WORKFLOW
Workflow specification loaders.
 
Example:
WORKFLOW/workflow_1a_loader.py
 
Responsibilities:
 
• load workflow definitions  
• validate structure  
 
---
 
## RUN
Execution runtime controller.
 
Example:
RUN/run_1a_executor.py
 
Responsibilities:
 
• run workflows  
• manage runtime state  
 
---
 
## HEAL
Self-healing utilities.
 
Example:
HEAL/heal_1a_selector_recovery.py
 
Responsibilities:
 
• selector recovery  
• fallback logic  
 
---
 
## SNAP
Snapshot utilities.
 
Example:
SNAP/snap_1a_capture.py
 
Responsibilities:
 
• capture DOM state  
• debugging support  
 
---
 
## REPLAY
Execution replay.
 
Example:
REPLAY/replay_1a_run_replay.py
 
Responsibilities:
 
• replay failed runs  
 
---
 
## REPORT
Execution reporting.
 
Example:
REPORT/report_1a_run_report.py
 
Responsibilities:
 
• generate run summaries  
• diagnostic outputs  
 
---
 
## GUARD
Runtime protection.
 
Example:
GUARD/guard_1a_execution_guard.py
 
Responsibilities:
 
• detect dangerous actions  
• prevent invalid operations  
 
---
 
## DIFF
Snapshot comparison utilities.
 
Example:
DIFF/diff_1a_snapshot_diff.py
 
Responsibilities:
 
• compare DOM snapshots  
 
---
 
## HISTORY
Run history tracking.
 
Example:
HISTORY/history_1a_run_history.py
 
Responsibilities:
 
• store historical runs  
• analyze past behavior  
 
---
 
## DOCTOR
Framework diagnostics.
 
Example:
DOCTOR/doctor_1a_system_check.py
 
Responsibilities:
 
• health checks  
• dependency validation  
 
---
 
## BUILD
Workflow generation utilities.
 
Example:
BUILD/build_1a_spec_builder.py
 
Responsibilities:
 
• convert specs into workflows  
• prepare automation tasks  

---

## Canonical End-to-End Execution

The framework defines a **canonical end-to-end (E2E) execution path** used to
validate full system readiness, including:

- workflow validation and grammar gates
- pipeline execution
- artifact generation
- production readiness checks (DOCTOR / GUARD)

The canonical E2E run is **not hard-coded in this document**.
Instead, it is **derived from existing repository artifacts** and surfaced in:

- `DOC/AGENT_PACKET.md`
- `DOC/agent_packet.json`

AI agents and operators should rely on **AGENT_PACKET** for the current,
authoritative declaration of the canonical E2E run and its readiness criteria.
 
---
 
# AI Agent Operating Rules
 
When generating new modules:
 
1. Do not duplicate existing modules.
2. Follow naming conventions.
3. Ensure `__all__` is defined.
4. Provide a smoke test.
5. Keep helpers pure where possible.
6. Prefer composition over modification.
 
---
 
# Smoke Test Convention
 
All modules must include a development smoke test:
dev_smoke_.py
 
Smoke tests should:
 
• demonstrate minimal functionality  
• validate module loading  
• print a success message  
 
---
 
# Expected Future Extensions
 
Possible future modules:
BUILD-2A   Natural language → workflow generator LEARN-1A   failure pattern analytics AGENT-2A   autonomous workflow repair
 
---
 
# Summary
 
This repository is a **modular automation engine**
designed for both human developers and AI agents.
 
The architecture favors:
 
• composability  
• transparency  
• deterministic execution  
• AI-assisted automation generation