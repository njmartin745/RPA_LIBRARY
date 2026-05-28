"""  
LEARN-1B — Selector Intelligence & Stability Scoring (pure analysis)  
  
Analyzes HISTORY rows to:  
- compute per-selector usage/failure counts  
- derive stability scores  
- identify low-stability / high-risk selectors  
- generate general, actionable recommendations (no DOM access, no workflow edits)  
  
No Selenium execution. Deterministic.  
"""  
  
from __future__ import annotations  
  
from typing import Any, Dict, List, Optional, Sequence, Tuple  
  
  
__all__ = [  
    "analyze_selector_stability",  
    "score_selector",  
    "generate_selector_recommendations",  
]  
  
  
def _dig(row: Dict[str, Any], paths: Sequence[Sequence[str]]) -> Optional[Any]:  
    for path in paths:  
        cur: Any = row  
        ok = True  
        for k in path:  
            if not isinstance(cur, dict) or k not in cur:  
                ok = False  
                break  
            cur = cur[k]  
        if ok:  
            return cur  
    return None  
  
  
def _as_str(x: Any) -> str:  
    return "" if x is None else str(x)  
  
  
def _workflow_name(row: Dict[str, Any]) -> str:  
    return _as_str(_dig(row, [["workflow_name"], ["workflow"], ["workflow", "name"]])) or "UNKNOWN_WORKFLOW"  
  
  
def _is_failure(row: Dict[str, Any]) -> bool:  
    status = _dig(row, [["status"], ["outcome"], ["result"], ["state"]])  
    if isinstance(status, str):  
        s = status.lower()  
        if s in {"fail", "failed", "error", "exception"}:  
            return True  
        if s in {"ok", "success", "passed"}:  
            return False  
  
    ok = _dig(row, [["ok"], ["success"]])  
    if isinstance(ok, bool):  
        return not ok  
  
    # if category/message exists assume failure  
    err = _dig(row, [["error"], ["error_message"], ["exception"], ["err"]])  
    cat = _dig(row, [["error_category"], ["failure_category"], ["category"]])  
    return bool(err or cat)  
  
  
def _selector_key(row: Dict[str, Any]) -> Optional[str]:  
    ref = _dig(row, [["selector_ref"], ["step", "selector_ref"], ["error", "selector_ref"]])  
    if ref:  
        return f"selector_ref:{_as_str(ref)}"  
  
    strat = _dig(row, [["strategy"], ["step", "strategy"], ["error", "strategy"]])  
    sel = _dig(row, [["selector"], ["step", "selector"], ["error", "selector"]])  
    if strat and sel:  
        return f"{_as_str(strat)}:{_as_str(sel)}"  
    return None  
  
  
def score_selector(selector_key: str, usage_count: int, failure_count: int) -> float:  
    """  
    stability = 1 - (failure_count / usage_count)  
    Deterministic and clamped to [0,1].  
    """  
    if usage_count <= 0:  
        return 0.0  
    frac = float(failure_count) / float(usage_count)  
    stability = 1.0 - frac  
    if stability < 0.0:  
        return 0.0  
    if stability > 1.0:  
        return 1.0  
    return stability  
  
  
def analyze_selector_stability(history_rows: List[Dict[str, Any]]) -> Dict[str, Any]:  
    """  
    Output structure:  
    {  
      "selectors": [ {key, usage_count, failure_count, workflows, stability_score, flaky}, ... ],  
      "low_stability": [...],  
      "high_risk": [...],  
      "stats": {...}  
    }  
    """  
    # Aggregate  
    agg: Dict[str, Dict[str, Any]] = {}  
    total_rows = 0  
    selector_rows = 0  
  
    for row in history_rows:  
        if not isinstance(row, dict):  
            continue  
        total_rows += 1  
        key = _selector_key(row)  
        if not key:  
            continue  
        selector_rows += 1  
  
        wf = _workflow_name(row)  
        is_fail = _is_failure(row)  
  
        a = agg.setdefault(  
            key,  
            {"key": key, "usage_count": 0, "failure_count": 0, "workflows": set(), "success_count": 0},  
        )  
        a["usage_count"] += 1  
        a["workflows"].add(wf)  
        if is_fail:  
            a["failure_count"] += 1  
        else:  
            a["success_count"] += 1  
  
    selectors: List[Dict[str, Any]] = []  
    for key, a in agg.items():  
        usage = int(a["usage_count"])  
        fail = int(a["failure_count"])  
        succ = int(a["success_count"])  
        st = score_selector(key, usage, fail)  
  
        # "flaky": both successes and failures exist (intermittent)  
        flaky = (fail > 0 and succ > 0)  
  
        selectors.append(  
            {  
                "key": key,  
                "usage_count": usage,  
                "failure_count": fail,  
                "stability_score": st,  
                "workflows": sorted(a["workflows"]),  
                "workflow_count": len(a["workflows"]),  
                "flaky": flaky,  
            }  
        )  
  
    # Deterministic order for base list  
    selectors.sort(key=lambda x: (x["key"]))  
  
    # Low stability threshold  
    low_stability = [s for s in selectors if s["usage_count"] >= 2 and s["stability_score"] < 0.8]  
  
    # High risk: low stability OR high impact (many workflows) with some failure  
    high_risk = []  
    for s in selectors:  
        if s["failure_count"] == 0:  
            continue  
        if s["workflow_count"] >= 2:  
            high_risk.append(s)  
            continue  
        if s["usage_count"] >= 5 and s["stability_score"] < 0.9:  
            high_risk.append(s)  
            continue  
        if s["stability_score"] < 0.7:  
            high_risk.append(s)  
  
    # Sort risk lists deterministically by severity  
    low_stability.sort(key=lambda x: (x["stability_score"], -x["usage_count"], x["key"]))  
    high_risk.sort(key=lambda x: (x["stability_score"], -x["workflow_count"], -x["usage_count"], x["key"]))  
  
    return {  
        "selectors": selectors,  
        "low_stability": low_stability,  
        "high_risk": high_risk,  
        "stats": {  
            "rows": total_rows,  
            "selector_rows": selector_rows,  
            "unique_selectors": len(selectors),  
        },  
    }  
  
  
