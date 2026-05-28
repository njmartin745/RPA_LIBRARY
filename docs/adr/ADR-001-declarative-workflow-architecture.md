# ADR-001: Declarative Workflow Architecture

- Status: Accepted
- Date: 2026-05-28

---

# Context

The RPA Library originally evolved through practical automation scripting focused on browser interaction and workflow execution.

As the platform expanded, several architectural pressures emerged:

- growing workflow complexity
- vendor-specific drift
- retry/recovery requirements
- validation needs
- orchestration reuse
- operational observability
- future AI-agent integration

Traditional imperative Selenium scripting began creating architectural risks:

- brittle orchestration
- duplicated logic
- hidden execution assumptions
- inconsistent retry behavior
- difficult maintainability
- poor introspection
- limited scalability

The platform required a more durable architectural direction.

---

# Decision

The platform will adopt a:

```text
Declarative Workflow Architecture
```

where:

- workflows describe intent
- the runtime owns execution mechanics
- actions are modular and standardized
- orchestration is centralized
- validation and reconciliation are first-class responsibilities

Workflows should define:

- ordered steps
- inputs
- variables
- validation expectations
- reconciliation requirements
- retry intent

The runtime should own:

- browser lifecycle
- execution sequencing
- retries
- logging
- state management
- orchestration
- error handling
- audit systems

---

# Architectural Principles

## 1. Runtime-Driven Execution

The runtime is responsible for orchestration.

Workflows should remain declarative whenever possible.

This enables:

- reusable execution engines
- centralized reliability strategies
- consistent observability
- platform governance

---

## 2. Modular Action Dispatching

Execution should move toward a standardized action registry.

Conceptual direction:

```python
ACTION_REGISTRY = {
    "click": click_action,
    "open_url": open_url_action,
    "execute_js": execute_js_action,
}
```

Goals:

- composability
- testability
- plugin support
- AI discoverability
- standardized behavior

---

## 3. Vendor Isolation

Vendor-specific logic should remain isolated from runtime orchestration.

Examples:

- selectors
- portal quirks
- DOM assumptions
- export logic
- JS helpers

This separation improves:

- maintainability
- portability
- repairability
- operational consistency

---

## 4. Validation-Driven Reliability

Execution success should NOT be assumed simply because actions completed.

The platform should prioritize:

- validation
- reconciliation
- auditability
- recovery
- retry safety

This is a foundational architectural principle.

---

## 5. Observable Execution

The runtime should produce:

- structured logs
- action results
- validation outcomes
- reconciliation reports
- retry history
- execution telemetry

This supports:

- operational debugging
- governance
- analytics
- AI-assisted reasoning

---

# Consequences

## Positive Consequences

### Improved Maintainability

Centralized orchestration reduces duplicated logic and inconsistent workflow behavior.

---

### Better Reliability

Validation and reconciliation become systemic platform capabilities instead of ad hoc workflow logic.

---

### Workflow Reuse

Declarative workflows become portable across runtime improvements.

---

### AI-Agent Compatibility

Explicit contracts and structured actions improve future AI-assisted operations.

Potential future capabilities:

- selector repair recommendations
- workflow drift detection
- runtime optimization
- stale documentation updates
- operational diagnostics

---

### Scalable Governance

Architectural boundaries become enforceable and reviewable.

---

# Tradeoffs

## Increased Initial Complexity

Declarative architectures require:

- schema design
- runtime abstraction
- contract formalization
- stronger boundaries

This increases short-term implementation overhead.

---

## Reduced Workflow Flexibility

Some highly custom portal interactions may initially feel slower to implement due to runtime constraints.

However, this tradeoff is intentional to preserve long-term platform integrity.

---

## Runtime Responsibility Expansion

The runtime becomes more sophisticated and must handle:

- retries
- orchestration
- validation
- observability
- state management

This increases the importance of runtime quality and governance.

---

# Rejected Alternatives

## Alternative 1: Pure Imperative Selenium Scripts

Rejected because:

- orchestration logic becomes duplicated
- workflows become brittle
- retry behavior becomes inconsistent
- validation becomes fragmented
- scaling becomes difficult

---

## Alternative 2: Fully Embedded Vendor Logic

Rejected because:

- vendor assumptions contaminate runtime behavior
- maintainability degrades rapidly
- portability decreases
- AI-assisted repair becomes harder

---

## Alternative 3: Fully Autonomous AI Execution

Rejected for now because:

- runtime governance is not mature enough
- contracts are still evolving
- auditability must remain primary
- deterministic execution is required first

The platform will move toward:

```text
AI-assisted governance
```

before:

```text
AI-autonomous orchestration
```

---

# Future Direction

Future architectural evolution may include:

- formal workflow schemas
- plugin-based action registries
- runtime capability discovery
- distributed orchestration
- workflow simulation/testing
- AI-assisted validation
- operational analytics dashboards
- automatic reconciliation systems

---

# Related Documents

- `/docs/architecture/runtime_overview.md`
- `/docs/architecture/workflow_contract.md`

---

# Notes

This ADR establishes the foundational architectural direction of the RPA platform.

Future ADRs should build upon this decision unless explicitly superseded.
