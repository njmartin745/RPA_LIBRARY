"""  
LEARN-1A — Failure Pattern Analytics (pure, deterministic)  
  
Analyzes HISTORY-1A JSONL rows to identify recurring failure patterns and produce  
actionable recommendations compatible with the existing STEP_GRAMMAR.  
  
No Selenium. No side effects beyond reading a history file in load_history().  
"""  
  
from __future__ import annotations  
  
import json  
from pathlib import Path  
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple  
  
  
__all__ = [  
    "load_history",  
    "extract_failure_patterns",  
    "rank_patterns",  
    "generate_recommendations",  
]  
  
  
# -------------------------  
# small pure helpers  
# -------------------------  
  
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
  
  
def _is_failure(row: Dict[str, Any]) -> bool:  
    # Be flexible: different producers may use different keys.  
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
  
    # If an error category/message exists, treat as failure.  
    err = _dig(row, [["error"], ["error_message"], ["exception"], ["err"]])  
    cat = _dig(row, [["error_category"], ["failure_category"], ["category"]])  
    return bool(err or cat)  
  
  
def _workflow_name(row: Dict[str, Any]) -> str:  
    return _as_str(_dig(row, [["workflow_name"], ["workflow"], ["workflow", "name"]])) or "UNKNOWN_WORKFLOW"  
  
  
def _run_id(row: Dict[str, Any]) -> str:  
    return _as_str(_dig(row, [["run_id"], ["run"], ["run", "id"]])) or "UNKNOWN_RUN"  
  
  
def _failure_category(row: Dict[str, Any]) -> str:  
    cat = _dig(row, [["error_category"], ["failure_category"], ["category"], ["error", "category"]])  
    return (_as_str(cat) or "unknown").lower()  
  
  
def _selector_key(row: Dict[str, Any]) -> Optional[str]:  
    # Prefer selector_ref (framework best practice), then strategy+selector.  
    ref = _dig(row, [["selector_ref"], ["step", "selector_ref"], ["error", "selector_ref"]])  
    if ref:  
        return f"ref={_as_str(ref)}"  
  
    strat = _dig(row, [["strategy"], ["step", "strategy"], ["error", "strategy"]])  
    sel = _dig(row, [["selector"], ["step", "selector"], ["error", "selector"]])  
    if strat and sel:  
        return f"{_as_str(strat)}={_as_str(sel)}"  
  
    return None  
  
  
def _diff_fingerprint(row: Dict[str, Any]) -> Optional[str]:  
    fp = _dig(row, [["diff_fingerprint"], ["diff", "fingerprint"], ["fingerprint"]])  
    return _as_str(fp) if fp else None  
  
  
def _step_action(row: Dict[str, Any]) -> str:  
    act = _dig(row, [["step_action"], ["step", "action"], ["action"]])  
    return _as_str(act).lower() if act else ""  
  
  
def _pattern_key(ptype: str, key: str) -> str:  
    return f"{ptype}::{key}"  
  
  
def _new_pattern(ptype: str, key: str) -> Dict[str, Any]:  
    return {  
        "type": ptype,  
        "key": key,  
        "count": 0,  
        "workflows": set(),  
        "runs": set(),  
        "categories": set(),  
        "actions": set(),  
        "examples": [],  
    }  
  
  
def _finalize_pattern(p: Dict[str, Any]) -> Dict[str, Any]:  
    out = dict(p)  
    out["workflows"] = sorted(out["workflows"])  
    out["runs"] = sorted(out["runs"])  
    out["categories"] = sorted(out["categories"])  
    out["actions"] = sorted(out["actions"])  
    # keep examples small/deterministic  
    out["examples"] = out["examples"][:3]  
    return out  
  
  
# -------------------------  
# public API  
# -------------------------  
  
def load_history(history_path: str | Path = "history/run_history.jsonl") -> List[Dict[str, Any]]:  
    """  
    Load HISTORY-1A JSONL rows. Returns [] if file doesn't exist.  
    """  
    p = Path(history_path)  
    if not p.exists():  
        return []  
    rows: List[Dict[str, Any]] = []  
    for line in p.read_text(encoding="utf-8").splitlines():  
        line = line.strip()  
        if not line:  
            continue  
        rows.append(json.loads(line))  
    return rows  
  
  