def _confidence(usage: int, failure: int, stability: float, workflow_count: int) -> float:  
    # Deterministic heuristic: more data + more failures + broader impact => higher confidence.  
    base = 0.55  
    if usage >= 10:  
        base += 0.15  
    elif usage >= 5:  
        base += 0.10  
    elif usage >= 3:  
        base += 0.05  
  
    if failure >= 5:  
        base += 0.15  
    elif failure >= 2:  
        base += 0.10  
    elif failure >= 1:  
        base += 0.05  
  
    if workflow_count >= 3:  
        base += 0.10  
    elif workflow_count >= 2:  
        base += 0.05  
  
    if stability < 0.7:  
        base += 0.05  
  
    if base > 0.95:  
        base = 0.95  
    return round(base, 2)  
  
  
def generate_selector_recommendations(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:  
    """  
    Generates general but actionable recommendations.  
    Does not invent new step types; "action" here is a meta-recommendation label.  
    """  
    selectors = analysis.get("high_risk")  
    if not isinstance(selectors, list):  
        return []  
  
    recs: List[Dict[str, Any]] = []  
  
    for s in selectors[:25]:  
        if not isinstance(s, dict):  
            continue  
  
        key = _as_str(s.get("key"))  
        usage = int(s.get("usage_count") or 0)  
        fail = int(s.get("failure_count") or 0)  
        stability = float(s.get("stability_score") or 0.0)  
        wf_count = int(s.get("workflow_count") or 0)  
        flaky = bool(s.get("flaky"))  
  
        suggestion_parts = [  
            "Prefer stable attributes (data-testid / aria-label / name) over brittle CSS paths.",  
            "Avoid nth-child and overly generic selectors; target unique attributes.",  
        ]  
        if key.startswith("xpath:"):  
            suggestion_parts.append("If possible, replace complex XPath with attribute-based CSS or selector_ref mapping.")  
        if flaky:  
            suggestion_parts.append("Intermittent failures suggest timing/animation issues; pair interactions with wait_for_selector and retry via repeat.")  
        if "selector_ref:" in key:  
            suggestion_parts.append("If selector_ref maps to multiple possible DOM shapes, split into more specific refs per page/context.")  
  
        recs.append(  
            {  
                "action": "improve_selector",  
                "target": key,  
                "suggestion": " ".join(suggestion_parts),  
                "reason": f"stability={stability:.2f} (failures={fail}/{usage}), workflows={wf_count}",  
                "confidence": _confidence(usage, fail, stability, wf_count),  
            }  
        )  
  
        # Additional recommendation when likely timing-related  
        if flaky or stability < 0.7:  
            recs.append(  
                {  
                    "action": "add_wait",  
                    "target": key,  
                    "suggestion": "Insert wait_for_selector immediately before click_selector/type_selector_secret using this selector.",  
                    "reason": "Selector appears unstable/flaky; explicit waits reduce race conditions.",  
                    "confidence": max(0.6, _confidence(usage, fail, stability, wf_count) - 0.05),  
                }  
            )  
  
    # Deterministic de-duplication  
    seen = set()  
    out: List[Dict[str, Any]] = []  
    for r in recs:  
        sig = (r.get("action"), r.get("target"), r.get("suggestion"))  
        if sig in seen:  
            continue  
        seen.add(sig)  
        out.append(r)  
  
    return out  