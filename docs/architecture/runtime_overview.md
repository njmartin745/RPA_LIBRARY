# Runtime Overview

## Purpose

The RPA Library is evolving from a collection of Selenium scripts into a reusable automation runtime and orchestration platform.

The purpose of this document is to define the high-level runtime architecture, execution philosophy, and operational boundaries of the system.

This document is intended to serve as:

- a shared architectural reference
- a contributor onboarding guide
- a future AI-agent reasoning reference
- a platform governance foundation

---

# Architectural Direction

The platform is designed around the following principles:

1. Declarative workflow orchestration
2. Runtime-driven execution
3. Modular browser interaction layers
4. Validation and reconciliation-first reliability
5. Observable and auditable execution
6. Vendor/workflow separation
7. AI-assisted operational scalability

The long-term goal is to support:

- reusable workflows
- recoverable execution
- autonomous validation
- operational governance
- AI-assisted maintenance and optimization

---

# High-Level Runtime Model

The runtime currently operates through:

1. Workflow definition loading
2. Runtime context initialization
3. Browser/session setup
4. Step orchestration
5. Action dispatching
6. Validation/reconciliation
7. Retry/recovery handling
8. Audit logging and completion reporting

Conceptually:

```text
Workflow Definition
        ↓
Runtime Engine
        ↓
Action Dispatcher
        ↓
Browser + JS Adapters
        ↓
Validation/Reconciliation
        ↓
Audit + Results
```

---

# Core Runtime Responsibilities

## 1. Orchestration

The runtime owns:

- workflow loading
- execution sequencing
- loop handling
- retry management
- variable substitution
- execution lifecycle control

The runtime should NOT contain:

- vendor-specific business logic
- brittle DOM assumptions
- hardcoded workflow semantics

---

## 2. Action Dispatching

Actions represent atomic runtime operations.

Examples:

- open page
- click selector
- execute JS
- switch tabs
- wait
- validate state
- download artifacts

Long-term direction:

```python
ACTION_REGISTRY = {
    "open": open_action,
    "click": click_action,
    "exec_js": exec_js_action,
}
```

Goals:

- modularity
- testability
- plugin support
- standardized contracts
- AI discoverability

---

## 3. Browser Interaction Layer

The platform currently uses Selenium-driven browser automation.

Design direction:

- Python manages orchestration
- JavaScript manages DOM-specific interactions
- Vendor logic remains isolated from runtime logic

This separation improves:

- maintainability
- selector isolation
- portability
- debugging
- vendor adaptation

---

## 4. Runtime Context

Execution context represents mutable state during workflow execution.

Examples:

- current manifest item
- retry attempt
- active workflow
- session state
- runtime variables
- audit references

Long-term direction:

```python
class RuntimeContext:
    workflow_id: str
    current_item: str
    attempt: int
    variables: dict
    audit: AuditManager
```

Goals:

- centralized state
- explicit ownership
- predictable execution
- AI introspection support

---

# Reliability Strategy

## Reconciliation-Driven Reliability

The runtime assumes:

- browser automation can partially fail
- downloads can silently fail
- selectors can drift
- sessions can expire
- portals can become unstable

Therefore:

Validation and reconciliation are considered first-class runtime responsibilities.

The runtime should:

- validate expected outputs
- compare expected vs actual artifacts
- retry missing work
- isolate partial failures
- preserve auditability

This differs from traditional Selenium scripting, where success is often incorrectly assumed after execution.

---

# Audit and Observability

The platform should maintain:

- execution logs
- timestamps
- retry history
- workflow status
- validation results
- reconciliation events
- error context

Future goals:

- structured telemetry
- workflow analytics
- failure dashboards
- operational health monitoring
- execution replay support

---

# Workflow Philosophy

Workflows should remain declarative whenever possible.

The runtime executes workflows.

Workflows should describe:

- intent
- sequencing
- validation expectations
- retry semantics
- required inputs

The runtime should implement:

- execution mechanics
- state management
- browser lifecycle
- logging
- recovery behavior

---

# Vendor Isolation

Vendor-specific logic should remain isolated from the runtime core.

Examples:

- selectors
- portal-specific waits
- navigation quirks
- DOM parsing
- download handling

Long-term direction:

```text
/workflows
/vendors
/scripts
/core
/runtime
```

This separation allows:

- reusable orchestration
- vendor swapping
- maintainable upgrades
- AI-assisted repair

---

# AI-Agent Readiness

The architecture is intentionally moving toward AI-compatible operational design.

To support future autonomous or semi-autonomous agents, the system should emphasize:

- explicit contracts
- deterministic workflows
- standardized action results
- observable runtime state
- validation-driven execution
- explainable behavior
- isolated side effects

Potential future agent responsibilities:

- workflow validation
- selector repair recommendations
- stale documentation updates
- retry optimization
- architectural drift detection
- operational reporting

Agents should operate under governance constraints and preserve auditability.

---

# Near-Term Architectural Priorities

## Priority 1

Stabilize runtime boundaries.

## Priority 2

Refactor orchestration into modular dispatching.

## Priority 3

Formalize workflow contracts and schemas.

## Priority 4

Separate runtime, vendor, and workflow ownership.

## Priority 5

Improve observability and reconciliation.

---

# Long-Term Vision

The long-term direction of the platform is:

```text
Automation Runtime Platform
```

rather than:

```text
isolated automation scripts
```

The platform is intended to support:

- reusable orchestration
- operational resilience
- scalable workflow governance
- AI-assisted maintenance
- automation observability
- continuous platform evolution

---

# Status

This document represents the initial runtime architecture baseline.

It will evolve as:

- runtime boundaries become formalized
- workflows become standardized
- recovery systems mature
- AI governance capabilities expand
- orchestration becomes more modular
