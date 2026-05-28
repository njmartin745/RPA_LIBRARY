"""  
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
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Iterable, List, Mapping, Sequence  
import json  
  
  
__all__ = [  
    "SLO",  
    "SuccessCriterion",  
    "get_slos",  
    "get_success_criteria",  
    "render_slos_markdown",  
    "render_success_criteria_markdown",  
    "render_operational_standards_markdown",  
    "slos_to_json",  
    "success_criteria_to_json",  
    "write_text_file",  
    "write_operational_standards_markdown",  
]  
  
  
@dataclass(frozen=True, slots=True)  
class SLO:  
    """  
    Service Level Objective definition.  
  
    Fields are written to be directly usable in docs and reviewable diffs.  
    """  
  
    slo_id: str  
    name: str  
    objective: str  
    scope: str  
    measurement: str  
    target: str  
    window: str  
    error_budget_policy: str  
  
  
@dataclass(frozen=True, slots=True)  
class SuccessCriterion:  
    """  
    Production-readiness success criteria.  
  
    These are gating conditions for calling the system "production ready".  
    """  
  
    criterion_id: str  
    statement: str  
    evidence: str  
  
  
def get_slos() -> List[SLO]:  
    """  
    Canonical SLO set for production readiness.  
  
    Deterministic ordering is part of the contract (stable diffs).  
    """  
    return [  
        SLO(  
            slo_id="SLO-VAL-001",  
            name="Workflow schema validation reliability",  
            objective="Workflows used in production must be schema-valid and limited to supported actions.",  
            scope="All workflows in release bundles intended for production",  
            measurement=(  
                "CI runs LINT/lint_1a_steps_validator.py against all workflow JSON/YAML before release."  
            ),  
            target="100% validation pass rate for any released bundle",  
            window="Per release",  
            error_budget_policy="No error budget: a single failure blocks release.",  
        ),  
        SLO(  
            slo_id="SLO-RUN-001",  
            name="Workflow run success rate",  
            objective="Production workflow runs should complete successfully under normal dependency conditions.",  
            scope="Production executions excluding confirmed upstream outages (e.g., vendor downtime)",  
            measurement=(  
                "RUN outcomes recorded by the runner + REPORT artifacts; compute success_rate = "  
                "successful_runs / total_runs."  
            ),  
            target=">= 99.5% success rate",  
            window="Rolling 30 days",  
            error_budget_policy=(  
                "If error budget exhausted, freeze non-critical changes and prioritize remediation."  
            ),  
        ),  
        SLO(  
            slo_id="SLO-OBS-001",  
            name="Artifact and audit trail completeness",  
            objective="Every run must emit sufficient artifacts for audit, debugging, and replay.",  
            scope="All production runs",  
            measurement=(  
                "Check presence of run logs + report output + history/replay artifacts "  
                "(where configured) per run_id."  
            ),  
            target="100% of runs produce required artifacts",  
            window="Rolling 7 days",  
            error_budget_policy="Any missing artifact is a Sev-2 until fixed or mitigated.",  
        ),  
        SLO(  
            slo_id="SLO-SEC-001",  
            name="Secret handling and log hygiene",  
            objective="Secrets must never be emitted in plaintext logs or reports.",  
            scope="All production runs and CI logs",  
            measurement=(  
                "Static grep/scan of emitted logs + report artifacts; "  
                "ensure secrets are only provided via type_selector_secret and are masked elsewhere."  
            ),  
            target="0 confirmed secret disclosures",  
            window="Rolling 90 days",  
            error_budget_policy="No error budget: any disclosure triggers incident response.",  
        ),  
        SLO(  
            slo_id="SLO-REL-001",  
            name="Deterministic re-run behavior",  
            objective="A re-run with the same inputs should follow the same workflow logic deterministically.",  
            scope="Workflows designed to be deterministic (most production flows)",  
            measurement=(  
                "Compare step traces / history artifacts across re-runs with same inputs "  
                "(excluding timestamps and external system variability)."  
            ),  
            target=">= 99% deterministic step-sequence match for controlled re-run tests",  
            window="Rolling 30 days",  
            error_budget_policy="If below target, block further releases for affected workflows until fixed.",  
        ),  
    ]  
  
  
def get_success_criteria() -> List[SuccessCriterion]:  
    """  
    Canonical production-readiness success criteria.  
  
    Deterministic ordering is part of the contract (stable diffs).  
    """  
    return [  
        SuccessCriterion(  
            criterion_id="SC-OPS-001",  
            statement="Operational SLOs are defined, reviewed, and accessible to operators.",  
            evidence="This module renders the SLOs to Markdown/JSON and is checked into version control.",  
        ),  
        SuccessCriterion(  
            criterion_id="SC-OPS-002",  
            statement="CI enforces schema validation and blocks unsupported workflow actions.",  
            evidence="CI runs the validator (LINT/lint_1a_steps_validator.py) and fails on violations.",  
        ),  
        SuccessCriterion(  
            criterion_id="SC-OPS-003",  
            statement="Run outcomes produce auditable artifacts for debugging and replay.",  
            evidence="A sample run demonstrates logs + report + any configured history/replay outputs.",  
        ),  
        SuccessCriterion(  
            criterion_id="SC-OPS-004",  
            statement="Secret injection uses only approved secret-handling mechanisms.",  
            evidence=(  
                "Workflows use type_selector_secret for secrets; logs/reports show no plaintext secrets."  
            ),  
        ),  
        SuccessCriterion(  
            criterion_id="SC-OPS-005",  
            statement="Determinism expectations are documented and verified for key workflows.",  
            evidence=(  
                "A controlled re-run test shows identical step ordering for deterministic workflows."  
            ),  
        ),  
    ]  
  
  
def _md_escape(s: str) -> str:  
    # Keep it simple and deterministic; we only need minimal escaping for docs.  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_slos_markdown(slos: Sequence[SLO]) -> str:  
    lines: List[str] = []  
    lines.append("# Operational SLOs")  
    lines.append("")  
    lines.append(  
        "This document defines Service Level Objectives (SLOs) for operating the Selenium RPA framework in production."  
    )  
    lines.append("")  
    for slo in slos:  
        lines.append(f"## { _md_escape(slo.slo_id) }: { _md_escape(slo.name) }")  
        lines.append("")  
        lines.append(f"- **Objective:** { _md_escape(slo.objective) }")  
        lines.append(f"- **Scope:** { _md_escape(slo.scope) }")  
        lines.append(f"- **Measurement:** { _md_escape(slo.measurement) }")  
        lines.append(f"- **Target:** { _md_escape(slo.target) }")  
        lines.append(f"- **Window:** { _md_escape(slo.window) }")  
        lines.append(f"- **Error budget policy:** { _md_escape(slo.error_budget_policy) }")  
        lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def render_success_criteria_markdown(criteria: Sequence[SuccessCriterion]) -> str:  
    lines: List[str] = []  
    lines.append("# Production Success Criteria")  
    lines.append("")  
    lines.append(  
        "These criteria define what 'production ready' means for this framework and its releases."  
    )  
    lines.append("")  
    for c in criteria:  
        lines.append(f"## { _md_escape(c.criterion_id) }")  
        lines.append("")  
        lines.append(f"- **Statement:** { _md_escape(c.statement) }")  
        lines.append(f"- **Evidence:** { _md_escape(c.evidence) }")  
        lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def render_operational_standards_markdown(  
    slos: Sequence[SLO],  
    criteria: Sequence[SuccessCriterion],  
) -> str:  
    """  
    Combined operator-facing doc artifact (single file) for convenience.  
    """  
    parts = [  
        "# Production Readiness — Operational Standards",  
        "",  
        "This document is generated from canonical definitions in code to ensure reviewable diffs.",  
        "",  
        render_slos_markdown(slos).rstrip(),  
        "",  
        render_success_criteria_markdown(criteria).rstrip(),  
        "",  
    ]  
    return "\n".join(parts).rstrip() + "\n"  
  
  
def slos_to_json(slos: Sequence[SLO]) -> str:  
    payload = [  
        {  
            "slo_id": s.slo_id,  
            "name": s.name,  
            "objective": s.objective,  
            "scope": s.scope,  
            "measurement": s.measurement,  
            "target": s.target,  
            "window": s.window,  
            "error_budget_policy": s.error_budget_policy,  
        }  
        for s in slos  
    ]  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def success_criteria_to_json(criteria: Sequence[SuccessCriterion]) -> str:  
    payload = [  
        {  
            "criterion_id": c.criterion_id,  
            "statement": c.statement,  
            "evidence": c.evidence,  
        }  
        for c in criteria  
    ]  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    """  
    Small I/O helper (kept separate from pure renderers).  
    """  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_operational_standards_markdown(path: str) -> None:  
    """  
    Convenience entrypoint for producing a single operator doc file.  
    """  
    slos = get_slos()  
    criteria = get_success_criteria()  
    md = render_operational_standards_markdown(slos, criteria)  
    write_text_file(path, md)  