def extract_failure_patterns(rows: List[Dict[str, Any]]) -> Dict[str, Any]:  
    """  
    Returns:  
    {  
      "patterns": [ {type, key, count, workflows, runs, ...}, ... ],  
      "stats": { "rows": N, "failures": F }  
    }  
    """  
    patterns: Dict[str, Dict[str, Any]] = {}  
    total = len(rows)  
    failures = 0  
  
    for row in rows:  
        if not isinstance(row, dict):  
            continue  
        if not _is_failure(row):  
            continue  
  
        failures += 1  
        wf = _workflow_name(row)  
        rid = _run_id(row)  
        cat = _failure_category(row)  
        act = _step_action(row)  
  
        # 1) Selector failure patterns  
        sel = _selector_key(row)  
        if sel and ("selector" in cat or "stale" in cat or "timeout" in cat or act in {"wait_for_selector", "click_selector", "type_selector_secret"}):  
            pk = _pattern_key("selector_failure", sel)  
            p = patterns.setdefault(pk, _new_pattern("selector_failure", sel))  
            p["count"] += 1  
            p["workflows"].add(wf)  
            p["runs"].add(rid)  
            p["categories"].add(cat)  
            if act:  
                p["actions"].add(act)  
            if len(p["examples"]) < 3:  
                p["examples"].append({"run_id": rid, "workflow": wf, "category": cat, "action": act})  
  
        # 2) Workflow failure patterns  
        pk2 = _pattern_key("workflow_failure", wf)  
        p2 = patterns.setdefault(pk2, _new_pattern("workflow_failure", wf))  
        p2["count"] += 1  
        p2["workflows"].add(wf)  
        p2["runs"].add(rid)  
        p2["categories"].add(cat)  
        if act:  
            p2["actions"].add(act)  
  
        # 3) DIFF fingerprint cluster patterns  
        fp = _diff_fingerprint(row)  
        if fp:  
            pk3 = _pattern_key("diff_fingerprint_cluster", fp)  
            p3 = patterns.setdefault(pk3, _new_pattern("diff_fingerprint_cluster", fp))  
            p3["count"] += 1  
            p3["workflows"].add(wf)  
            p3["runs"].add(rid)  
            p3["categories"].add(cat)  
            if act:  
                p3["actions"].add(act)  
  
    out_patterns = [_finalize_pattern(p) for p in patterns.values() if p["count"] >= 2]  
    out_patterns.sort(key=lambda x: (x["type"], x["key"]))  
  
    return {  
        "patterns": out_patterns,  
        "stats": {"rows": total, "failures": failures},  
    }  
  
  
def rank_patterns(patterns: Dict[str, Any]) -> List[Dict[str, Any]]:  
    """  
    Returns a list of pattern dicts sorted by severity.  
    Deterministic: sort by (count desc, workflows desc, type, key).  
    """  
    pats = patterns.get("patterns") if isinstance(patterns, dict) else None  
    if not isinstance(pats, list):  
        return []  
  
    ranked: List[Dict[str, Any]] = []  
    for p in pats:  
        if not isinstance(p, dict):  
            continue  
        ranked.append(  
            dict(  
                p,  
                score=(  
                    int(p.get("count") or 0),  
                    len(p.get("workflows") or []),  
                ),  
            )  
        )  
  
    ranked.sort(  
        key=lambda x: (  
            -(x["score"][0]),  
            -(x["score"][1]),  
            _as_str(x.get("type")),  
            _as_str(x.get("key")),  
        )  
    )  
    return ranked  
  
  
def generate_recommendations(ranked_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:  
    """  
    Recommendations are actionable and map to existing STEP_GRAMMAR patterns:  
    - add_wait (wait_for_selector)  
    - add_repeat (repeat polling/retry)  
    - reorder_open (open first)  
    - prefer_exec_js_file (for brittle UI interactions)  
    """  
    recs: List[Dict[str, Any]] = []  
  
    def conf(count: int) -> float:  
        # deterministic bounded confidence  
        if count >= 10:  
            return 0.9  
        if count >= 5:  
            return 0.8  
        if count >= 3:  
            return 0.7  
        return 0.6  
  
    for p in ranked_patterns[:10]:  
        ptype = _as_str(p.get("type"))  
        key = _as_str(p.get("key"))  
        count = int(p.get("count") or 0)  
        actions = [a.lower() for a in (p.get("actions") or [])]  
  
        if ptype == "selector_failure":  
            # If failures happen on click/type, strongly suggest explicit waits and retry structure.  
            if any(a in {"click_selector", "type_selector_secret"} for a in actions):  
                recs.append(  
                    {  
                        "action": "add_wait",  
                        "target": key,  
                        "reason": f"Repeated selector failures ({count}x). Insert wait_for_selector immediately before click/type.",  
                        "confidence": conf(count),  
                    }  
                )  
                recs.append(  
                    {  
                        "action": "add_repeat",  
                        "target": key,  
                        "reason": "For flaky UI, wrap [wait_for_selector, click_selector] in repeat(times=2..3).",  
                        "confidence": max(0.6, conf(count) - 0.1),  
                    }  
                )  
            else:  
                recs.append(  
                    {  
                        "action": "add_wait",  
                        "target": key,  
                        "reason": f"Repeated wait/selector failures ({count}x). Consider polling via repeat around wait_for_selector.",  
                        "confidence": conf(count),  
                    }  
                )  
  
            # Export-like readiness hint (common real workflow pattern)  
            if "EXPORT" in key.upper() or "DOWNLOAD" in key.upper():  
                recs.append(  
                    {  
                        "action": "add_repeat",  
                        "target": key,  
                        "reason": "Export/download is often async; add repeat polling for readiness before triggering export.",  
                        "confidence": max(0.6, conf(count)),  
                    }  
                )  
  
        elif ptype == "diff_fingerprint_cluster":  
            recs.append(  
                {  
                    "action": "prefer_exec_js_file",  
                    "target": key,  
                    "reason": f"Same UI fingerprint diff repeats ({count}x). Consider replacing brittle selector interactions with exec_js_file (stable DOM targeting).",  
                    "confidence": conf(count),  
                }  
            )  
  
        elif ptype == "workflow_failure":  
            recs.append(  
                {  
                    "action": "add_repeat",  
                    "target": key,  
                    "reason": f"Workflow-level failures repeat ({count}x). Consider guarded repeat blocks around login/navigation checkpoints.",  
                    "confidence": conf(count),  
                }  
            )  
  
    # deterministic de-duplication by (action,target,reason)  
    seen = set()  
    out: List[Dict[str, Any]] = []  
    for r in recs:  
        sig = (r.get("action"), r.get("target"), r.get("reason"))  
        if sig in seen:  
            continue  
        seen.add(sig)  
        out.append(r)  
  
    return out  