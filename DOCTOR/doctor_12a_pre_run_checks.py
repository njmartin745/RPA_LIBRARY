"""  
DOCTOR-12A: Pre-run DOCTOR Checks Policy (Milestone 12.4.1)  
  
Single responsibility:  
- Define a deterministic pre-run DOCTOR policy (especially for production).  
- Provide a pure evaluator that decides pass/fail from supplied evidence.  
- Provide deterministic renderers (Markdown/JSON) for operator-facing documentation.  
  
Determinism constraints:  
- No timestamps.  
- Stable ordering (sorted by check_id).  
- JSON rendering uses sort_keys=True.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union  
import json  
  
  
__all__ = [  
    "DoctorCheck",  
    "DoctorPolicy",  
    "DoctorDecision",  
    "get_doctor_policy",  
    "evaluate_doctor_policy",  
    "policy_to_json",  
    "render_policy_markdown",  
    "decision_to_json",  
    "render_decision_markdown",  
    "write_text_file",  
    "write_policy_json",  
    "write_policy_markdown",  
    "write_decision_json",  
    "write_decision_markdown",  
]  
  
  
JsonScalar = Union[str, int, float, bool, None]  
  
  
@dataclass(frozen=True, slots=True)  
class DoctorCheck:  
    """  
    A single pre-run check.  
  
    Evidence evaluation rules:  
    - If expected_value is None: evidence value must be truthy (bool(value) is True)  
    - Else: evidence value must equal expected_value  
    """  
    check_id: str  
    description: str  
    evidence_key: str  
    expected_value: Optional[JsonScalar] = None  
  
  
@dataclass(frozen=True, slots=True)  
class DoctorPolicy:  
    policy_id: str  
    title: str  
    env_checks: Dict[str, List[DoctorCheck]]  # e.g. {"prod": [...], "default": [...]}  
    notes: List[str]  
  
  
@dataclass(frozen=True, slots=True)  
class DoctorDecision:  
    policy_id: str  
    env: str  
    passed: bool  
    failed_checks: List[str]  
    missing_evidence: List[str]  
    details: List[str]  
  
  
def _sorted_checks(checks: Sequence[DoctorCheck]) -> List[DoctorCheck]:  
    return sorted(list(checks), key=lambda c: c.check_id)  
  
  
def get_doctor_policy(  
    *,  
    policy_id: str = "DOCTOR-PRE-RUN-12A",  
    title: str = "Pre-run DOCTOR Checks",  
    notes: Optional[Sequence[str]] = None,  
) -> DoctorPolicy:  
    """  
    Canonical pre-run checks policy.  
  
    This module does NOT perform live environment checks. It defines what must be  
    checked, and evaluates based on supplied evidence.  
    """  
    n = list(notes) if notes is not None else [  
        "This policy is deterministic and contains no generated timestamps.",  
        "Evaluation is evidence-based: callers must supply evidence for each required key.",  
        "In production, all listed checks are required to pass before a run proceeds.",  
    ]  
  
    # Production checks (evidence keys are intentionally generic and runner-agnostic)  
    prod_checks = _sorted_checks([  
        DoctorCheck(  
            check_id="doctor.webdriver_ready",  
            description="WebDriver is available and can start a session (or remote grid reachable).",  
            evidence_key="webdriver_ready",  
            expected_value=True,  
        ),  
        DoctorCheck(  
            check_id="doctor.workflow_loaded",  
            description="Workflow is loaded and structurally readable (pre-run load succeeded).",  
            evidence_key="workflow_loaded",  
            expected_value=True,  
        ),  
        DoctorCheck(  
            check_id="doctor.selectors_loaded",  
            description="Selectors bundle is loaded and queryable (pre-run load succeeded).",  
            evidence_key="selectors_loaded",  
            expected_value=True,  
        ),  
        DoctorCheck(  
            check_id="doctor.secrets_resolved",  
            description="All required secrets are resolvable (no missing secret bindings).",  
            evidence_key="secrets_resolved",  
            expected_value=True,  
        ),  
        DoctorCheck(  
            check_id="doctor.output_dir_writable",  
            description="Output/artifacts directory is writable (logs/screenshots/reports).",  
            evidence_key="output_dir_writable",  
            expected_value=True,  
        ),  
        DoctorCheck(  
            check_id="doctor.target_reachable",  
            description="Target base URL / critical endpoints are reachable (per environment).",  
            evidence_key="target_reachable",  
            expected_value=True,  
        ),  
    ])  
  
    # Default (non-prod) checks can be empty or lighter; keep deterministic structure.  
    default_checks = _sorted_checks([  
        DoctorCheck(  
            check_id="doctor.workflow_loaded",  
            description="Workflow is loaded and structurally readable (pre-run load succeeded).",  
            evidence_key="workflow_loaded",  
            expected_value=True,  
        ),  
        DoctorCheck(  
            check_id="doctor.selectors_loaded",  
            description="Selectors bundle is loaded and queryable (pre-run load succeeded).",  
            evidence_key="selectors_loaded",  
            expected_value=True,  
        ),  
    ])  
  
    env_checks = {  
        "default": default_checks,  
        "prod": prod_checks,  
    }  
  
    return DoctorPolicy(  
        policy_id=policy_id,  
        title=title,  
        env_checks=env_checks,  
        notes=n,  
    )  
  
  
def _evaluate_check(check: DoctorCheck, evidence: Mapping[str, object]) -> Tuple[bool, Optional[str]]:  
    if check.evidence_key not in evidence:  
        return False, f"Missing evidence key: {check.evidence_key} ({check.check_id})"  
  
    val = evidence[check.evidence_key]  
  
    if check.expected_value is None:  
        ok = bool(val) is True  
        if not ok:  
            return False, f"Failed {check.check_id}: expected truthy for '{check.evidence_key}', got {val!r}"  
        return True, f"Passed {check.check_id}"  
  
    ok = val == check.expected_value  
    if not ok:  
        return False, (  
            f"Failed {check.check_id}: expected '{check.evidence_key}' == {check.expected_value!r}, got {val!r}"  
        )  
    return True, f"Passed {check.check_id}"  
  
  
def evaluate_doctor_policy(  
    policy: DoctorPolicy,  
    *,  
    env: str,  
    evidence: Mapping[str, object],  
) -> DoctorDecision:  
    """  
    Pure evaluation: decides pass/fail based on policy + supplied evidence.  
    """  
    checks = policy.env_checks.get(env, policy.env_checks.get("default", []))  
    checks = _sorted_checks(checks)  
  
    failed: List[str] = []  
    missing: List[str] = []  
    details: List[str] = []  
  
    for c in checks:  
        ok, msg = _evaluate_check(c, evidence)  
        if msg:  
            details.append(msg)  
        if not ok:  
            failed.append(c.check_id)  
            if c.evidence_key not in evidence:  
                missing.append(c.evidence_key)  
  
    # Stable ordering  
    failed_sorted = sorted(set(failed))  
    missing_sorted = sorted(set(missing))  
    passed = (len(failed_sorted) == 0)  
  
    return DoctorDecision(  
        policy_id=policy.policy_id,  
        env=env,  
        passed=passed,  
        failed_checks=failed_sorted,  
        missing_evidence=missing_sorted,  
        details=details,  
    )  
  
  
def policy_to_json(policy: DoctorPolicy) -> str:  
    payload: Dict[str, object] = {  
        "policy_id": policy.policy_id,  
        "title": policy.title,  
        "env_checks": {  
            env: [  
                {  
                    "check_id": c.check_id,  
                    "description": c.description,  
                    "evidence_key": c.evidence_key,  
                    "expected_value": c.expected_value,  
                }  
                for c in _sorted_checks(checks)  
            ]  
            for env, checks in sorted(policy.env_checks.items(), key=lambda kv: kv[0])  
        },  
        "notes": list(policy.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_policy_markdown(policy: DoctorPolicy) -> str:  
    lines: List[str] = []  
    lines.append(f"# { _md(policy.title) }")  
    lines.append("")  
    lines.append(f"**Policy ID:** { _md(policy.policy_id) }")  
    lines.append("")  
    for env, checks in sorted(policy.env_checks.items(), key=lambda kv: kv[0]):  
        lines.append(f"## Environment: { _md(env) }")  
        lines.append("")  
        if not checks:  
            lines.append("(No checks defined)")  
            lines.append("")  
            continue  
        for c in _sorted_checks(checks):  
            lines.append(f"- **{ _md(c.check_id) }**")  
            lines.append(f"  - Evidence key: `{ _md(c.evidence_key) }`")  
            if c.expected_value is None:  
                lines.append("  - Expected: truthy")  
            else:  
                lines.append(f"  - Expected: `{c.expected_value!r}`")  
            lines.append(f"  - Description: { _md(c.description) }")  
        lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in policy.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def decision_to_json(decision: DoctorDecision) -> str:  
    payload: Dict[str, object] = {  
        "policy_id": decision.policy_id,  
        "env": decision.env,  
        "passed": decision.passed,  
        "failed_checks": list(decision.failed_checks),  
        "missing_evidence": list(decision.missing_evidence),  
        "details": list(decision.details),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def render_decision_markdown(decision: DoctorDecision) -> str:  
    lines: List[str] = []  
    lines.append("# DOCTOR Pre-run Decision")  
    lines.append("")  
    lines.append(f"**Policy ID:** { _md(decision.policy_id) }")  
    lines.append(f"**Environment:** { _md(decision.env) }")  
    lines.append("")  
    lines.append(f"**Passed:** `{decision.passed}`")  
    lines.append("")  
    if decision.failed_checks:  
        lines.append("## Failed Checks")  
        lines.append("")  
        for c in decision.failed_checks:  
            lines.append(f"- { _md(c) }")  
        lines.append("")  
    if decision.missing_evidence:  
        lines.append("## Missing Evidence Keys")  
        lines.append("")  
        for k in decision.missing_evidence:  
            lines.append(f"- `{ _md(k) }`")  
        lines.append("")  
    lines.append("## Details")  
    lines.append("")  
    for d in decision.details:  
        lines.append(f"- { _md(d) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_policy_json(path: str, policy: DoctorPolicy) -> None:  
    write_text_file(path, policy_to_json(policy))  
  
  
def write_policy_markdown(path: str, policy: DoctorPolicy) -> None:  
    write_text_file(path, render_policy_markdown(policy))  
  
  
def write_decision_json(path: str, decision: DoctorDecision) -> None:  
    write_text_file(path, decision_to_json(decision))  
  
  
def write_decision_markdown(path: str, decision: DoctorDecision) -> None:  
    write_text_file(path, render_decision_markdown(decision))  