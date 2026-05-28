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