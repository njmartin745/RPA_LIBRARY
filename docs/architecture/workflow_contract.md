# Workflow Contract Specification

## Purpose

This document defines the standard contract structure for workflows executed by the RPA runtime.

The goal of workflow contracts is to ensure:

- consistent execution behavior
- predictable runtime orchestration
- reusable automation patterns
- validation-driven reliability
- AI-compatible workflow reasoning
- long-term maintainability

This document establishes the architectural baseline for workflow definitions across the platform.

---

# Core Philosophy

Workflows should remain:

- declarative
- deterministic
- observable
- composable
- vendor-isolated
- runtime-driven

A workflow should describe:

- WHAT should happen
- the runtime determines HOW execution occurs

This separation is critical for:

- scalability
- maintainability
- orchestration reuse
- AI-assisted governance

---

# Workflow Responsibilities

A workflow is responsible for defining:

- execution intent
- ordered steps
- runtime variables
- validation expectations
- retry behavior
- reconciliation requirements
- output expectations

A workflow should NOT directly own:

- browser lifecycle management
- orchestration internals
- logging systems
- retry engine implementation
- runtime state persistence
- audit storage

These belong to the runtime layer.

---

# Workflow Structure

Conceptually:

```text
Workflow
 ├── Metadata
 ├── Variables
 ├── Inputs
 ├── Steps
 ├── Validation Rules
 ├── Retry Policy
 ├── Reconciliation Rules
 └── Outputs
```

---

# Recommended Workflow Schema

Example conceptual structure:

```json
{
  "workflow_id": "invoice_download",
  "name": "Invoice Download Workflow",
  "version": "1.0",
  "vendor": "example_vendor",
  "criticality": "high",
  "inputs": {},
  "variables": {},
  "steps": [],
  "validation": {},
  "retry_policy": {},
  "reconciliation": {},
  "outputs": {}
}
```

This is a conceptual reference and may evolve as runtime contracts mature.

---

# Metadata Contract

Metadata defines runtime classification and governance attributes.

Recommended fields:

```json
{
  "workflow_id": "invoice_download",
  "name": "Invoice Download Workflow",
  "version": "1.0",
  "vendor": "vendor_name",
  "criticality": "high",
  "owner": "finance_ops"
}
```

Goals:

- workflow discoverability
- auditability
- governance
- operational classification
- dependency tracking

---

# Inputs Contract

Inputs represent external data required for execution.

Examples:

- file paths
- account identifiers
- date ranges
- manifest records
- download directories

Example:

```json
{
  "inputs": {
    "manifest_path": "input/manifest.csv",
    "download_dir": "downloads/"
  }
}
```

Inputs should remain:

- explicit
- validated
- serializable
- environment-independent whenever possible

---

# Variables Contract

Variables represent runtime-scoped mutable values.

Examples:

- current item
- temporary selectors
- retry counts
- dynamic URLs
- runtime substitutions

Variables should:

- remain scoped
- avoid hidden mutation
- support runtime introspection
- remain serializable where possible

---

# Step Contract

Steps define ordered executable actions.

Each step should contain:

- action type
- parameters
- optional validation
- optional retry override
- optional timeout
- optional reconciliation metadata

Conceptual example:

```json
{
  "step_id": "open_portal",
  "action": "open_url",
  "params": {
    "url": "https://vendor-portal.com"
  },
  "timeout": 30
}
```

---

# Action Contract

The runtime should dispatch actions through a standardized action registry.

Examples:

- open_url
- click
- wait
- execute_js
- switch_frame
- download_file
- validate_element

Actions should:

- remain atomic
- produce structured results
- avoid hidden side effects
- expose clear failure states

---

# Action Result Contract

Every action should return a standardized result object.

Conceptual structure:

```json
{
  "success": true,
  "message": "Opened URL successfully",
  "duration_ms": 420,
  "artifacts": [],
  "warnings": []
}
```

Benefits:

- deterministic orchestration
- auditability
- AI reasoning compatibility
- standardized retry handling
- observability

---

# Validation Contract

Validation is a first-class workflow responsibility.

Validation should confirm:

- expected page state
- expected downloads
- expected row counts
- expected file existence
- expected portal responses

Validation should NOT assume success simply because execution completed.

Example:

```json
{
  "validation": {
    "expected_download_count": 10,
    "required_files": ["report.csv"]
  }
}
```

---

# Retry Policy Contract

Retries should be explicitly configurable.

Recommended structure:

```json
{
  "retry_policy": {
    "max_attempts": 3,
    "backoff": "exponential"
  }
}
```

The runtime owns retry implementation.

The workflow defines retry intent.

---

# Reconciliation Contract

Reconciliation compares:

- expected outputs
- actual outputs

Examples:

- expected invoices vs downloaded invoices
- expected rows vs processed rows
- expected files vs produced files

Example:

```json
{
  "reconciliation": {
    "enabled": true,
    "key": "invoice_id"
  }
}
```

This is a core reliability strategy of the platform.

---

# Output Contract

Outputs define artifacts produced by workflow execution.

Examples:

- CSV files
- PDFs
- screenshots
- logs
- reconciliation reports
- processed manifests

Example:

```json
{
  "outputs": {
    "download_dir": "downloads/",
    "report_file": "results/report.csv"
  }
}
```

Outputs should remain:

- explicit
- predictable
- auditable
- machine-readable

---

# Runtime Ownership Boundaries

The runtime owns:

- execution sequencing
- browser lifecycle
- retries
- logging
- audit systems
- runtime state
- exception handling
- orchestration

The workflow owns:

- declarative intent
- ordered actions
- validation expectations
- reconciliation expectations
- runtime parameters

Maintaining this boundary is critical.

---

# Vendor Isolation

Vendor-specific behavior should remain isolated.

Examples:

- selectors
- JS snippets
- portal navigation quirks
- DOM assumptions
- export/download logic

This prevents vendor logic from contaminating runtime orchestration.

---

# AI-Agent Compatibility

Workflow contracts are intentionally designed to support future AI-assisted operations.

Benefits include:

- machine-readable execution plans
- predictable action structures
- introspectable runtime behavior
- automated validation reasoning
- safer autonomous recommendations
- workflow governance

Potential future AI responsibilities:

- selector repair suggestions
- workflow drift detection
- retry optimization
- stale workflow detection
- documentation generation
- dependency analysis

---

# Design Constraints

Workflow definitions should avoid:

- hidden side effects
- implicit dependencies
- environment-specific assumptions
- tightly coupled vendor logic
- embedded orchestration behavior
- non-deterministic execution

---

# Long-Term Direction

The workflow system is evolving toward:

```text
Declarative Automation Contracts
```

rather than:

```text
imperative automation scripts
```

This transition enables:

- reusable orchestration
- scalable governance
- AI-assisted operations
- runtime portability
- operational resilience

---

# Status

This document represents the initial workflow contract baseline.

The specification will evolve alongside:

- runtime modularization
- action registry formalization
- orchestration maturity
- validation/reconciliation improvements
- AI governance systems
