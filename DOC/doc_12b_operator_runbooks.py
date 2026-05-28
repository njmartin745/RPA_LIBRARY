"""  
DOC-12B: Operator Runbooks (Milestone 12.1.2)  
  
Single responsibility:  
- Provide deterministic, reviewable operator runbooks for production operation  
  of the Selenium RPA framework.  
- Provide pure renderers to Markdown/JSON for operator-facing documentation.  
  
Notes:  
- This module avoids hard-coding environment-specific commands. Where CLI entry  
  points vary by installation, steps call out "use your standard runner entry point".  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import List, Sequence  
import json  
  
  
__all__ = [  
    "RunbookStep",  
    "Runbook",  
    "get_operator_runbooks",  
    "render_runbooks_markdown",  
    "runbooks_to_json",  
    "write_text_file",  
    "write_operator_runbooks_markdown",  
]  
  
  
@dataclass(frozen=True, slots=True)  
class RunbookStep:  
    """  
    A single operator action step.  
  
    Keep steps human-actionable and auditable.  
    """  
    step_id: str  
    action: str  
    expected: str  
  
  
@dataclass(frozen=True, slots=True)  
class Runbook:  
    """  
    An operator runbook with prerequisites and a deterministic ordered procedure.  
    """  
    runbook_id: str  
    title: str  
    intent: str  
    prerequisites: List[str]  
    steps: List[RunbookStep]  
    rollback: List[str]  
    artifacts: List[str]  
  
  
def get_operator_runbooks() -> List[Runbook]:  
    """  
    Canonical set of runbooks. Ordering is stable for reviewable diffs.  
    """  
    return [  
        Runbook(  
            runbook_id="RB-OPS-001",  
            title="Start a production run (standard execution)",  
            intent="Safely execute a released workflow bundle in production and capture required artifacts.",  
            prerequisites=[  
                "You have the approved release bundle + its immutable fingerprint (if applicable).",  
                "You have access to the production execution environment.",  
                "Secrets are available via the approved secret mechanism (never embedded in workflow files).",  
            ],  
            steps=[  
                RunbookStep(  
                    step_id="RB-OPS-001-01",  
                    action="Run pre-flight checks (DOCTOR) according to your production policy.",  
                    expected="Pre-flight checks pass; any failures are resolved or escalated before proceeding.",  
                ),  
                RunbookStep(  
                    step_id="RB-OPS-001-02",  
                    action="Execute the workflow using your standard runner entry point with the intended inputs.",  
                    expected="Runner starts and a run identifier (run_id) is captured.",  
                ),  
                RunbookStep(  
                    step_id="RB-OPS-001-03",  
                    action="Monitor the run until completion using standard logs/output capture.",  
                    expected="Run completes with a success status, or fails with recorded diagnostics.",  
                ),  
                RunbookStep(  
                    step_id="RB-OPS-001-04",  
                    action="Verify required artifacts exist and are stored per retention policy.",  
                    expected="Logs + report output (+ history/replay where configured) are present for the run_id.",  
                ),  
            ],  
            rollback=[  
                "If the run causes unintended side effects, follow RB-OPS-004 (Rollback a release / revert to last known-good bundle).",  
                "If an external system change must be reversed, follow the application-specific rollback SOP.",  
            ],  
            artifacts=[  
                "Runner stdout/stderr logs captured to a file",  
                "Report artifacts (framework-defined output directory)",  
                "Run metadata (run_id, workflow name/version, bundle fingerprint)",  
            ],  
        ),  
        Runbook(  
            runbook_id="RB-OPS-002",  
            title="Triage a failed run",  
            intent="Determine whether failure is workflow logic, selector drift, environment, or upstream dependency.",  
            prerequisites=[  
                "You have the run_id and access to logs and report artifacts.",  
                "You can re-run in a safe/non-destructive mode if your workflow supports it.",  
            ],  
            steps=[  
                RunbookStep(  
                    step_id="RB-OPS-002-01",  
                    action="Identify the first failing step in the captured step logs / trace.",  
                    expected="A specific step index/type and context are identified as the failure point.",  
                ),  
                RunbookStep(  
                    step_id="RB-OPS-002-02",  
                    action="Classify failure: selector mismatch, auth failure, navigation timing, upstream outage, or data issue.",  
                    expected="Failure class is documented with evidence (log excerpt + screenshot if available).",  
                ),  
                RunbookStep(  
                    step_id="RB-OPS-002-03",  
                    action="Check for recent changes: workflow diff, selector diff, environment/browser updates.",  
                    expected="You can attribute the issue to a change or confirm no changes occurred.",  
                ),  
                RunbookStep(  
                    step_id="RB-OPS-002-04",  
                    action="If safe, attempt a controlled re-run with identical inputs.",  
                    expected="Re-run outcome confirms deterministic behavior or indicates intermittent/external causes.",  
                ),  
                RunbookStep(  
                    step_id="RB-OPS-002-05",  
                    action="Escalate according to the support path if unresolved within your SLO policy timebox.",  
                    expected="Ticket/incident includes run_id, bundle fingerprint, failing step, and artifacts.",  
                ),  
            ],  
            rollback=[  
                "If failure correlates with a new release, follow RB-OPS-004 to revert to last known-good.",  
                "If failure is selector drift, follow your selector update process and require reviewable diffs.",  
            ],  
            artifacts=[  
                "Failing run logs and report outputs",  
                "Environment details (browser version, driver version, machine image/version)",  
                "Workflow/selector versions or fingerprints",  
            ],  
        ),  
        Runbook(  
            runbook_id="RB-OPS-003",  
            title="Re-run a workflow deterministically (replay procedure)",  
            intent="Re-run with the same inputs to confirm reproducibility and aid debugging.",  
            prerequisites=[  
                "The workflow is expected to be deterministic for the tested scenario.",  
                "You have the exact same input payload and configuration.",  
                "You have the original run_id artifacts for comparison.",  
            ],  
            steps=[  
                RunbookStep(  
                    step_id="RB-OPS-003-01",  
                    action="Confirm you are using the same released bundle (same version/fingerprint) as the original run.",  
                    expected="Bundle identity matches the original run records.",  
                ),  
                RunbookStep(  
                    step_id="RB-OPS-003-02",  
                    action="Re-run the workflow with identical inputs and configuration (including selectors bundle).",  
                    expected="A new run_id is produced; execution proceeds without ad-hoc operator changes.",  
                ),  
                RunbookStep(  
                    step_id="RB-OPS-003-03",  
                    action="Compare step ordering/trace between original and rerun (ignore timestamps).",  
                    expected="Step sequence matches for deterministic flows; differences are documented if present.",  
                ),  
            ],  
            rollback=[  
                "If re-run risks duplicate side effects (e.g., double submission), stop and use a sandbox or no-op mode.",  
            ],  
            artifacts=[  
                "Original and rerun logs",  
                "Original and rerun reports",  
                "Any history/replay traces used for comparison",  
            ],  
        ),  
        Runbook(  
            runbook_id="RB-OPS-004",  
            title="Rollback a release (revert to last known-good bundle)",  
            intent="Restore service by reverting workflow/selector/framework bundle to a last known-good state.",  
            prerequisites=[  
                "You have access to prior release artifacts and their fingerprints.",  
                "Promotion gates allow selecting a prior approved bundle.",  
                "You have approval per change-control policy (if required).",  
            ],  
            steps=[  
                RunbookStep(  
                    step_id="RB-OPS-004-01",  
                    action="Identify the last known-good bundle and confirm its fingerprint/version.",  
                    expected="Rollback target is clearly identified and approved.",  
                ),  
                RunbookStep(  
                    step_id="RB-OPS-004-02",  
                    action="Deploy/activate the prior bundle in the production environment.",  
                    expected="Runtime is now pointing to the rollback bundle.",  
                ),  
                RunbookStep(  
                    step_id="RB-OPS-004-03",  
                    action="Execute a smoke run (safe test) to confirm recovery.",  
                    expected="Smoke run passes; artifacts recorded for audit.",  
                ),  
                RunbookStep(  
                    step_id="RB-OPS-004-04",  
                    action="Open an incident/root-cause item for the regressed release and freeze further promotion if needed.",  
                    expected="Issue is tracked with evidence and next steps.",  
                ),  
            ],  
            rollback=[  
                "If rollback fails, escalate immediately and consider environment rollback (image/browser/driver).",  
            ],  
            artifacts=[  
                "Rollback decision record (who/when/why)",  
                "Rollback bundle fingerprint/version",  
                "Smoke run artifacts post-rollback",  
            ],  
        ),  
    ]  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_runbooks_markdown(runbooks: Sequence[Runbook]) -> str:  
    lines: List[str] = []  
    lines.append("# Operator Runbooks")  
    lines.append("")  
    lines.append("Canonical procedures for operating the RPA framework in production.")  
    lines.append("")  
    for rb in runbooks:  
        lines.append(f"## { _md(rb.runbook_id) }: { _md(rb.title) }")  
        lines.append("")  
        lines.append(f"**Intent:** { _md(rb.intent) }")  
        lines.append("")  
        lines.append("### Prerequisites")  
        lines.append("")  
        for p in rb.prerequisites:  
            lines.append(f"- { _md(p) }")  
        lines.append("")  
        lines.append("### Procedure")  
        lines.append("")  
        for step in rb.steps:  
            lines.append(f"#### { _md(step.step_id) }")  
            lines.append("")  
            lines.append(f"- **Action:** { _md(step.action) }")  
            lines.append(f"- **Expected:** { _md(step.expected) }")  
            lines.append("")  
        lines.append("### Rollback / Mitigation")  
        lines.append("")  
        for r in rb.rollback:  
            lines.append(f"- { _md(r) }")  
        lines.append("")  
        lines.append("### Required Artifacts")  
        lines.append("")  
        for a in rb.artifacts:  
            lines.append(f"- { _md(a) }")  
        lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def runbooks_to_json(runbooks: Sequence[Runbook]) -> str:  
    payload = []  
    for rb in runbooks:  
        payload.append(  
            {  
                "runbook_id": rb.runbook_id,  
                "title": rb.title,  
                "intent": rb.intent,  
                "prerequisites": list(rb.prerequisites),  
                "steps": [  
                    {"step_id": s.step_id, "action": s.action, "expected": s.expected}  
                    for s in rb.steps  
                ],  
                "rollback": list(rb.rollback),  
                "artifacts": list(rb.artifacts),  
            }  
        )  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_operator_runbooks_markdown(path: str) -> None:  
    runbooks = get_operator_runbooks()  
    md = render_runbooks_markdown(runbooks)  
    write_text_file(path, md)  