# Module Header Standard

## Purpose

Every production module should have a standardized header that allows:

- Repository inventory generation
- Capability discovery
- Dependency mapping
- Audit tracking
- AI-assisted maintenance
- Faster onboarding

The goal is not to prove a module works.

The goal is to establish:

```text
Exists
↓
Identified
↓
Audited
↓
Tested
↓
Signed Off
```

---

# Standard Format

```python
"""
RUN-1B — Workflow Runner With Snapshot Support

Purpose
-------
Execute workflows while automatically capturing runtime
snapshots for replay, diagnostics, healing, and auditing.

Public API
----------
run_workflow(...)
execute_step(...)

Dependencies
------------
ACT-*
PIPE-*
SNAP-*

Status
------
Draft
"""
```

---

# Required Sections

## Module ID and Title

First line of the docstring.

Format:

```text
CATEGORY-NUMBER — Human Readable Title
```

Examples:

```text
RUN-1B — Workflow Runner With Snapshot Support
BUILD-2A — Natural Language Build Spec Generator
HEAL-1C — Selector Repair Engine
```

Rules:

- Must be unique.
- Must be the first non-empty line.
- Must remain stable once published.

---

## Purpose

Describe:

- Why the module exists
- What responsibility it owns
- What problem it solves

Keep concise.

Target:

```text
2–8 lines
```

---

## Public API

List the primary entry points.

Example:

```text
run_workflow(...)
load_workflow(...)
```

If the module is internal-only:

```text
Internal Only
```

---

## Dependencies

List major module-level dependencies.

Example:

```text
ACT-*
PIPE-*
SNAP-*
```

If none:

```text
None
```

---

## Status

Allowed values:

```text
Draft
Audited
Tested
Signed Off
Deprecated
```

Definitions:

| Status | Meaning |
|----------|----------|
| Draft | Exists but not formally reviewed |
| Audited | Design reviewed |
| Tested | Validation completed |
| Signed Off | Approved for platform use |
| Deprecated | Retained for compatibility only |

---

# Optional Sections

## Inputs

Describe expected inputs.

## Outputs

Describe expected outputs.

## Notes

Additional implementation notes.

## Example

Usage examples.

---

# Generator Compatibility

The repository inventory generator expects:

- A top-level module docstring
- Module ID on the first non-empty line

Example:

```text
RUN-1B
BUILD-2A
PIPE-1F
```

This enables automatic categorization and capability mapping.

---

# Repository Policy

Production modules should comply with this standard.

Dev, smoke-test, experimental, and temporary files may use simplified headers until promoted into the main platform.