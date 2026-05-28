"""  
DOC-12D: Rollback and Recovery Procedures (Milestone 12.4.3)  
  
Single responsibility:  
- Provide a canonical, deterministic rollback/recovery playbook structure for operators.  
- Provide deterministic renderers (Markdown/JSON) and a minimal validator.  
  
Determinism:  
- No timestamps generated.  
- Stable ordering (procedures sorted by procedure_id).  
- JSON uses sort_keys=True.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Dict, List, Optional, Sequence  
import json  
  
  
__all__ = [  
    "PlaybookStep",  
    "Procedure",  
    "RollbackRecoveryPlaybook",  
    "get_rollback_recovery_playbook",  
    "validate_playbook",  
    "playbook_to_json",  
    "render_playbook_markdown",  
    "write_text_file",  
    "write_playbook_json",  
    "write_playbook_markdown",  
]  
  
  
@dataclass(frozen=True, slots=True)  
class PlaybookStep:  
    step_id: str  
    text: str  
  
  
@dataclass(frozen=True, slots=True)  
class Procedure:  
    """  
    A rollback or recovery procedure.  
    """  
    procedure_id: str  
    title: str  
    category: str  # "rollback" | "recovery"  
    when_to_use: List[str]  
    prerequisites: List[str]  
    steps: List[PlaybookStep]  
    verification: List[str]  
    escalation: List[str]  
  
  
@dataclass(frozen=True, slots=True)  
class RollbackRecoveryPlaybook:  
    playbook_id: str  
    title: str  
    procedures: List[Procedure]  
    notes: List[str]  
  
  
def _sorted_procedures(procs: Sequence[Procedure]) -> List[Procedure]:  
    return sorted(list(procs), key=lambda p: p.procedure_id)  
  
  
def get_rollback_recovery_playbook(  
    *,  
    playbook_id: str = "RR-PLAYBOOK-12D",  
    title: str = "Rollback and Recovery Procedures",  
    notes: Optional[Sequence[str]] = None,  
) -> RollbackRecoveryPlaybook:  
    n = list(notes) if notes is not None else [  
        "This playbook is deterministic and contains no generated timestamps.",  
        "Procedures are written to be framework-agnostic; integrate with your CI/CD and RUN wrappers.",  
        "Always preserve artifacts (logs/screenshots/reports) before rollback where possible.",  
    ]  
  
    rollback_fast = Procedure(  
        procedure_id="rollback.fast_disable_prod",  
        title="Fast rollback: disable production schedule / stop new runs",  
        category="rollback",  
        when_to_use=[  
            "Production runs are failing broadly due to recent change.",  
            "System instability or external dependency outage makes continued runs unsafe.",  
        ],  
        prerequisites=[  
            "Access to scheduler/orchestrator (e.g., Task Scheduler/cron/CI schedule).",  
            "Access to run host(s) to stop any currently running job if needed.",  
        ],  
        steps=[  
            PlaybookStep(step_id="1", text="Disable the production schedule / stop triggering new runs."),  
            PlaybookStep(step_id="2", text="If a run is currently executing, stop it only if safe to do so (avoid partial writes)."),  
            PlaybookStep(step_id="3", text="Capture/retain artifacts from the last known failing run (logs, screenshots, reports, bundle fingerprint)."),  
            PlaybookStep(step_id="4", text="Notify stakeholders: rollout paused; investigation in progress."),  
        ],  
        verification=[  
            "No new runs start in production.",  
            "Artifacts retained and linked to incident/ticket.",  
        ],  
        escalation=[  
            "Escalate to on-call if production impact persists beyond SLO response targets.",  
        ],  
    )  
  
    rollback_bundle = Procedure(  
        procedure_id="rollback.revert_to_previous_bundle",  
        title="Rollback: revert to last known-good bundle",  
        category="rollback",  
        when_to_use=[  
            "A specific bundle version is identified as causing regressions.",  
            "You have a previous versioned bundle fingerprint that passed promotion gates.",  
        ],  
        prerequisites=[  
            "Access to the bundle repository/location holding versioned artifacts.",  
            "A known-good fingerprint/manifest/promotion record for the prior version.",  
        ],  
        steps=[  
            PlaybookStep(step_id="1", text="Identify last known-good bundle version (from manifests/promotion records)."),  
            PlaybookStep(step_id="2", text="Deploy/activate the prior bundle in the production run location."),  
            PlaybookStep(step_id="3", text="Confirm selectors/workflow versions match the intended rollback bundle."),  
            PlaybookStep(step_id="4", text="Re-enable production schedule (or trigger a controlled single run)."),  
        ],  
        verification=[  
            "A controlled run completes successfully with the rolled-back bundle.",  
            "Run outcomes and key outputs return to expected levels.",  
        ],  
        escalation=[  
            "If rollback does not restore success, disable schedule and escalate to engineering + ops.",  
        ],  
    )  
  
    recovery_rerun = Procedure(  
        procedure_id="recovery.safe_rerun_with_controls",  
        title="Recovery: safe re-run with controls (after incident)",  
        category="recovery",  
        when_to_use=[  
            "Production runs were paused and you are restoring service.",  
            "A fix is deployed or external dependency has recovered.",  
        ],  
        prerequisites=[  
            "A verified bundle (manifest + fingerprint) is deployed.",  
            "DOCTOR pre-run checks pass in production.",  
            "GUARD production policy evaluation passes for the workflow/selectors.",  
        ],  
        steps=[  
            PlaybookStep(step_id="1", text="Run DOCTOR pre-run checks; confirm all required evidence is green."),  
            PlaybookStep(step_id="2", text="Evaluate GUARD policies against the intended workflow/selectors bundle."),  
            PlaybookStep(step_id="3", text="Trigger a single controlled production run (not scheduled) and observe."),  
            PlaybookStep(step_id="4", text="If successful, restore normal scheduling and continue monitoring."),  
        ],  
        verification=[  
            "Controlled run passes and produces expected artifacts/outputs.",  
            "Monitoring indicates stability for a defined observation window.",  
        ],  
        escalation=[  
            "If controlled run fails, keep schedule disabled and follow rollback procedures.",  
        ],  
    )  
  
    procedures = _sorted_procedures([rollback_fast, rollback_bundle, recovery_rerun])  
  
    return RollbackRecoveryPlaybook(  
        playbook_id=playbook_id,  
        title=title,  
        procedures=procedures,  
        notes=n,  
    )  
  
  
def validate_playbook(playbook: RollbackRecoveryPlaybook) -> List[str]:  
    """  
    Minimal deterministic validator. Returns list of error strings (empty => valid).  
    """  
    errors: List[str] = []  
    if not playbook.playbook_id:  
        errors.append("playbook_id is required")  
    if not playbook.title:  
        errors.append("title is required")  
    if not playbook.procedures:  
        errors.append("At least one procedure is required")  
  
    seen = set()  
    for p in playbook.procedures:  
        if not p.procedure_id:  
            errors.append("procedure_id is required")  
        if p.procedure_id in seen:  
            errors.append(f"Duplicate procedure_id: {p.procedure_id}")  
        seen.add(p.procedure_id)  
        if p.category not in ("rollback", "recovery"):  
            errors.append(f"Invalid category for {p.procedure_id}: {p.category!r}")  
        if not p.steps:  
            errors.append(f"Procedure has no steps: {p.procedure_id}")  
  
    return errors  
  
  
def playbook_to_json(playbook: RollbackRecoveryPlaybook) -> str:  
    payload: Dict[str, object] = {  
        "playbook_id": playbook.playbook_id,  
        "title": playbook.title,  
        "procedures": [  
            {  
                "procedure_id": p.procedure_id,  
                "title": p.title,  
                "category": p.category,  
                "when_to_use": list(p.when_to_use),  
                "prerequisites": list(p.prerequisites),  
                "steps": [{"step_id": s.step_id, "text": s.text} for s in p.steps],  
                "verification": list(p.verification),  
                "escalation": list(p.escalation),  
            }  
            for p in _sorted_procedures(playbook.procedures)  
        ],  
        "notes": list(playbook.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_playbook_markdown(playbook: RollbackRecoveryPlaybook) -> str:  
    lines: List[str] = []  
    lines.append(f"# { _md(playbook.title) }")  
    lines.append("")  
    lines.append(f"**Playbook ID:** { _md(playbook.playbook_id) }")  
    lines.append("")  
    for p in _sorted_procedures(playbook.procedures):  
        lines.append(f"## { _md(p.title) }")  
        lines.append("")  
        lines.append(f"- **Procedure ID:** `{ _md(p.procedure_id) }`")  
        lines.append(f"- **Category:** `{ _md(p.category) }`")  
        lines.append("")  
        lines.append("### When to use")  
        lines.append("")  
        for x in p.when_to_use:  
            lines.append(f"- { _md(x) }")  
        lines.append("")  
        lines.append("### Prerequisites")  
        lines.append("")  
        for x in p.prerequisites:  
            lines.append(f"- { _md(x) }")  
        lines.append("")  
        lines.append("### Steps")  
        lines.append("")  
        for s in p.steps:  
            lines.append(f"{ _md(s.step_id) }. { _md(s.text) }")  
        lines.append("")  
        lines.append("### Verification")  
        lines.append("")  
        for x in p.verification:  
            lines.append(f"- { _md(x) }")  
        lines.append("")  
        lines.append("### Escalation")  
        lines.append("")  
        for x in p.escalation:  
            lines.append(f"- { _md(x) }")  
        lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in playbook.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_playbook_json(path: str, playbook: RollbackRecoveryPlaybook) -> None:  
    write_text_file(path, playbook_to_json(playbook))  
  
  
def write_playbook_markdown(path: str, playbook: RollbackRecoveryPlaybook) -> None:  
    write_text_file(path, render_playbook_markdown(playbook))  