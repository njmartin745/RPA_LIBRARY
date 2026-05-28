"""  
GUARD-12A: Production-default GUARD Policy (Milestone 12.4.2)  
  
Single responsibility:  
- Define deterministic GUARD policy defaults, especially for production.  
- Provide a pure evaluator that checks a workflow (dict) + selectors (dict) against the policy.  
- Provide deterministic Markdown/JSON renderers for operator-facing docs.  
  
Notes:  
- This module does not execute Selenium, and does not mutate workflows.  
- It is intended to be called by RUN/PIPE layers before execution in production.  
- Deterministic: no timestamps; stable ordering of violations.  
  
Policy intent (prod defaults):  
- Disallow exec_js / exec_js_file by default.  
- Require https URLs for open.  
- Optionally restrict open hostnames.  
- Require selector_ref (not raw selector strings) for selector-based steps.  
- Require selector_ref keys to exist in selectors bundle.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple  
import json  
from urllib.parse import urlparse  
  
  
__all__ = [  
    "GuardProfile",  
    "GuardPolicy",  
    "GuardViolation",  
    "GuardDecision",  
    "get_guard_policy",  
    "evaluate_guard_policy",  
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
  
  
_ALLOWED_STEP_TYPES = (  
    "open",  
    "click_selector",  
    "type_selector_secret",  
    "wait_for_selector",  
    "exec_js",  
    "exec_js_file",  
    "repeat",  
    "log",  
    "switch_back_to_main_tab",  
)  
  
_SELECTOR_STEP_TYPES = (  
    "click_selector",  
    "wait_for_selector",  
    "type_selector_secret",  
)  
  
  
@dataclass(frozen=True, slots=True)  
class GuardProfile:  
    """  
    Environment-specific policy knobs.  
    """  
    allow_exec_js: bool  
    allow_exec_js_file: bool  
    require_https_open: bool  
    allowed_open_hosts: List[str]  # empty => no host restriction  
    require_selector_ref: bool  
  
  
@dataclass(frozen=True, slots=True)  
class GuardPolicy:  
    policy_id: str  
    title: str  
    env_profiles: Dict[str, GuardProfile]  # includes "default", "prod"  
    notes: List[str]  
  
  
@dataclass(frozen=True, slots=True)  
class GuardViolation:  
    rule_id: str  
    severity: str  # "error" | "warn"  
    step_path: str  
    message: str  
  
  
@dataclass(frozen=True, slots=True)  
class GuardDecision:  
    policy_id: str  
    env: str  
    passed: bool  
    violations: List[GuardViolation]  
    details: List[str]  
  
  
def get_guard_policy(  
    *,  
    policy_id: str = "GUARD-PROD-DEFAULTS-12A",  
    title: str = "GUARD Policies (Production Defaults)",  
    notes: Optional[Sequence[str]] = None,  
) -> GuardPolicy:  
    n = list(notes) if notes is not None else [  
        "This policy is deterministic and contains no generated timestamps.",  
        "Production defaults prioritize safety: JS execution is disallowed unless explicitly enabled.",  
        "Selector-based steps should use selector_ref and must resolve in the selectors bundle.",  
    ]  
  
    default_profile = GuardProfile(  
        allow_exec_js=True,  
        allow_exec_js_file=True,  
        require_https_open=False,  
        allowed_open_hosts=[],  
        require_selector_ref=False,  
    )  
  
    prod_profile = GuardProfile(  
        allow_exec_js=False,  
        allow_exec_js_file=False,  
        require_https_open=True,  
        allowed_open_hosts=[],  # keep empty by default; operators may lock to known hosts  
        require_selector_ref=True,  
    )  
  
    return GuardPolicy(  
        policy_id=policy_id,  
        title=title,  
        env_profiles={  
            "default": default_profile,  
            "prod": prod_profile,  
        },  
        notes=n,  
    )  
  
  
def _extract_selectors_map(selectors_bundle: Mapping[str, Any]) -> Mapping[str, Any]:  
    """  
    Accept either:  
      {"selectors": {...}} or {...}  
    """  
    if "selectors" in selectors_bundle and isinstance(selectors_bundle.get("selectors"), Mapping):  
        return selectors_bundle["selectors"]  # type: ignore[return-value]  
    return selectors_bundle  
  
  
def _profile_for_env(policy: GuardPolicy, env: str) -> GuardProfile:  
    return policy.env_profiles.get(env, policy.env_profiles["default"])  
  
  
def _step_type(step: Mapping[str, Any]) -> str:  
    t = step.get("type")  
    return t if isinstance(t, str) else ""  
  
  
def _has_key(step: Mapping[str, Any], k: str) -> bool:  
    return k in step and step.get(k) is not None  
  
  
def _get_str(step: Mapping[str, Any], k: str) -> Optional[str]:  
    v = step.get(k)  
    return v if isinstance(v, str) else None  
  
  
def _is_https_url(url: str) -> bool:  
    try:  
        p = urlparse(url)  
        return (p.scheme.lower() == "https") and bool(p.netloc)  
    except Exception:  
        return False  
  
  
def _url_host(url: str) -> str:  
    try:  
        return (urlparse(url).hostname or "").lower()  
    except Exception:  
        return ""  
  
  
def _sorted_violations(vs: Sequence[GuardViolation]) -> List[GuardViolation]:  
    return sorted(list(vs), key=lambda v: (v.severity, v.rule_id, v.step_path, v.message))  
  
  
def _eval_step(  
    *,  
    step: Mapping[str, Any],  
    step_path: str,  
    profile: GuardProfile,  
    selectors_map: Mapping[str, Any],  
) -> Tuple[List[GuardViolation], List[str]]:  
    """  
    Evaluate one step (not including children of repeat; caller handles recursion).  
    Returns: (violations, details_lines)  
    """  
    violations: List[GuardViolation] = []  
    details: List[str] = []  
    t = _step_type(step)  
  
    # Rule: known step types only (schema should also catch, but keep guard explicit)  
    if t not in _ALLOWED_STEP_TYPES:  
        violations.append(  
            GuardViolation(  
                rule_id="guard.allowed_step_types",  
                severity="error",  
                step_path=step_path,  
                message=f"Unknown/unsupported step type: {t!r}",  
            )  
        )  
        return violations, details  
  
    # Rule: exec_js / exec_js_file disallowed by default in prod  
    if t == "exec_js" and not profile.allow_exec_js:  
        violations.append(  
            GuardViolation(  
                rule_id="guard.disallow_exec_js",  
                severity="error",  
                step_path=step_path,  
                message="exec_js is disallowed by policy in this environment",  
            )  
        )  
    if t == "exec_js_file" and not profile.allow_exec_js_file:  
        violations.append(  
            GuardViolation(  
                rule_id="guard.disallow_exec_js_file",  
                severity="error",  
                step_path=step_path,  
                message="exec_js_file is disallowed by policy in this environment",  
            )  
        )  
  
    # Rule: open URL restrictions  
    if t == "open":  
        url = _get_str(step, "url")  
        if not url:  
            violations.append(  
                GuardViolation(  
                    rule_id="guard.open_requires_url",  
                    severity="error",  
                    step_path=step_path,  
                    message="open step missing required string field: 'url'",  
                )  
            )  
        else:  
            if profile.require_https_open and not _is_https_url(url):  
                violations.append(  
                    GuardViolation(  
                        rule_id="guard.open_requires_https",  
                        severity="error",  
                        step_path=step_path,  
                        message=f"open url must be https with host; got: {url!r}",  
                    )  
                )  
            if profile.allowed_open_hosts:  
                host = _url_host(url)  
                allowed = {h.lower() for h in profile.allowed_open_hosts}  
                if host not in allowed:  
                    violations.append(  
                        GuardViolation(  
                            rule_id="guard.open_host_allowlist",  
                            severity="error",  
                            step_path=step_path,  
                            message=f"open url host {host!r} not in allowlist {sorted(allowed)!r}",  
                        )  
                    )  
  
    # Rule: selector-based steps must use selector_ref (prod default)  
    if t in _SELECTOR_STEP_TYPES:  
        has_selector_ref = _has_key(step, "selector_ref") and isinstance(step.get("selector_ref"), str)  
        has_raw_selector = _has_key(step, "selector") and isinstance(step.get("selector"), str)  
  
        if profile.require_selector_ref:  
            if not has_selector_ref:  
                violations.append(  
                    GuardViolation(  
                        rule_id="guard.require_selector_ref",  
                        severity="error",  
                        step_path=step_path,  
                        message=f"{t} must use 'selector_ref' (raw 'selector' is not allowed in this env)",  
                    )  
                )  
            if has_raw_selector:  
                violations.append(  
                    GuardViolation(  
                        rule_id="guard.disallow_raw_selector",  
                        severity="error",  
                        step_path=step_path,  
                        message=f"{t} contains raw 'selector' which is disallowed in this env",  
                    )  
                )  
  
        # If selector_ref exists, it must resolve.  
        if has_selector_ref:  
            ref = str(step.get("selector_ref"))  
            if ref not in selectors_map:  
                violations.append(  
                    GuardViolation(  
                        rule_id="guard.selector_ref_must_resolve",  
                        severity="error",  
                        step_path=step_path,  
                        message=f"selector_ref {ref!r} not found in selectors bundle",  
                    )  
                )  
  
    # Nice-to-have detail line (deterministic)  
    details.append(f"Checked step {step_path}: {t}")  
  
    return violations, details  
  
  
def _walk_steps(  
    *,  
    steps: Sequence[Any],  
    prefix: str,  
    profile: GuardProfile,  
    selectors_map: Mapping[str, Any],  
) -> Tuple[List[GuardViolation], List[str]]:  
    violations: List[GuardViolation] = []  
    details: List[str] = []  
  
    for i, raw in enumerate(list(steps)):  
        step_path = f"{prefix}{i}"  
        if not isinstance(raw, Mapping):  
            violations.append(  
                GuardViolation(  
                    rule_id="guard.step_must_be_object",  
                    severity="error",  
                    step_path=step_path,  
                    message=f"Step must be an object/dict; got: {type(raw).__name__}",  
                )  
            )  
            continue  
  
        v, d = _eval_step(step=raw, step_path=step_path, profile=profile, selectors_map=selectors_map)  
        violations.extend(v)  
        details.extend(d)  
  
        # Recurse into repeat.steps  
        if _step_type(raw) == "repeat":  
            inner = raw.get("steps")  
            if not isinstance(inner, list):  
                violations.append(  
                    GuardViolation(  
                        rule_id="guard.repeat_requires_steps_list",  
                        severity="error",  
                        step_path=step_path,  
                        message="repeat step requires 'steps' as a list",  
                    )  
                )  
            else:  
                iv, idt = _walk_steps(  
                    steps=inner,  
                    prefix=f"{step_path}.steps.",  
                    profile=profile,  
                    selectors_map=selectors_map,  
                )  
                violations.extend(iv)  
                details.extend(idt)  
  
    return violations, details  
  
  
def evaluate_guard_policy(  
    policy: GuardPolicy,  
    *,  
    env: str,  
    workflow: Mapping[str, Any],  
    selectors: Mapping[str, Any],  
) -> GuardDecision:  
    """  
    Pure evaluation over workflow/selectors dicts.  
    """  
    profile = _profile_for_env(policy, env)  
    selectors_map = _extract_selectors_map(selectors)  
  
    steps = workflow.get("steps")  
    violations: List[GuardViolation] = []  
    details: List[str] = []  
  
    if not isinstance(steps, list):  
        violations.append(  
            GuardViolation(  
                rule_id="guard.workflow_requires_steps",  
                severity="error",  
                step_path="workflow",  
                message="Workflow must contain 'steps' as a list",  
            )  
        )  
    else:  
        v, d = _walk_steps(steps=steps, prefix="steps.", profile=profile, selectors_map=selectors_map)  
        violations.extend(v)  
        details.extend(d)  
  
    violations_sorted = _sorted_violations(violations)  
    passed = (len([v for v in violations_sorted if v.severity == "error"]) == 0)  
  
    return GuardDecision(  
        policy_id=policy.policy_id,  
        env=env,  
        passed=passed,  
        violations=violations_sorted,  
        details=details,  
    )  
  
  
def policy_to_json(policy: GuardPolicy) -> str:  
    payload: Dict[str, Any] = {  
        "policy_id": policy.policy_id,  
        "title": policy.title,  
        "env_profiles": {  
            env: {  
                "allow_exec_js": prof.allow_exec_js,  
                "allow_exec_js_file": prof.allow_exec_js_file,  
                "require_https_open": prof.require_https_open,  
                "allowed_open_hosts": list(prof.allowed_open_hosts),  
                "require_selector_ref": prof.require_selector_ref,  
            }  
            for env, prof in sorted(policy.env_profiles.items(), key=lambda kv: kv[0])  
        },  
        "notes": list(policy.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_policy_markdown(policy: GuardPolicy) -> str:  
    lines: List[str] = []  
    lines.append(f"# { _md(policy.title) }")  
    lines.append("")  
    lines.append(f"**Policy ID:** { _md(policy.policy_id) }")  
    lines.append("")  
    lines.append("## Environment Profiles")  
    lines.append("")  
    for env, prof in sorted(policy.env_profiles.items(), key=lambda kv: kv[0]):  
        lines.append(f"### { _md(env) }")  
        lines.append("")  
        lines.append(f"- allow_exec_js: `{prof.allow_exec_js}`")  
        lines.append(f"- allow_exec_js_file: `{prof.allow_exec_js_file}`")  
        lines.append(f"- require_https_open: `{prof.require_https_open}`")  
        lines.append(f"- allowed_open_hosts: `{prof.allowed_open_hosts}`")  
        lines.append(f"- require_selector_ref: `{prof.require_selector_ref}`")  
        lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in policy.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def decision_to_json(decision: GuardDecision) -> str:  
    payload: Dict[str, Any] = {  
        "policy_id": decision.policy_id,  
        "env": decision.env,  
        "passed": decision.passed,  
        "violations": [  
            {  
                "rule_id": v.rule_id,  
                "severity": v.severity,  
                "step_path": v.step_path,  
                "message": v.message,  
            }  
            for v in decision.violations  
        ],  
        "details": list(decision.details),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def render_decision_markdown(decision: GuardDecision) -> str:  
    lines: List[str] = []  
    lines.append("# GUARD Decision")  
    lines.append("")  
    lines.append(f"**Policy ID:** { _md(decision.policy_id) }")  
    lines.append(f"**Environment:** { _md(decision.env) }")  
    lines.append("")  
    lines.append(f"**Passed:** `{decision.passed}`")  
    lines.append("")  
  
    lines.append("## Violations")  
    lines.append("")  
    if not decision.violations:  
        lines.append("(none)")  
        lines.append("")  
    else:  
        for v in decision.violations:  
            lines.append(f"- **{_md(v.severity)}** `{_md(v.rule_id)}` @ `{_md(v.step_path)}` — {_md(v.message)}")  
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
  
  
def write_policy_json(path: str, policy: GuardPolicy) -> None:  
    write_text_file(path, policy_to_json(policy))  
  
  
def write_policy_markdown(path: str, policy: GuardPolicy) -> None:  
    write_text_file(path, render_policy_markdown(policy))  
  
  
def write_decision_json(path: str, decision: GuardDecision) -> None:  
    write_text_file(path, decision_to_json(decision))  
  
  
def write_decision_markdown(path: str, decision: GuardDecision) -> None:  
    write_text_file(path, render_decision_markdown(decision))  