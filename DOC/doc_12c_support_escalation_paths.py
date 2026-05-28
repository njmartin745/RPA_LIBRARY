"""  
DOC-12C: Support and Escalation Paths (Milestone 12.1.3)  
  
Single responsibility:  
- Define deterministic, reviewable support + escalation standards for operating  
  the RPA framework in production.  
- Provide pure renderers (Markdown/JSON) for operator documentation.  
  
Scope:  
- Defines roles, severity taxonomy, response targets, escalation matrix, and  
  incident ticket requirements. Does not integrate with any external paging/ticketing.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Dict, List, Sequence  
import json  
  
  
__all__ = [  
    "SupportRole",  
    "SeverityLevel",  
    "ResponseTarget",  
    "EscalationRule",  
    "IncidentTicketRequirements",  
    "get_support_roles",  
    "get_severity_levels",  
    "get_response_targets",  
    "get_escalation_matrix",  
    "get_incident_ticket_requirements",  
    "render_support_escalation_markdown",  
    "support_escalation_to_json",  
    "write_text_file",  
    "write_support_escalation_markdown",  
]  
  
  
@dataclass(frozen=True, slots=True)  
class SupportRole:  
    role_id: str  
    name: str  
    responsibilities: List[str]  
  
  
@dataclass(frozen=True, slots=True)  
class SeverityLevel:  
    sev: str  # e.g., "SEV-1"  
    definition: str  
    examples: List[str]  
  
  
@dataclass(frozen=True, slots=True)  
class ResponseTarget:  
    sev: str  
    initial_response: str  # human-readable to avoid timezone/format ambiguity  
    update_frequency: str  
    mitigation_target: str  
  
  
@dataclass(frozen=True, slots=True)  
class EscalationRule:  
    rule_id: str  
    trigger: str  
    escalate_to: str  
    notes: str  
  
  
@dataclass(frozen=True, slots=True)  
class IncidentTicketRequirements:  
    required_fields: List[str]  
    recommended_fields: List[str]  
  
  
def get_support_roles() -> List[SupportRole]:  
    # Deterministic ordering for reviewable diffs  
    return [  
        SupportRole(  
            role_id="ROLE-L1",  
            name="L1 Operator (On-Call Runner)",  
            responsibilities=[  
                "Execute scheduled/manual production runs using approved bundles.",  
                "Monitor run outcomes and confirm artifact generation.",  
                "Perform initial triage using operator runbooks.",  
                "Escalate incidents with complete evidence and metadata.",  
            ],  
        ),  
        SupportRole(  
            role_id="ROLE-L2",  
            name="L2 Automation Engineer (Workflow/Selector Owner)",  
            responsibilities=[  
                "Diagnose workflow logic issues and selector drift.",  
                "Prepare reviewed fixes (workflow/selector diffs) and coordinate promotion.",  
                "Define deterministic re-run tests for key workflows.",  
                "Improve resilience within allowed action set and framework constraints.",  
            ],  
        ),  
        SupportRole(  
            role_id="ROLE-L3",  
            name="L3 Platform Maintainer (Framework Owner)",  
            responsibilities=[  
                "Investigate framework/runtime regressions (runner/executor/driver behavior).",  
                "Approve and ship framework changes under change control.",  
                "Own production operational gates defaults (DOCTOR/GUARD policies where applicable).",  
                "Drive root-cause analysis for systemic issues.",  
            ],  
        ),  
        SupportRole(  
            role_id="ROLE-SEC",  
            name="Security Contact (Secrets/Compliance)",  
            responsibilities=[  
                "Respond to suspected secret disclosure or audit/compliance concerns.",  
                "Review secret-handling incidents and remediation plans.",  
                "Approve changes to secret-handling operational procedures.",  
            ],  
        ),  
    ]  
  
  
def get_severity_levels() -> List[SeverityLevel]:  
    return [  
        SeverityLevel(  
            sev="SEV-1",  
            definition="Production automation is causing critical business impact or uncontrolled harmful side effects.",  
            examples=[  
                "High-volume incorrect submissions or irreversible destructive actions triggered by automation",  
                "Confirmed secret disclosure in logs/artifacts",  
                "Sustained production failure for a critical workflow with no workaround",  
            ],  
        ),  
        SeverityLevel(  
            sev="SEV-2",  
            definition="Major degradation or repeated failures impacting important workflows; workaround may exist.",  
            examples=[  
                "Critical workflow failing intermittently with growing backlog",  
                "Artifact/audit trail missing for production runs",  
                "Authentication failures due to environment/credential issues affecting multiple runs",  
            ],  
        ),  
        SeverityLevel(  
            sev="SEV-3",  
            definition="Minor impact, single workflow affected with low urgency, or non-production issue.",  
            examples=[  
                "Non-critical workflow failure with easy workaround",  
                "Cosmetic report issue with no business impact",  
            ],  
        ),  
    ]  
  
  
def get_response_targets() -> List[ResponseTarget]:  
    # Keep targets human-readable; orgs can map to SLAs.  
    return [  
        ResponseTarget(  
            sev="SEV-1",  
            initial_response="15 minutes",  
            update_frequency="Every 30 minutes until mitigated",  
            mitigation_target="4 hours (or fastest safe rollback)",  
        ),  
        ResponseTarget(  
            sev="SEV-2",  
            initial_response="1 hour",  
            update_frequency="Every 4 hours during business hours (or per on-call policy)",  
            mitigation_target="1 business day",  
        ),  
        ResponseTarget(  
            sev="SEV-3",  
            initial_response="1 business day",  
            update_frequency="As needed",  
            mitigation_target="Best effort / next planned release",  
        ),  
    ]  
  
  
def get_escalation_matrix() -> List[EscalationRule]:  
    return [  
        EscalationRule(  
            rule_id="ESC-001",  
            trigger="SEV-1 declared OR suspected secret disclosure",  
            escalate_to="ROLE-L3 + ROLE-SEC",  
            notes="Freeze promotions; preserve artifacts; restrict access if necessary.",  
        ),  
        EscalationRule(  
            rule_id="ESC-002",  
            trigger="SEV-1 mitigation not found within 60 minutes",  
            escalate_to="ROLE-L3",  
            notes="Execute rollback runbook; consider environment rollback; coordinate incident command if used.",  
        ),  
        EscalationRule(  
            rule_id="ESC-003",  
            trigger="Repeat failures of same workflow >= 3 times within 24 hours (non-SEV-1)",  
            escalate_to="ROLE-L2",  
            notes="Treat as systemic; require root cause and reviewed fix before further retries.",  
        ),  
        EscalationRule(  
            rule_id="ESC-004",  
            trigger="Framework/runtime suspected regression after upgrade (browser/driver/framework)",  
            escalate_to="ROLE-L3",  
            notes="Pin versions; revert upgrade; run smoke suite in controlled environment.",  
        ),  
    ]  
  
  
def get_incident_ticket_requirements() -> IncidentTicketRequirements:  
    return IncidentTicketRequirements(  
        required_fields=[  
            "run_id",  
            "workflow name",  
            "bundle version/fingerprint (workflow/selectors/framework as applicable)",  
            "environment (prod/stage), machine/image identity if known",  
            "failure timestamp (UTC recommended)",  
            "first failing step (index + action type)",  
            "logs + report artifact locations",  
            "impact summary (what business process affected)",  
            "severity (SEV-1/2/3) with rationale",  
        ],  
        recommended_fields=[  
            "screenshots/video if captured",  
            "browser + driver versions",  
            "recent change references (PRs/commits) for workflow/selectors/framework",  
            "re-run comparison notes (deterministic vs intermittent)",  
            "workaround attempted and outcome",  
        ],  
    )  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_support_escalation_markdown(  
    roles: Sequence[SupportRole],  
    severities: Sequence[SeverityLevel],  
    targets: Sequence[ResponseTarget],  
    matrix: Sequence[EscalationRule],  
    ticket: IncidentTicketRequirements,  
) -> str:  
    lines: List[str] = []  
    lines.append("# Support and Escalation Paths")  
    lines.append("")  
    lines.append("Canonical support model for operating the RPA framework in production.")  
    lines.append("")  
  
    lines.append("## Support Roles")  
    lines.append("")  
    for r in roles:  
        lines.append(f"### { _md(r.role_id) }: { _md(r.name) }")  
        lines.append("")  
        for item in r.responsibilities:  
            lines.append(f"- { _md(item) }")  
        lines.append("")  
  
    lines.append("## Severity Levels")  
    lines.append("")  
    for s in severities:  
        lines.append(f"### { _md(s.sev) }")  
        lines.append("")  
        lines.append(f"- **Definition:** { _md(s.definition) }")  
        lines.append("- **Examples:**")  
        for ex in s.examples:  
            lines.append(f"  - { _md(ex) }")  
        lines.append("")  
  
    lines.append("## Response Targets")  
    lines.append("")  
    for t in targets:  
        lines.append(f"### { _md(t.sev) }")  
        lines.append("")  
        lines.append(f"- **Initial response:** { _md(t.initial_response) }")  
        lines.append(f"- **Update frequency:** { _md(t.update_frequency) }")  
        lines.append(f"- **Mitigation target:** { _md(t.mitigation_target) }")  
        lines.append("")  
  
    lines.append("## Escalation Matrix")  
    lines.append("")  
    for e in matrix:  
        lines.append(f"### { _md(e.rule_id) }")  
        lines.append("")  
        lines.append(f"- **Trigger:** { _md(e.trigger) }")  
        lines.append(f"- **Escalate to:** { _md(e.escalate_to) }")  
        lines.append(f"- **Notes:** { _md(e.notes) }")  
        lines.append("")  
  
    lines.append("## Incident Ticket Requirements")  
    lines.append("")  
    lines.append("### Required")  
    lines.append("")  
    for f in ticket.required_fields:  
        lines.append(f"- { _md(f) }")  
    lines.append("")  
    lines.append("### Recommended")  
    lines.append("")  
    for f in ticket.recommended_fields:  
        lines.append(f"- { _md(f) }")  
    lines.append("")  
  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def support_escalation_to_json() -> str:  
    roles = get_support_roles()  
    severities = get_severity_levels()  
    targets = get_response_targets()  
    matrix = get_escalation_matrix()  
    ticket = get_incident_ticket_requirements()  
  
    payload: Dict[str, object] = {  
        "roles": [  
            {  
                "role_id": r.role_id,  
                "name": r.name,  
                "responsibilities": list(r.responsibilities),  
            }  
            for r in roles  
        ],  
        "severity_levels": [  
            {  
                "sev": s.sev,  
                "definition": s.definition,  
                "examples": list(s.examples),  
            }  
            for s in severities  
        ],  
        "response_targets": [  
            {  
                "sev": t.sev,  
                "initial_response": t.initial_response,  
                "update_frequency": t.update_frequency,  
                "mitigation_target": t.mitigation_target,  
            }  
            for t in targets  
        ],  
        "escalation_matrix": [  
            {  
                "rule_id": e.rule_id,  
                "trigger": e.trigger,  
                "escalate_to": e.escalate_to,  
                "notes": e.notes,  
            }  
            for e in matrix  
        ],  
        "incident_ticket_requirements": {  
            "required_fields": list(ticket.required_fields),  
            "recommended_fields": list(ticket.recommended_fields),  
        },  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_support_escalation_markdown(path: str) -> None:  
    roles = get_support_roles()  
    severities = get_severity_levels()  
    targets = get_response_targets()  
    matrix = get_escalation_matrix()  
    ticket = get_incident_ticket_requirements()  
    md = render_support_escalation_markdown(roles, severities, targets, matrix, ticket)  
    write_text_file(path, md)  