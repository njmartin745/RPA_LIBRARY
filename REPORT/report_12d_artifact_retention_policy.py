"""  
REPORT-12D: Artifact Retention Policy (Milestone 12.5.1)  
  
Single responsibility:  
- Define a canonical, deterministic artifact retention policy for production readiness.  
- Provide a pure evaluator that, given:  
    - env (e.g., "prod")  
    - artifacts metadata (kind, created_date, tags)  
    - now_date (caller supplied)  
  produces a deterministic keep/delete plan.  
- Provide deterministic Markdown/JSON renderers.  
  
Determinism:  
- No timestamps are generated.  
- Dates are handled as ISO strings (YYYY-MM-DD) and parsed deterministically.  
- Output ordering is stable.  
  
This module does NOT delete files. It only produces a plan.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from datetime import date, timedelta  
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple  
import json  
  
  
__all__ = [  
    "RetentionRule",  
    "RetentionPolicy",  
    "ArtifactMeta",  
    "RetentionAction",  
    "RetentionDecision",  
    "get_retention_policy",  
    "validate_retention_policy",  
    "parse_date_iso",  
    "evaluate_retention_policy",  
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
  
  
@dataclass(frozen=True, slots=True)  
class RetentionRule:  
    """  
    Retention rule for a specific artifact kind.  
  
    - keep_days: number of days after created_date to keep (inclusive).  
    - keep_last_n: always keep the newest N artifacts for this kind, regardless of age.  
    - legal_hold_tag: if an artifact's tags contain this value, it is always kept.  
    """  
    kind: str  
    keep_days: int  
    keep_last_n: int = 0  
    legal_hold_tag: str = "legal_hold"  
  
  
@dataclass(frozen=True, slots=True)  
class RetentionPolicy:  
    policy_id: str  
    title: str  
    env_rules: Dict[str, List[RetentionRule]]  # includes "default"  
    notes: List[str]  
  
  
@dataclass(frozen=True, slots=True)  
class ArtifactMeta:  
    """  
    Metadata supplied by callers (inventory/scan layer).  
  
    created_date must be ISO (YYYY-MM-DD).  
    """  
    artifact_id: str  
    kind: str  
    created_date: str  
    path_label: Optional[str] = None  
    size_bytes: Optional[int] = None  
    tags: Tuple[str, ...] = ()  
  
  
@dataclass(frozen=True, slots=True)  
class RetentionAction:  
    """  
    Action plan for one artifact.  
    """  
    artifact_id: str  
    kind: str  
    created_date: str  
    keep: bool  
    delete_on_or_after: Optional[str]  
    reason: str  
  
  
@dataclass(frozen=True, slots=True)  
class RetentionDecision:  
    policy_id: str  
    env: str  
    now_date: str  
    actions: List[RetentionAction]  
    summary: Dict[str, int]  # keep/delete counts by kind + totals  
  
  
def parse_date_iso(s: str) -> date:  
    """  
    Parse YYYY-MM-DD deterministically; raises ValueError on invalid input.  
    """  
    parts = s.split("-")  
    if len(parts) != 3:  
        raise ValueError(f"Invalid ISO date: {s!r}")  
    y, m, d = parts  
    return date(int(y), int(m), int(d))  
  
  
def _date_to_iso(d: date) -> str:  
    return d.isoformat()  
  
  
def _sorted_rules(rules: Sequence[RetentionRule]) -> List[RetentionRule]:  
    return sorted(list(rules), key=lambda r: r.kind)  
  
  
def _rules_for_env(policy: RetentionPolicy, env: str) -> List[RetentionRule]:  
    rules = policy.env_rules.get(env)  
    if rules is None:  
        rules = policy.env_rules.get("default", [])  
    return _sorted_rules(rules)  
  
  
def get_retention_policy(  
    *,  
    policy_id: str = "RETENTION-12D",  
    title: str = "Artifact Retention Policy",  
    notes: Optional[Sequence[str]] = None,  
) -> RetentionPolicy:  
    """  
    Canonical baseline retention policy. Adjust per your compliance needs.  
  
    Artifact kinds are intentionally generic and can map to your actual artifact layout:  
    - run_log  
    - screenshot  
    - run_report  
    - replay_bundle  
    - promotion_record  
    - release_manifest  
    - bundle_fingerprint  
    """  
    n = list(notes) if notes is not None else [  
        "This policy is deterministic and contains no generated timestamps.",  
        "Evaluation is based on caller-supplied artifact metadata and now_date.",  
        "legal_hold-tagged artifacts are always retained regardless of age.",  
        "keep_last_n provides an operational safety net for debugging/regressions.",  
    ]  
  
    default_rules = _sorted_rules([  
        RetentionRule(kind="run_log", keep_days=14, keep_last_n=5),  
        RetentionRule(kind="screenshot", keep_days=14, keep_last_n=20),  
        RetentionRule(kind="run_report", keep_days=30, keep_last_n=10),  
        RetentionRule(kind="replay_bundle", keep_days=30, keep_last_n=10),  
        RetentionRule(kind="promotion_record", keep_days=365, keep_last_n=50),  
        RetentionRule(kind="release_manifest", keep_days=365, keep_last_n=50),  
        RetentionRule(kind="bundle_fingerprint", keep_days=365, keep_last_n=50),  
    ])  
  
    # Production typically retains longer for audit and incident investigation.  
    prod_rules = _sorted_rules([  
        RetentionRule(kind="run_log", keep_days=30, keep_last_n=10),  
        RetentionRule(kind="screenshot", keep_days=30, keep_last_n=50),  
        RetentionRule(kind="run_report", keep_days=180, keep_last_n=50),  
        RetentionRule(kind="replay_bundle", keep_days=180, keep_last_n=50),  
        RetentionRule(kind="promotion_record", keep_days=730, keep_last_n=200),  
        RetentionRule(kind="release_manifest", keep_days=730, keep_last_n=200),  
        RetentionRule(kind="bundle_fingerprint", keep_days=730, keep_last_n=200),  
    ])  
  
    return RetentionPolicy(  
        policy_id=policy_id,  
        title=title,  
        env_rules={  
            "default": default_rules,  
            "prod": prod_rules,  
        },  
        notes=n,  
    )  
  
  
def validate_retention_policy(policy: RetentionPolicy) -> List[str]:  
    errors: List[str] = []  
    if not policy.policy_id:  
        errors.append("policy_id is required")  
    if "default" not in policy.env_rules:  
        errors.append("env_rules must include a 'default' profile")  
    for env, rules in policy.env_rules.items():  
        if not env:  
            errors.append("env name must be non-empty")  
        seen = set()  
        for r in rules:  
            if not r.kind:  
                errors.append(f"{env}: rule kind must be non-empty")  
                continue  
            if r.kind in seen:  
                errors.append(f"{env}: duplicate rule kind: {r.kind}")  
            seen.add(r.kind)  
            if r.keep_days < 0:  
                errors.append(f"{env}:{r.kind}: keep_days must be >= 0")  
            if r.keep_last_n < 0:  
                errors.append(f"{env}:{r.kind}: keep_last_n must be >= 0")  
    return errors  
  
  
def _index_rules_by_kind(rules: Sequence[RetentionRule]) -> Dict[str, RetentionRule]:  
    return {r.kind: r for r in rules}  
  
  
def _group_artifacts_by_kind(artifacts: Sequence[ArtifactMeta]) -> Dict[str, List[ArtifactMeta]]:  
    groups: Dict[str, List[ArtifactMeta]] = {}  
    for a in artifacts:  
        groups.setdefault(a.kind, []).append(a)  
    # stable ordering within group: newest first, then artifact_id for determinism  
    for k, lst in list(groups.items()):  
        groups[k] = sorted(  
            list(lst),  
            key=lambda x: (parse_date_iso(x.created_date), x.artifact_id),  
            reverse=True,  
        )  
    return groups  
  
  
def evaluate_retention_policy(  
    policy: RetentionPolicy,  
    *,  
    env: str,  
    artifacts: Sequence[ArtifactMeta],  
    now_date: str,  
) -> RetentionDecision:  
    """  
    Pure evaluator producing deterministic keep/delete plan.  
    """  
    now = parse_date_iso(now_date)  
    rules = _rules_for_env(policy, env)  
    rules_by_kind = _index_rules_by_kind(rules)  
  
    groups = _group_artifacts_by_kind(list(artifacts))  
  
    actions: List[RetentionAction] = []  
    keep_count_by_kind: Dict[str, int] = {}  
    delete_count_by_kind: Dict[str, int] = {}  
  
    for kind in sorted(groups.keys()):  
        group = groups[kind]  
        rule = rules_by_kind.get(kind)  
  
        # Determine last_n keep set for this kind  
        keep_last_ids = set()  
        if rule is not None and rule.keep_last_n > 0:  
            for a in group[: rule.keep_last_n]:  
                keep_last_ids.add(a.artifact_id)  
  
        for a in group:  
            # default behavior for unknown kinds: keep (warnable policy elsewhere)  
            if rule is None:  
                keep = True  
                delete_on = None  
                reason = f"Unknown kind {kind!r}: default keep"  
            else:  
                if rule.legal_hold_tag in set(a.tags):  
                    keep = True  
                    delete_on = None  
                    reason = f"Tag '{rule.legal_hold_tag}' present: always keep"  
                elif a.artifact_id in keep_last_ids:  
                    keep = True  
                    delete_on = None  
                    reason = f"Within keep_last_n={rule.keep_last_n} newest for kind"  
                else:  
                    created = parse_date_iso(a.created_date)  
                    keep_until = created + timedelta(days=rule.keep_days)  
                    # inclusive: if now <= keep_until => keep  
                    if now <= keep_until:  
                        keep = True  
                        delete_on = None  
                        reason = f"Age within keep_days={rule.keep_days} (keep_until={_date_to_iso(keep_until)})"  
                    else:  
                        keep = False  
                        # deterministic planned deletion date: keep_until + 1 day  
                        delete_on_date = keep_until + timedelta(days=1)  
                        delete_on = _date_to_iso(delete_on_date)  
                        reason = f"Expired keep_days={rule.keep_days} (keep_until={_date_to_iso(keep_until)})"  
  
            actions.append(  
                RetentionAction(  
                    artifact_id=a.artifact_id,  
                    kind=a.kind,  
                    created_date=a.created_date,  
                    keep=keep,  
                    delete_on_or_after=delete_on,  
                    reason=reason,  
                )  
            )  
  
            if keep:  
                keep_count_by_kind[kind] = keep_count_by_kind.get(kind, 0) + 1  
            else:  
                delete_count_by_kind[kind] = delete_count_by_kind.get(kind, 0) + 1  
  
    # stable ordering of actions overall  
    actions_sorted = sorted(actions, key=lambda x: (x.kind, x.created_date, x.artifact_id))  
  
    summary: Dict[str, int] = {}  
    for kind in sorted(set(list(keep_count_by_kind.keys()) + list(delete_count_by_kind.keys()))):  
        summary[f"{kind}.keep"] = keep_count_by_kind.get(kind, 0)  
        summary[f"{kind}.delete"] = delete_count_by_kind.get(kind, 0)  
    summary["total.keep"] = sum(keep_count_by_kind.values())  
    summary["total.delete"] = sum(delete_count_by_kind.values())  
    summary["total.artifacts"] = summary["total.keep"] + summary["total.delete"]  
  
    return RetentionDecision(  
        policy_id=policy.policy_id,  
        env=env,  
        now_date=now_date,  
        actions=actions_sorted,  
        summary=summary,  
    )  
  
  
def policy_to_json(policy: RetentionPolicy) -> str:  
    payload: Dict[str, Any] = {  
        "policy_id": policy.policy_id,  
        "title": policy.title,  
        "env_rules": {  
            env: [  
                {  
                    "kind": r.kind,  
                    "keep_days": r.keep_days,  
                    "keep_last_n": r.keep_last_n,  
                    "legal_hold_tag": r.legal_hold_tag,  
                }  
                for r in _sorted_rules(rules)  
            ]  
            for env, rules in sorted(policy.env_rules.items(), key=lambda kv: kv[0])  
        },  
        "notes": list(policy.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_policy_markdown(policy: RetentionPolicy) -> str:  
    lines: List[str] = []  
    lines.append(f"# { _md(policy.title) }")  
    lines.append("")  
    lines.append(f"**Policy ID:** { _md(policy.policy_id) }")  
    lines.append("")  
    lines.append("## Rules by Environment")  
    lines.append("")  
    for env, rules in sorted(policy.env_rules.items(), key=lambda kv: kv[0]):  
        lines.append(f"### { _md(env) }")  
        lines.append("")  
        for r in _sorted_rules(rules):  
            lines.append(f"- **{_md(r.kind)}**: keep_days={r.keep_days}, keep_last_n={r.keep_last_n}, legal_hold_tag={_md(r.legal_hold_tag)!r}")  
        lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in policy.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def decision_to_json(decision: RetentionDecision) -> str:  
    payload: Dict[str, Any] = {  
        "policy_id": decision.policy_id,  
        "env": decision.env,  
        "now_date": decision.now_date,  
        "summary": dict(decision.summary),  
        "actions": [  
            {  
                "artifact_id": a.artifact_id,  
                "kind": a.kind,  
                "created_date": a.created_date,  
                "keep": a.keep,  
                "delete_on_or_after": a.delete_on_or_after,  
                "reason": a.reason,  
            }  
            for a in decision.actions  
        ],  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def render_decision_markdown(decision: RetentionDecision) -> str:  
    lines: List[str] = []  
    lines.append("# Artifact Retention Decision")  
    lines.append("")  
    lines.append(f"**Policy ID:** { _md(decision.policy_id) }")  
    lines.append(f"**Environment:** { _md(decision.env) }")  
    lines.append(f"**Now date:** `{ _md(decision.now_date) }`")  
    lines.append("")  
    lines.append("## Summary")  
    lines.append("")  
    for k, v in sorted(decision.summary.items(), key=lambda kv: kv[0]):  
        lines.append(f"- { _md(k) }: `{v}`")  
    lines.append("")  
    lines.append("## Actions")  
    lines.append("")  
    if not decision.actions:  
        lines.append("(none)")  
        lines.append("")  
        return "\n".join(lines).rstrip() + "\n"  
  
    for a in decision.actions:  
        if a.keep:  
            lines.append(f"- KEEP `{_md(a.kind)}` `{_md(a.artifact_id)}` (created {a.created_date}) — { _md(a.reason) }")  
        else:  
            lines.append(  
                f"- DELETE `{_md(a.kind)}` `{_md(a.artifact_id)}` (created {a.created_date}) "  
                f"on/after {a.delete_on_or_after} — { _md(a.reason) }"  
            )  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_policy_json(path: str, policy: RetentionPolicy) -> None:  
    write_text_file(path, policy_to_json(policy))  
  
  
def write_policy_markdown(path: str, policy: RetentionPolicy) -> None:  
    write_text_file(path, render_policy_markdown(policy))  
  
  
def write_decision_json(path: str, decision: RetentionDecision) -> None:  
    write_text_file(path, decision_to_json(decision))  
  
  
def write_decision_markdown(path: str, decision: RetentionDecision) -> None:  
    write_text_file(path, render_decision_markdown(decision))  