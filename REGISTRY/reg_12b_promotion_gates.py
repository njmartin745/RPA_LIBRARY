"""  
REG-12B: Promotion Gates Policy (Milestone 12.2.3)  
  
Single responsibility:  
- Define deterministic promotion gates between environments (e.g., dev->stage->prod).  
- Provide a pure evaluator to decide if a promotion is allowed based on evidence.  
- Provide deterministic renderers (Markdown/JSON) for governance documentation.  
  
This module is policy-only: it does not execute CI, run workflows, or integrate with  
ticketing systems. It is intended to be called by BUILD/CLI/CI later.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Dict, List, Mapping, Optional, Sequence, Tuple  
import json  
  
  
__all__ = [  
    "Gate",  
    "PromotionPath",  
    "PromotionPolicy",  
    "PromotionDecision",  
    "get_promotion_policy",  
    "evaluate_promotion",  
    "render_promotion_policy_markdown",  
    "promotion_policy_to_json",  
    "write_text_file",  
    "write_promotion_policy_markdown",  
]  
  
  
@dataclass(frozen=True, slots=True)  
class Gate:  
    gate_id: str  
    name: str  
    description: str  
    required_evidence_keys: List[str]  
    pass_criteria: str  
  
  
@dataclass(frozen=True, slots=True)  
class PromotionPath:  
    from_env: str  
    to_env: str  
    gates: List[Gate]  
  
  
@dataclass(frozen=True, slots=True)  
class PromotionPolicy:  
    policy_id: str  
    title: str  
    environments: List[str]  
    paths: List[PromotionPath]  
    notes: List[str]  
  
  
@dataclass(frozen=True, slots=True)  
class PromotionDecision:  
    allowed: bool  
    from_env: str  
    to_env: str  
    failed_gates: List[str]  
    missing_evidence: List[str]  
    details: List[str]  
  
  
def get_promotion_policy() -> PromotionPolicy:  
    """  
    Canonical promotion gates. Ordering is stable for reviewable diffs.  
    Evidence keys are intentionally generic so organizations can map them to CI checks.  
  
    Evidence values are expected to be truthy for pass (e.g., True or "PASS").  
    """  
    gate_schema_validation = Gate(  
        gate_id="GATE-VAL-001",  
        name="Schema validation passes",  
        description="All workflows in the promotion set are schema-valid and limited to supported actions.",  
        required_evidence_keys=["lint_steps_validator_passed"],  
        pass_criteria="lint_steps_validator_passed is truthy",  
    )  
    gate_reviewable_diffs = Gate(  
        gate_id="GATE-DIFF-001",  
        name="Reviewable diffs are available",  
        description="Workflow/selector changes are accompanied by unified diffs suitable for review.",  
        required_evidence_keys=["reviewable_diffs_attached"],  
        pass_criteria="reviewable_diffs_attached is truthy",  
    )  
    gate_smoke_suite = Gate(  
        gate_id="GATE-SMOKE-001",  
        name="Smoke suite passes",  
        description="Smoke tests and minimal end-to-end checks pass for the promotion candidate.",  
        required_evidence_keys=["smoke_suite_passed"],  
        pass_criteria="smoke_suite_passed is truthy",  
    )  
    gate_bundle_fingerprint = Gate(  
        gate_id="GATE-REL-001",  
        name="Bundle is versioned and fingerprinted",  
        description="Release artifacts are immutable and include version identifiers and/or fingerprints.",  
        required_evidence_keys=["bundle_fingerprint_recorded", "bundle_version_recorded"],  
        pass_criteria="bundle_fingerprint_recorded and bundle_version_recorded are truthy",  
    )  
    gate_doctor_required = Gate(  
        gate_id="GATE-OPS-001",  
        name="Operational preflight (DOCTOR) passes for target env",  
        description="Production/stage preflight checks (where required by policy) are executed and pass.",  
        required_evidence_keys=["doctor_checks_passed"],  
        pass_criteria="doctor_checks_passed is truthy",  
    )  
    gate_approval = Gate(  
        gate_id="GATE-CC-001",  
        name="Change-control approval recorded",  
        description="Required human approvals are recorded per governance policy (e.g., PR approval).",  
        required_evidence_keys=["change_control_approved"],  
        pass_criteria="change_control_approved is truthy",  
    )  
  
    environments = ["dev", "stage", "prod"]  
  
    paths = [  
        PromotionPath(  
            from_env="dev",  
            to_env="stage",  
            gates=[  
                gate_schema_validation,  
                gate_reviewable_diffs,  
                gate_smoke_suite,  
                gate_bundle_fingerprint,  
            ],  
        ),  
        PromotionPath(  
            from_env="stage",  
            to_env="prod",  
            gates=[  
                gate_schema_validation,  
                gate_reviewable_diffs,  
                gate_smoke_suite,  
                gate_bundle_fingerprint,  
                gate_doctor_required,  
                gate_approval,  
            ],  
        ),  
    ]  
  
    notes = [  
        "Promotion is denied if any gate fails or required evidence is missing.",  
        "Evidence keys should be produced by CI/BUILD pipelines and stored alongside release artifacts.",  
        "Emergency/hotfix promotions should still satisfy these gates unless a formal break-glass policy exists.",  
    ]  
  
    return PromotionPolicy(  
        policy_id="PG-12B",  
        title="Environment Promotion Gates Policy",  
        environments=environments,  
        paths=paths,  
        notes=notes,  
    )  
  
  
def _truthy(v: object) -> bool:  
    """  
    Deterministic evidence evaluation:  
    - bool: use value  
    - str: accept PASS/TRUE/YES/OK (case-insensitive) as truthy; otherwise falsy  
    - numbers: non-zero is truthy  
    - None/other: bool(v)  
    """  
    if isinstance(v, bool):  
        return v  
    if isinstance(v, str):  
        s = v.strip().lower()  
        return s in ("pass", "passed", "true", "yes", "ok")  
    if isinstance(v, (int, float)):  
        return v != 0  
    return bool(v)  
  
  
def _find_path(policy: PromotionPolicy, from_env: str, to_env: str) -> Optional[PromotionPath]:  
    for p in policy.paths:  
        if p.from_env == from_env and p.to_env == to_env:  
            return p  
    return None  
  
  
def evaluate_promotion(  
    policy: PromotionPolicy,  
    *,  
    from_env: str,  
    to_env: str,  
    evidence: Mapping[str, object],  
) -> PromotionDecision:  
    """  
    Pure evaluator: does not perform any checks itself; relies on provided evidence.  
  
    Returns deterministic failure lists (stable ordering by path gate order).  
    """  
    details: List[str] = []  
    missing_evidence: List[str] = []  
    failed_gates: List[str] = []  
  
    path = _find_path(policy, from_env, to_env)  
    if path is None:  
        return PromotionDecision(  
            allowed=False,  
            from_env=from_env,  
            to_env=to_env,  
            failed_gates=["NO-PATH"],  
            missing_evidence=[],  
            details=[f"No promotion path defined for {from_env} -> {to_env}"],  
        )  
  
    for g in path.gates:  
        # Missing evidence keys  
        missing_for_gate = [k for k in g.required_evidence_keys if k not in evidence]  
        if missing_for_gate:  
            missing_evidence.extend(missing_for_gate)  
            failed_gates.append(g.gate_id)  
            details.append(  
                f"{g.gate_id} failed: missing evidence keys: {', '.join(missing_for_gate)}"  
            )  
            continue  
  
        # Evaluate truthiness of required evidence keys; all must be truthy  
        values = [(k, evidence.get(k)) for k in g.required_evidence_keys]  
        failing = [(k, v) for (k, v) in values if not _truthy(v)]  
        if failing:  
            failed_gates.append(g.gate_id)  
            details.append(  
                f"{g.gate_id} failed: non-truthy evidence: "  
                + ", ".join([f"{k}={v!r}" for (k, v) in failing])  
            )  
        else:  
            details.append(f"{g.gate_id} passed")  
  
    allowed = len(failed_gates) == 0  
    # Deterministic de-dup for missing evidence while preserving order  
    seen: set[str] = set()  
    missing_unique: List[str] = []  
    for k in missing_evidence:  
        if k not in seen:  
            seen.add(k)  
            missing_unique.append(k)  
  
    return PromotionDecision(  
        allowed=allowed,  
        from_env=from_env,  
        to_env=to_env,  
        failed_gates=failed_gates,  
        missing_evidence=missing_unique,  
        details=details,  
    )  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_promotion_policy_markdown(policy: PromotionPolicy) -> str:  
    lines: List[str] = []  
    lines.append(f"# { _md(policy.title) }")  
    lines.append("")  
    lines.append(f"**Policy ID:** { _md(policy.policy_id) }")  
    lines.append("")  
    lines.append("## Environments")  
    lines.append("")  
    for e in policy.environments:  
        lines.append(f"- { _md(e) }")  
    lines.append("")  
    lines.append("## Promotion Paths and Gates")  
    lines.append("")  
    for p in policy.paths:  
        lines.append(f"### { _md(p.from_env) } → { _md(p.to_env) }")  
        lines.append("")  
        for g in p.gates:  
            lines.append(f"#### { _md(g.gate_id) }: { _md(g.name) }")  
            lines.append("")  
            lines.append(f"- **Description:** { _md(g.description) }")  
            lines.append(f"- **Required evidence keys:** {', '.join([_md(k) for k in g.required_evidence_keys])}")  
            lines.append(f"- **Pass criteria:** { _md(g.pass_criteria) }")  
            lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in policy.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def promotion_policy_to_json(policy: Optional[PromotionPolicy] = None) -> str:  
    p = policy or get_promotion_policy()  
    payload = {  
        "policy_id": p.policy_id,  
        "title": p.title,  
        "environments": list(p.environments),  
        "paths": [  
            {  
                "from_env": path.from_env,  
                "to_env": path.to_env,  
                "gates": [  
                    {  
                        "gate_id": g.gate_id,  
                        "name": g.name,  
                        "description": g.description,  
                        "required_evidence_keys": list(g.required_evidence_keys),  
                        "pass_criteria": g.pass_criteria,  
                    }  
                    for g in path.gates  
                ],  
            }  
            for path in p.paths  
        ],  
        "notes": list(p.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_promotion_policy_markdown(path: str) -> None:  
    p = get_promotion_policy()  
    md = render_promotion_policy_markdown(p)  
    write_text_file(path, md)  