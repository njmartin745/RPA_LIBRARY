"""  
REPORT-12E: Alerting Signals From Run Outcomes (Milestone 12.5.2)  
  
Single responsibility:  
- Define a canonical, deterministic alerting policy (signal thresholds).  
- Provide a pure evaluator that turns run outcome metrics into triggered alerts.  
- Provide deterministic Markdown/JSON renderers.  
  
Determinism:  
- No timestamps generated.  
- Stable ordering of signals and triggered alerts.  
- JSON rendering uses sort_keys=True.  
  
This module does NOT send alerts. It only evaluates signals and returns an alert plan.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple  
import json  
  
  
__all__ = [  
    "SignalThresholds",  
    "AlertPolicy",  
    "TriggeredAlert",  
    "AlertDecision",  
    "get_alert_policy",  
    "validate_alert_policy",  
    "evaluate_alert_policy",  
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
class SignalThresholds:  
    """  
    Thresholds are interpreted deterministically by this module.  
  
    Metric contract (caller provides):  
      - total_runs: int  
      - success_runs: int  
      - failed_runs: int  
      - consecutive_failures: int  
      - doctor_blocked_runs: int  
      - guard_blocked_runs: int  
      - p95_duration_seconds: int (optional; if missing, duration signals are skipped)  
    """  
    min_total_runs: int  
  
    # Ratios are represented as integer basis points (0..10000)  
    min_success_rate_bp: int  # e.g., 9900 = 99.00%  
    max_fail_rate_bp: int     # e.g., 100 = 1.00%  
  
    max_consecutive_failures: int  
  
    max_doctor_block_rate_bp: int  
    max_guard_block_rate_bp: int  
  
    # Optional perf gate (None disables)  
    max_p95_duration_seconds: Optional[int]  
  
  
@dataclass(frozen=True, slots=True)  
class AlertPolicy:  
    policy_id: str  
    title: str  
    env_thresholds: Dict[str, SignalThresholds]  # includes "default"  
    notes: List[str]  
  
  
@dataclass(frozen=True, slots=True)  
class TriggeredAlert:  
    signal_id: str  
    severity: str  # "warning" | "critical"  
    metric: str  
    value: int  
    threshold: int  
    message: str  
  
  
@dataclass(frozen=True, slots=True)  
class AlertDecision:  
    policy_id: str  
    env: str  
    passed: bool  
    alerts: List[TriggeredAlert]  
    computed: Dict[str, int]  # deterministic derived metrics (basis points etc.)  
    details: List[str]  
  
  
def get_alert_policy(  
    *,  
    policy_id: str = "ALERT-SIGNALS-12E",  
    title: str = "Alerting Signals From Run Outcomes",  
    notes: Optional[Sequence[str]] = None,  
) -> AlertPolicy:  
    n = list(notes) if notes is not None else [  
        "This policy is deterministic and contains no generated timestamps.",  
        "Ratios are computed as integer basis points (bp) to avoid float ambiguity.",  
        "Callers supply run metrics for a defined window (e.g., last N runs or last X minutes).",  
    ]  
  
    default = SignalThresholds(  
        min_total_runs=5,  
        min_success_rate_bp=9500,       # >= 95.00%  
        max_fail_rate_bp=500,           # <= 5.00%  
        max_consecutive_failures=3,  
        max_doctor_block_rate_bp=200,   # <= 2.00%  
        max_guard_block_rate_bp=200,    # <= 2.00%  
        max_p95_duration_seconds=None,  # disabled by default  
    )  
  
    prod = SignalThresholds(  
        min_total_runs=10,  
        min_success_rate_bp=9900,       # >= 99.00%  
        max_fail_rate_bp=100,           # <= 1.00%  
        max_consecutive_failures=2,  
        max_doctor_block_rate_bp=50,    # <= 0.50%  
        max_guard_block_rate_bp=50,     # <= 0.50%  
        max_p95_duration_seconds=180,   # 3 minutes p95  
    )  
  
    return AlertPolicy(  
        policy_id=policy_id,  
        title=title,  
        env_thresholds={"default": default, "prod": prod},  
        notes=n,  
    )  
  
  
def validate_alert_policy(policy: AlertPolicy) -> List[str]:  
    errors: List[str] = []  
    if not policy.policy_id:  
        errors.append("policy_id is required")  
    if "default" not in policy.env_thresholds:  
        errors.append("env_thresholds must include 'default'")  
    for env, t in policy.env_thresholds.items():  
        if not env:  
            errors.append("env key must be non-empty")  
        if t.min_total_runs < 0:  
            errors.append(f"{env}: min_total_runs must be >= 0")  
        for name, bp in [  
            ("min_success_rate_bp", t.min_success_rate_bp),  
            ("max_fail_rate_bp", t.max_fail_rate_bp),  
            ("max_doctor_block_rate_bp", t.max_doctor_block_rate_bp),  
            ("max_guard_block_rate_bp", t.max_guard_block_rate_bp),  
        ]:  
            if not (0 <= bp <= 10000):  
                errors.append(f"{env}: {name} must be in [0, 10000], got {bp}")  
        if t.max_consecutive_failures < 0:  
            errors.append(f"{env}: max_consecutive_failures must be >= 0")  
        if t.max_p95_duration_seconds is not None and t.max_p95_duration_seconds < 0:  
            errors.append(f"{env}: max_p95_duration_seconds must be >= 0 or None")  
    return errors  
  
  
def _thresholds_for_env(policy: AlertPolicy, env: str) -> SignalThresholds:  
    return policy.env_thresholds.get(env, policy.env_thresholds["default"])  
  
  
def _get_int(metrics: Mapping[str, Any], key: str) -> int:  
    v = metrics.get(key)  
    if isinstance(v, bool):  # avoid bool as int  
        raise TypeError(f"Metric {key!r} must be int, got bool")  
    if not isinstance(v, int):  
        raise TypeError(f"Metric {key!r} must be int, got {type(v).__name__}")  
    return v  
  
  
def _bp(numer: int, denom: int) -> int:  
    if denom <= 0:  
        return 0  
    # integer basis points, truncated deterministically  
    return (numer * 10000) // denom  
  
  
def _sorted_alerts(alerts: Sequence[TriggeredAlert]) -> List[TriggeredAlert]:  
    return sorted(list(alerts), key=lambda a: (a.severity, a.signal_id, a.metric, a.message))  
  
  
def evaluate_alert_policy(  
    policy: AlertPolicy,  
    *,  
    env: str,  
    metrics: Mapping[str, Any],  
) -> AlertDecision:  
    """  
    Pure evaluator. The caller defines the time window / sample window for metrics.  
    """  
    t = _thresholds_for_env(policy, env)  
  
    total_runs = _get_int(metrics, "total_runs")  
    success_runs = _get_int(metrics, "success_runs")  
    failed_runs = _get_int(metrics, "failed_runs")  
    consecutive_failures = _get_int(metrics, "consecutive_failures")  
    doctor_blocked_runs = _get_int(metrics, "doctor_blocked_runs")  
    guard_blocked_runs = _get_int(metrics, "guard_blocked_runs")  
  
    details: List[str] = []  
    alerts: List[TriggeredAlert] = []  
  
    if total_runs < 0 or success_runs < 0 or failed_runs < 0:  
        raise ValueError("Run counts must be >= 0")  
    if success_runs + failed_runs > total_runs:  
        raise ValueError("success_runs + failed_runs cannot exceed total_runs")  
  
    success_rate_bp = _bp(success_runs, total_runs)  
    fail_rate_bp = _bp(failed_runs, total_runs)  
    doctor_block_rate_bp = _bp(doctor_blocked_runs, total_runs)  
    guard_block_rate_bp = _bp(guard_blocked_runs, total_runs)  
  
    computed: Dict[str, int] = {  
        "success_rate_bp": success_rate_bp,  
        "fail_rate_bp": fail_rate_bp,  
        "doctor_block_rate_bp": doctor_block_rate_bp,  
        "guard_block_rate_bp": guard_block_rate_bp,  
    }  
  
    details.append(f"Computed success_rate_bp={success_rate_bp} from {success_runs}/{total_runs}")  
    details.append(f"Computed fail_rate_bp={fail_rate_bp} from {failed_runs}/{total_runs}")  
    details.append(f"Computed doctor_block_rate_bp={doctor_block_rate_bp} from {doctor_blocked_runs}/{total_runs}")  
    details.append(f"Computed guard_block_rate_bp={guard_block_rate_bp} from {guard_blocked_runs}/{total_runs}")  
    details.append(f"Computed consecutive_failures={consecutive_failures}")  
  
    # If insufficient samples, still report a warning (deterministic) but do not "fail"  
    if total_runs < t.min_total_runs:  
        alerts.append(  
            TriggeredAlert(  
                signal_id="signal.insufficient_samples",  
                severity="warning",  
                metric="total_runs",  
                value=total_runs,  
                threshold=t.min_total_runs,  
                message="Not enough runs in window to make strong assertions; increase window or wait",  
            )  
        )  
  
    # Reliability signals  
    if total_runs >= t.min_total_runs and success_rate_bp < t.min_success_rate_bp:  
        alerts.append(  
            TriggeredAlert(  
                signal_id="signal.success_rate_low",  
                severity="critical",  
                metric="success_rate_bp",  
                value=success_rate_bp,  
                threshold=t.min_success_rate_bp,  
                message="Success rate below threshold",  
            )  
        )  
  
    if total_runs >= t.min_total_runs and fail_rate_bp > t.max_fail_rate_bp:  
        alerts.append(  
            TriggeredAlert(  
                signal_id="signal.fail_rate_high",  
                severity="critical",  
                metric="fail_rate_bp",  
                value=fail_rate_bp,  
                threshold=t.max_fail_rate_bp,  
                message="Failure rate above threshold",  
            )  
        )  
  
    if consecutive_failures > t.max_consecutive_failures:  
        alerts.append(  
            TriggeredAlert(  
                signal_id="signal.consecutive_failures_high",  
                severity="critical",  
                metric="consecutive_failures",  
                value=consecutive_failures,  
                threshold=t.max_consecutive_failures,  
                message="Consecutive failures exceed threshold",  
            )  
        )  
  
    # Operational gate signals  
    if total_runs >= t.min_total_runs and doctor_block_rate_bp > t.max_doctor_block_rate_bp:  
        alerts.append(  
            TriggeredAlert(  
                signal_id="signal.doctor_block_rate_high",  
                severity="warning",  
                metric="doctor_block_rate_bp",  
                value=doctor_block_rate_bp,  
                threshold=t.max_doctor_block_rate_bp,  
                message="DOCTOR blocks are frequent; investigate environment readiness or config drift",  
            )  
        )  
  
    if total_runs >= t.min_total_runs and guard_block_rate_bp > t.max_guard_block_rate_bp:  
        alerts.append(  
            TriggeredAlert(  
                signal_id="signal.guard_block_rate_high",  
                severity="warning",  
                metric="guard_block_rate_bp",  
                value=guard_block_rate_bp,  
                threshold=t.max_guard_block_rate_bp,  
                message="GUARD blocks are frequent; investigate policy violations or unreviewed changes",  
            )  
        )  
  
    # Performance signal (optional)  
    p95 = metrics.get("p95_duration_seconds")  
    if t.max_p95_duration_seconds is not None:  
        if p95 is None:  
            details.append("p95_duration_seconds missing; skipping duration signal")  
        else:  
            if not isinstance(p95, int) or isinstance(p95, bool):  
                raise TypeError("Metric 'p95_duration_seconds' must be int if provided")  
            computed["p95_duration_seconds"] = p95  
            details.append(f"Computed p95_duration_seconds={p95}")  
            if p95 > t.max_p95_duration_seconds:  
                alerts.append(  
                    TriggeredAlert(  
                        signal_id="signal.p95_duration_high",  
                        severity="warning",  
                        metric="p95_duration_seconds",  
                        value=p95,  
                        threshold=t.max_p95_duration_seconds,  
                        message="p95 duration above threshold; investigate performance/regressions",  
                    )  
                )  
  
    alerts_sorted = _sorted_alerts(alerts)  
  
    # Pass/fail: critical alerts fail  
    passed = (len([a for a in alerts_sorted if a.severity == "critical"]) == 0)  
  
    return AlertDecision(  
        policy_id=policy.policy_id,  
        env=env,  
        passed=passed,  
        alerts=alerts_sorted,  
        computed=computed,  
        details=details,  
    )  
  
  
def policy_to_json(policy: AlertPolicy) -> str:  
    payload: Dict[str, Any] = {  
        "policy_id": policy.policy_id,  
        "title": policy.title,  
        "env_thresholds": {  
            env: {  
                "min_total_runs": t.min_total_runs,  
                "min_success_rate_bp": t.min_success_rate_bp,  
                "max_fail_rate_bp": t.max_fail_rate_bp,  
                "max_consecutive_failures": t.max_consecutive_failures,  
                "max_doctor_block_rate_bp": t.max_doctor_block_rate_bp,  
                "max_guard_block_rate_bp": t.max_guard_block_rate_bp,  
                "max_p95_duration_seconds": t.max_p95_duration_seconds,  
            }  
            for env, t in sorted(policy.env_thresholds.items(), key=lambda kv: kv[0])  
        },  
        "notes": list(policy.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_policy_markdown(policy: AlertPolicy) -> str:  
    lines: List[str] = []  
    lines.append(f"# { _md(policy.title) }")  
    lines.append("")  
    lines.append(f"**Policy ID:** { _md(policy.policy_id) }")  
    lines.append("")  
    lines.append("## Thresholds by Environment")  
    lines.append("")  
    for env, t in sorted(policy.env_thresholds.items(), key=lambda kv: kv[0]):  
        lines.append(f"### { _md(env) }")  
        lines.append("")  
        lines.append(f"- min_total_runs: `{t.min_total_runs}`")  
        lines.append(f"- min_success_rate_bp: `{t.min_success_rate_bp}`")  
        lines.append(f"- max_fail_rate_bp: `{t.max_fail_rate_bp}`")  
        lines.append(f"- max_consecutive_failures: `{t.max_consecutive_failures}`")  
        lines.append(f"- max_doctor_block_rate_bp: `{t.max_doctor_block_rate_bp}`")  
        lines.append(f"- max_guard_block_rate_bp: `{t.max_guard_block_rate_bp}`")  
        lines.append(f"- max_p95_duration_seconds: `{t.max_p95_duration_seconds}`")  
        lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in policy.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def decision_to_json(decision: AlertDecision) -> str:  
    payload: Dict[str, Any] = {  
        "policy_id": decision.policy_id,  
        "env": decision.env,  
        "passed": decision.passed,  
        "computed": dict(decision.computed),  
        "alerts": [  
            {  
                "signal_id": a.signal_id,  
                "severity": a.severity,  
                "metric": a.metric,  
                "value": a.value,  
                "threshold": a.threshold,  
                "message": a.message,  
            }  
            for a in decision.alerts  
        ],  
        "details": list(decision.details),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def render_decision_markdown(decision: AlertDecision) -> str:  
    lines: List[str] = []  
    lines.append("# Alerting Signals Decision")  
    lines.append("")  
    lines.append(f"**Policy ID:** { _md(decision.policy_id) }")  
    lines.append(f"**Environment:** { _md(decision.env) }")  
    lines.append("")  
    lines.append(f"**Passed:** `{decision.passed}`")  
    lines.append("")  
    lines.append("## Computed")  
    lines.append("")  
    for k, v in sorted(decision.computed.items(), key=lambda kv: kv[0]):  
        lines.append(f"- { _md(k) }: `{v}`")  
    lines.append("")  
    lines.append("## Alerts")  
    lines.append("")  
    if not decision.alerts:  
        lines.append("(none)")  
        lines.append("")  
    else:  
        for a in decision.alerts:  
            lines.append(  
                f"- **{_md(a.severity)}** `{_md(a.signal_id)}` — { _md(a.metric) }={a.value} "  
                f"(threshold {a.threshold}) — { _md(a.message) }"  
            )  
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
  
  
def write_policy_json(path: str, policy: AlertPolicy) -> None:  
    write_text_file(path, policy_to_json(policy))  
  
  
def write_policy_markdown(path: str, policy: AlertPolicy) -> None:  
    write_text_file(path, render_policy_markdown(policy))  
  
  
def write_decision_json(path: str, decision: AlertDecision) -> None:  
    write_text_file(path, decision_to_json(decision))  
  
  
def write_decision_markdown(path: str, decision: AlertDecision) -> None:  
    write_text_file(path, render_decision_markdown(decision))  