"""  
DOCTOR-12D: Release Readiness Gate (Milestone 12.5.6)  
  
Single responsibility:  
- Provide a deterministic "release readiness" gate:  
  - canonical readiness policy (required checks by env)  
  - pure evaluator that consumes caller-supplied observations  
  - deterministic JSON/Markdown renderers  
  
Determinism:  
- No timestamps generated.  
- Stable ordering by check_id.  
- JSON uses sort_keys=True.  
  
This module does NOT execute workflows and does NOT mutate state.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple  
import json  
  
  
__all__ = [  
    "CheckSpec",  
    "ReadinessPolicy",  
    "CheckObservation",  
    "CheckResult",  
    "ReadinessDecision",  
    "get_readiness_policy",  
    "validate_readiness_policy",  
    "evaluate_readiness",  
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
  
  
_ALLOWED_SEVERITIES = ("info", "warning", "critical")  
  
  
@dataclass(frozen=True, slots=True)  
class CheckSpec:  
    check_id: str  
    severity: str  # info|warning|critical  
    description: str  
  
  
@dataclass(frozen=True, slots=True)  
class ReadinessPolicy:  
    policy_id: str  
    title: str  
    env_checks: Dict[str, Tuple[CheckSpec, ...]]  # includes "default"  
    notes: Tuple[str, ...]  
  
  
@dataclass(frozen=True, slots=True)  
class CheckObservation:  
    """  
    Caller-supplied observation for a check.  
  
    - passed: whether the check passed.  
    - message: short explanation (optional)  
    - data: structured details (optional, JSON-serializable)  
    """  
    passed: bool  
    message: str = ""  
    data: Optional[Dict[str, Any]] = None  
  
  
@dataclass(frozen=True, slots=True)  
class CheckResult:  
    check_id: str  
    severity: str  
    passed: bool  
    required: bool  
    message: str  
    data: Optional[Dict[str, Any]]  
  
  
@dataclass(frozen=True, slots=True)  
class ReadinessDecision:  
    policy_id: str  
    env: str  
    passed: bool  
    results: List[CheckResult]  
    summary: Dict[str, int]  
    notes: List[str]  
  
  
def get_readiness_policy(  
    *,  
    policy_id: str = "READINESS-GATE-12D",  
    title: str = "Release Readiness Gate",  
    notes: Optional[Sequence[str]] = None,  
) -> ReadinessPolicy:  
    """  
    Canonical baseline readiness checks.  
  
    These check_ids are intentionally generic so other layers can map their outputs:  
      - lint.steps_valid  
      - workflow.loaded  
      - replay.index_verified  
      - alerts.signals_passed  
      - audit.log_present  
      - retention.policy_valid  
      - incident.packet_ready (info)  
    """  
    n = tuple(notes) if notes is not None else (  
        "This gate is deterministic and contains no generated timestamps.",  
        "Missing required checks are treated as failures.",  
        "Overall pass requires all required checks of severity warning/critical to pass.",  
        "info checks never block the gate (but are reported).",  
    )  
  
    default_checks = (  
        CheckSpec("lint.steps_valid", "critical", "Workflow steps validated against schema and allowed actions"),  
        CheckSpec("workflow.loaded", "critical", "Workflow bundle loaded successfully"),  
        CheckSpec("replay.index_verified", "warning", "Replay artifacts are internally consistent (hash/index)"),  
        CheckSpec("alerts.signals_passed", "warning", "Alerting signal window indicates healthy run outcomes"),  
        CheckSpec("audit.log_present", "warning", "Audit log (JSONL) available for the run/window"),  
        CheckSpec("retention.policy_valid", "info", "Artifact retention policy validated"),  
        CheckSpec("incident.packet_ready", "info", "Incident packet manifest template prepared (for ops readiness)"),  
    )  
  
    prod_checks = (  
        CheckSpec("lint.steps_valid", "critical", "Workflow steps validated against schema and allowed actions"),  
        CheckSpec("workflow.loaded", "critical", "Workflow bundle loaded successfully"),  
        CheckSpec("replay.index_verified", "critical", "Replay artifacts are internally consistent (hash/index)"),  
        CheckSpec("alerts.signals_passed", "critical", "Alerting signal window indicates healthy run outcomes"),  
        CheckSpec("audit.log_present", "warning", "Audit log (JSONL) available for the run/window"),  
        CheckSpec("retention.policy_valid", "warning", "Artifact retention policy validated"),  
        CheckSpec("incident.packet_ready", "info", "Incident packet manifest template prepared (for ops readiness)"),  
    )  
  
    return ReadinessPolicy(  
        policy_id=policy_id,  
        title=title,  
        env_checks={"default": default_checks, "prod": prod_checks},  
        notes=n,  
    )  
  
  
def validate_readiness_policy(policy: ReadinessPolicy) -> List[str]:  
    errs: List[str] = []  
    if not policy.policy_id:  
        errs.append("policy_id is required")  
    if "default" not in policy.env_checks:  
        errs.append("env_checks must include 'default'")  
    for env, checks in policy.env_checks.items():  
        if not env:  
            errs.append("env key must be non-empty")  
        seen = set()  
        for c in checks:  
            if not c.check_id:  
                errs.append(f"{env}: check_id is required")  
            if c.check_id in seen:  
                errs.append(f"{env}: duplicate check_id: {c.check_id!r}")  
            seen.add(c.check_id)  
            if c.severity not in _ALLOWED_SEVERITIES:  
                errs.append(f"{env}:{c.check_id}: invalid severity {c.severity!r}")  
            if not isinstance(c.description, str):  
                errs.append(f"{env}:{c.check_id}: description must be str")  
    return errs  
  
  
def _checks_for_env(policy: ReadinessPolicy, env: str) -> Tuple[CheckSpec, ...]:  
    return policy.env_checks.get(env, policy.env_checks["default"])  
  
  
def evaluate_readiness(  
    policy: ReadinessPolicy,  
    *,  
    env: str,  
    observations: Mapping[str, CheckObservation],  
) -> ReadinessDecision:  
    """  
    Pure evaluator: combines policy-required checks with caller-supplied observations.  
    Missing required check => failed result with message "Missing observation".  
  
    Pass criteria:  
    - Any failed required check with severity in {warning, critical} => overall fail.  
    - info checks never block the gate.  
    """  
    per_env = _checks_for_env(policy, env)  
  
    results: List[CheckResult] = []  
    notes: List[str] = []  
  
    # Required checks from policy  
    required_by_id: Dict[str, CheckSpec] = {c.check_id: c for c in per_env}  
  
    for check_id in sorted(required_by_id.keys()):  
        spec = required_by_id[check_id]  
        obs = observations.get(check_id)  
        if obs is None:  
            results.append(  
                CheckResult(  
                    check_id=check_id,  
                    severity=spec.severity,  
                    passed=False,  
                    required=True,  
                    message="Missing observation",  
                    data=None,  
                )  
            )  
        else:  
            results.append(  
                CheckResult(  
                    check_id=check_id,  
                    severity=spec.severity,  
                    passed=bool(obs.passed),  
                    required=True,  
                    message=str(obs.message or ""),  
                    data=dict(obs.data) if obs.data is not None else None,  
                )  
            )  
  
    # Extra observations (not in policy) are included as non-required info  
    extra_ids = sorted([k for k in observations.keys() if k not in required_by_id])  
    for check_id in extra_ids:  
        obs = observations[check_id]  
        results.append(  
            CheckResult(  
                check_id=check_id,  
                severity="info",  
                passed=bool(obs.passed),  
                required=False,  
                message=str(obs.message or "Extra observation"),  
                data=dict(obs.data) if obs.data is not None else None,  
            )  
        )  
        notes.append(f"Extra observation provided: {check_id}")  
  
    # Summary + pass/fail  
    summary: Dict[str, int] = {  
        "total": len(results),  
        "required.total": len(required_by_id),  
        "required.passed": 0,  
        "required.failed": 0,  
        "failed.critical": 0,  
        "failed.warning": 0,  
        "failed.info": 0,  
    }  
  
    blocking_fail = False  
    for r in results:  
        if r.required:  
            if r.passed:  
                summary["required.passed"] += 1  
            else:  
                summary["required.failed"] += 1  
  
        if not r.passed:  
            summary[f"failed.{r.severity}"] = summary.get(f"failed.{r.severity}", 0) + 1  
            if r.required and r.severity in ("warning", "critical"):  
                blocking_fail = True  
  
    passed = not blocking_fail  
  
    return ReadinessDecision(  
        policy_id=policy.policy_id,  
        env=env,  
        passed=passed,  
        results=sorted(results, key=lambda x: (x.check_id, x.required is False, x.severity)),  
        summary=summary,  
        notes=notes,  
    )  
  
  
def policy_to_json(policy: ReadinessPolicy) -> str:  
    payload: Dict[str, Any] = {  
        "policy_id": policy.policy_id,  
        "title": policy.title,  
        "env_checks": {  
            env: [  
                {"check_id": c.check_id, "severity": c.severity, "description": c.description}  
                for c in sorted(list(checks), key=lambda x: x.check_id)  
            ]  
            for env, checks in sorted(policy.env_checks.items(), key=lambda kv: kv[0])  
        },  
        "notes": list(policy.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_policy_markdown(policy: ReadinessPolicy) -> str:  
    lines: List[str] = []  
    lines.append(f"# { _md(policy.title) }")  
    lines.append("")  
    lines.append(f"**Policy ID:** { _md(policy.policy_id) }")  
    lines.append("")  
    lines.append("## Checks by Environment")  
    lines.append("")  
    for env, checks in sorted(policy.env_checks.items(), key=lambda kv: kv[0]):  
        lines.append(f"### { _md(env) }")  
        lines.append("")  
        for c in sorted(list(checks), key=lambda x: x.check_id):  
            lines.append(f"- `{_md(c.check_id)}` (**{_md(c.severity)}**) — { _md(c.description) }")  
        lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in policy.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def decision_to_json(decision: ReadinessDecision) -> str:  
    payload: Dict[str, Any] = {  
        "policy_id": decision.policy_id,  
        "env": decision.env,  
        "passed": decision.passed,  
        "summary": dict(decision.summary),  
        "results": [  
            {  
                "check_id": r.check_id,  
                "severity": r.severity,  
                "passed": r.passed,  
                "required": r.required,  
                "message": r.message,  
                "data": r.data,  
            }  
            for r in decision.results  
        ],  
        "notes": list(decision.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def render_decision_markdown(decision: ReadinessDecision) -> str:  
    lines: List[str] = []  
    lines.append("# Release Readiness Decision")  
    lines.append("")  
    lines.append(f"**Policy ID:** { _md(decision.policy_id) }")  
    lines.append(f"**Environment:** `{ _md(decision.env) }`")  
    lines.append("")  
    lines.append(f"**Passed:** `{decision.passed}`")  
    lines.append("")  
    lines.append("## Summary")  
    lines.append("")  
    for k, v in sorted(decision.summary.items(), key=lambda kv: kv[0]):  
        lines.append(f"- { _md(k) }: `{v}`")  
    lines.append("")  
    lines.append("## Results")  
    lines.append("")  
    for r in decision.results:  
        req = "required" if r.required else "extra"  
        status = "PASS" if r.passed else "FAIL"  
        msg = f" — { _md(r.message) }" if r.message else ""  
        lines.append(f"- {status} `{_md(r.check_id)}` ({req}, **{_md(r.severity)}**){msg}")  
    lines.append("")  
    if decision.notes:  
        lines.append("## Notes")  
        lines.append("")  
        for n in decision.notes:  
            lines.append(f"- { _md(n) }")  
        lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_policy_json(path: str, policy: ReadinessPolicy) -> None:  
    write_text_file(path, policy_to_json(policy))  
  
  
def write_policy_markdown(path: str, policy: ReadinessPolicy) -> None:  
    write_text_file(path, render_policy_markdown(policy))  
  
  
def write_decision_json(path: str, decision: ReadinessDecision) -> None:  
    write_text_file(path, decision_to_json(decision))  
  
  
def write_decision_markdown(path: str, decision: ReadinessDecision) -> None:  
    write_text_file(path, render_decision_markdown(decision))  