"""  
BUILD-2B — Workflow Plan Optimizer (pure transformation)  
  
Takes a spec (from BUILD-2A or BUILD-1B) and optimizes it *before* BUILD-1A  
compiles it into a workflow.  
  
Constraints:  
- No Selenium execution.  
- Deterministic.  
- Only uses existing STEP_GRAMMAR actions (does not invent new step types).  
- Does not remove non-redundant required steps (conservative removals only).  
"""  
  
from __future__ import annotations  
  
import copy  
from typing import Any, Dict, List, Optional, Sequence, Tuple  
  
  
__all__ = [  
    "analyze_spec",  
    "apply_optimizations",  
    "optimize_spec",  
]  
  
  
SUPPORTED_ACTIONS: Tuple[str, ...] = (  
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
  
  
# ----------------------------  
# selectors / step primitives  
# ----------------------------  
  
def _selector_key(step: Dict[str, Any]) -> Optional[Tuple[str, str]]:  
    """  
    Returns a stable identity for selector-bearing steps.  
    Prefers selector_ref; falls back to (strategy, selector) if present.  
    """  
    if not isinstance(step, dict):  
        return None  
    if step.get("selector_ref"):  
        return ("ref", str(step["selector_ref"]))  
    strat = step.get("strategy")  
    sel = step.get("selector")  
    if strat and sel:  
        return (strat, str(sel))  
    return None  
  
  
def _is_action(step: Dict[str, Any], action: str) -> bool:  
    return isinstance(step, dict) and step.get("action") == action  
  
  
def _is_wait(step: Dict[str, Any]) -> bool:  
    return _is_action(step, "wait_for_selector")  
  
  
def _is_click(step: Dict[str, Any]) -> bool:  
    return _is_action(step, "click_selector")  
  
  
def _is_type_secret(step: Dict[str, Any]) -> bool:  
    return _is_action(step, "type_selector_secret")  
  
  
def _is_log(step: Dict[str, Any]) -> bool:  
    return _is_action(step, "log")  
  
  
def _is_repeat(step: Dict[str, Any]) -> bool:  
    return _is_action(step, "repeat")  
  
  
def _is_exportish(step: Dict[str, Any]) -> bool:  
    if not isinstance(step, dict):  
        return False  
    if step.get("action") == "click_selector":  
        ref = (step.get("selector_ref") or "").upper()  
        name = (step.get("name") or "").upper()  
        return any(k in ref for k in ("EXPORT", "DOWNLOAD")) or any(k in name for k in ("EXPORT", "DOWNLOAD"))  
    if step.get("action") == "exec_js_file":  
        path = (step.get("path") or "").lower()  
        name = (step.get("name") or "").lower()  
        return any(k in path for k in ("download", "export")) or any(k in name for k in ("download", "export"))  
    return False  
  
  
def _mk_wait_like(step_with_selector: Dict[str, Any], *, name: Optional[str] = None) -> Dict[str, Any]:  
    """  
    Create a wait_for_selector step matching a given selector-bearing step.  
    """  
    out: Dict[str, Any] = {"action": "wait_for_selector"}  
    if step_with_selector.get("selector_ref"):  
        out["selector_ref"] = step_with_selector["selector_ref"]  
    else:  
        if step_with_selector.get("strategy"):  
            out["strategy"] = step_with_selector["strategy"]  
        if step_with_selector.get("selector"):  
            out["selector"] = step_with_selector["selector"]  
    if name:  
        out["name"] = name  
    return out  
  
  
def _strip_nonsemantic_keys(step: Dict[str, Any]) -> Dict[str, Any]:  
    """  
    For duplicate detection: ignore cosmetic keys that should not affect meaning.  
    (Keep it conservative to avoid removing required steps.)  
    """  
    if not isinstance(step, dict):  
        return step  
    ignored = {"name"}  
    return {k: v for k, v in step.items() if k not in ignored}  
  
  
# ----------------------------  
# analysis  
# ----------------------------  
  
def _analyze_steps(steps: Sequence[Dict[str, Any]], *, warnings: List[str]) -> Dict[str, Any]:  
    dup_waits = 0  
    missing_waits = 0  
    repeated_wait_click_runs = 0  
    export_actions = 0  
    export_ready_waits = 0  
    open_not_first = False  
  
    if steps:  
        # open ordering check (top-level semantics; only meaningful for direct step lists)  
        # We'll also compute it here for convenience.  
        first_nonlog_idx = None  
        first_open_idx = None  
        for i, st in enumerate(steps):  
            if first_open_idx is None and _is_action(st, "open"):  
                first_open_idx = i  
            if first_nonlog_idx is None and not _is_log(st):  
                first_nonlog_idx = i  
        if first_open_idx is not None and first_nonlog_idx is not None and first_open_idx > first_nonlog_idx:  
            open_not_first = True  
  
    prev = None  
    for i, st in enumerate(steps):  
        if not isinstance(st, dict):  
            warnings.append(f"Non-dict step at index {i}: {type(st)}")  
            continue  
  
        act = st.get("action")  
        if act not in SUPPORTED_ACTIONS:  
            warnings.append(f"Unsupported action encountered (left as-is): {act!r} at index {i}")  
  
        if _is_wait(st) and _is_wait(prev):  
            if _selector_key(st) == _selector_key(prev):  
                dup_waits += 1  
  
        if (_is_click(st) or _is_type_secret(st)) and _selector_key(st):  
            # Missing wait if immediately preceded by a non-log step that isn't a wait for same selector  
            j = i - 1  
            while j >= 0 and _is_log(steps[j]):  
                j -= 1  
            if j >= 0:  
                prev_nonlog = steps[j]  
                if not (_is_wait(prev_nonlog) and _selector_key(prev_nonlog) == _selector_key(st)):  
                    missing_waits += 1  
            else:  
                missing_waits += 1  
  
        if _is_exportish(st):  
            export_actions += 1  
  
        if _is_wait(st):  
            sk = _selector_key(st)  
            if sk and sk == ("ref", "EXPORT_READY"):  
                export_ready_waits += 1  
  
        # count repeated wait+click pairs (consecutive pattern)  
        if i + 3 < len(steps):  
            a, b, c, d = steps[i], steps[i + 1], steps[i + 2], steps[i + 3]  
            if _is_wait(a) and _is_click(b) and _is_wait(c) and _is_click(d):  
                if _selector_key(a) and _selector_key(a) == _selector_key(b) == _selector_key(c) == _selector_key(d):  
                    repeated_wait_click_runs += 1  
  
        if _is_repeat(st):  
            inner = st.get("steps")  
            if isinstance(inner, list):  
                inner_a = _analyze_steps(inner, warnings=warnings)  
                dup_waits += inner_a["duplicate_waits"]  
                missing_waits += inner_a["missing_waits_before_actions"]  
                repeated_wait_click_runs += inner_a["repeated_wait_click_runs"]  
                export_actions += inner_a["export_actions"]  
                export_ready_waits += inner_a["export_ready_waits"]  
  
        prev = st  
  
    return {  
        "duplicate_waits": dup_waits,  
        "missing_waits_before_actions": missing_waits,  
        "repeated_wait_click_runs": repeated_wait_click_runs,  
        "export_actions": export_actions,  
        "export_ready_waits": export_ready_waits,  
        "open_not_first": open_not_first,  
    }  
  
  
def analyze_spec(spec: Dict[str, Any]) -> Dict[str, Any]:  
    warnings: List[str] = []  
    steps = spec.get("steps")  
    if not isinstance(steps, list):  
        warnings.append("Spec missing 'steps' list; no optimizations applied to steps.")  
        steps = []  
  
    analysis = _analyze_steps(steps, warnings=warnings)  
  
    # Add some higher-level flags  
    analysis["has_steps"] = bool(steps)  
    analysis["warnings"] = warnings  
    analysis["looks_like_build_2a"] = spec.get("spec_version") == "BUILD-2A"  
    analysis["has_workflow_wrapper"] = isinstance(spec.get("workflow"), dict) and isinstance(spec["workflow"].get("steps"), list)  
    return analysis  
  
  
# ----------------------------  
# optimizations (transformations)  
# ----------------------------  
  
def _dedupe_consecutive_safe(steps: List[Dict[str, Any]], *, applied: List[str]) -> List[Dict[str, Any]]:  
    """  
    Remove *consecutive* duplicates for low-risk actions only.  
    (Conservative: do not dedupe click/type.)  
    """  
    if not steps:  
        return steps  
  
    safe_actions = {"wait_for_selector", "open", "log", "switch_back_to_main_tab"}  
    out: List[Dict[str, Any]] = []  
    prev_sig = None  
  
    for st in steps:  
        if not isinstance(st, dict):  
            out.append(st)  
            prev_sig = None  
            continue  
  
        act = st.get("action")  
        sig = (act, _strip_nonsemantic_keys(st)) if act in safe_actions else None  
  
        if sig is not None and prev_sig is not None and sig == prev_sig:  
            if act == "wait_for_selector":  
                if "remove_duplicate_waits" not in applied:  
                    applied.append("remove_duplicate_waits")  
            elif act == "open":  
                if "remove_duplicate_open" not in applied:  
                    applied.append("remove_duplicate_open")  
            elif act == "log":  
                if "remove_duplicate_log" not in applied:  
                    applied.append("remove_duplicate_log")  
            elif act == "switch_back_to_main_tab":  
                if "remove_duplicate_switch_back" not in applied:  
                    applied.append("remove_duplicate_switch_back")  
            continue  
  
        out.append(st)  
        prev_sig = sig  
  
    return out  
  
  
def _insert_missing_waits(steps: List[Dict[str, Any]], *, applied: List[str]) -> List[Dict[str, Any]]:  
    out: List[Dict[str, Any]] = []  
    for i, st in enumerate(steps):  
        if not isinstance(st, dict):  
            out.append(st)  
            continue  
  
        if _is_repeat(st):  
            inner = st.get("steps")  
            if isinstance(inner, list):  
                st2 = copy.deepcopy(st)  
                st2["steps"] = _insert_missing_waits(inner, applied=applied)  
                out.append(st2)  
                continue  
  
        if (_is_click(st) or _is_type_secret(st)) and _selector_key(st):  
            # Check last non-log output step  
            j = len(out) - 1  
            while j >= 0 and _is_log(out[j]):  
                j -= 1  
            needs_wait = True  
            if j >= 0 and _is_wait(out[j]) and _selector_key(out[j]) == _selector_key(st):  
                needs_wait = False  
            if needs_wait:  
                out.append(_mk_wait_like(st, name="(optimizer) inserted wait"))  
                if "insert_missing_waits_before_actions" not in applied:  
                    applied.append("insert_missing_waits_before_actions")  
  
        out.append(st)  
  
    return out  
  
  
def _consolidate_repeated_wait_click_pairs(steps: List[Dict[str, Any]], *, applied: List[str]) -> List[Dict[str, Any]]:  
    """  
    Convert consecutive [wait X, click X] repeated N times into:  
      repeat(times=N, steps=[wait X, click X])  
    This is a practical retry pattern for flaky UI clicks.  
    """  
    out: List[Dict[str, Any]] = []  
    i = 0  
    while i < len(steps):  
        st = steps[i]  
  
        # recurse for repeat blocks  
        if isinstance(st, dict) and _is_repeat(st) and isinstance(st.get("steps"), list):  
            st2 = copy.deepcopy(st)  
            st2["steps"] = _consolidate_repeated_wait_click_pairs(st2["steps"], applied=applied)  
            out.append(st2)  
            i += 1  
            continue  
  
        if i + 1 < len(steps) and _is_wait(steps[i]) and _is_click(steps[i + 1]):  
            key = _selector_key(steps[i])  
            if key and key == _selector_key(steps[i + 1]):  
                # count consecutive pairs  
                count = 1  
                j = i + 2  
                while j + 1 < len(steps) and _is_wait(steps[j]) and _is_click(steps[j + 1]):  
                    if _selector_key(steps[j]) == key == _selector_key(steps[j + 1]):  
                        count += 1  
                        j += 2  
                    else:  
                        break  
  
                if count >= 2:  
                    rep = {  
                        "action": "repeat",  
                        "times": count,  
                        "name": f"(optimizer) retry click {key[1]}",  
                        "steps": [copy.deepcopy(steps[i]), copy.deepcopy(steps[i + 1])],  
                    }  
                    out.append(rep)  
                    if "consolidate_repeated_wait_click_pairs_into_repeat" not in applied:  
                        applied.append("consolidate_repeated_wait_click_pairs_into_repeat")  
                    i = i + 2 * count  
                    continue  
  
        out.append(st)  
        i += 1  
  
    return out  
  
  
def _add_export_polling_loop(steps: List[Dict[str, Any]], *, applied: List[str], warnings: List[str]) -> List[Dict[str, Any]]:  
    """  
    If an export/download action exists, ensure there's a polling repeat for EXPORT_READY.  
  
    Safe approach:  
    - If we find an existing wait_for_selector EXPORT_READY directly before an export action,  
      wrap that wait into repeat(times=3, steps=[wait EXPORT_READY]).  
    - Else, insert a repeat(times=3, steps=[wait EXPORT_READY]) immediately before the first  
      export action. This does NOT repeat the export click itself.  
    """  
    # Find first export action index  
    export_idx = None  
    for i, st in enumerate(steps):  
        if isinstance(st, dict) and _is_repeat(st) and isinstance(st.get("steps"), list):  
            st2 = copy.deepcopy(st)  
            st2["steps"] = _add_export_polling_loop(st2["steps"], applied=applied, warnings=warnings)  
            steps[i] = st2  
            continue  
        if isinstance(st, dict) and _is_exportish(st):  
            export_idx = i  
            break  
  
    if export_idx is None:  
        return steps  
  
    # If immediately preceded by EXPORT_READY wait, wrap it  
    prev_idx = export_idx - 1  
    if prev_idx >= 0 and _is_wait(steps[prev_idx]) and _selector_key(steps[prev_idx]) == ("ref", "EXPORT_READY"):  
        wait_step = steps[prev_idx]  
        rep = {  
            "action": "repeat",  
            "times": 3,  
            "name": "(optimizer) poll export readiness",  
            "steps": [copy.deepcopy(wait_step)],  
        }  
        new_steps = steps[:prev_idx] + [rep] + steps[export_idx:]  
        if "add_export_polling_repeat_for_export_ready" not in applied:  
            applied.append("add_export_polling_repeat_for_export_ready")  
        return new_steps  
  
    # Otherwise insert polling repeat before export action  
    rep2 = {  
        "action": "repeat",  
        "times": 3,  
        "name": "(optimizer) poll export readiness",  
        "steps": [{"action": "wait_for_selector", "selector_ref": "EXPORT_READY", "name": "Wait for export readiness"}],  
    }  
    warnings.append("Inserted EXPORT_READY polling loop before export action (placeholder selector_ref may need mapping).")  
    if "add_export_polling_repeat_for_export_ready" not in applied:  
        applied.append("add_export_polling_repeat_for_export_ready")  
    return steps[:export_idx] + [rep2] + steps[export_idx:]  
  
  
def _reorder_open_to_front_if_safe(steps: List[Dict[str, Any]], *, applied: List[str]) -> List[Dict[str, Any]]:  
    """  
    If 'open' exists and is preceded only by logs, move it to the front.  
    Conservative: do not reorder across non-log actions.  
    """  
    open_idx = None  
    for i, st in enumerate(steps):  
        if _is_action(st, "open"):  
            open_idx = i  
            break  
        if not _is_log(st):  
            # encountered non-log before open -> unsafe to move  
            return steps  
  
    if open_idx is None or open_idx == 0:  
        return steps  
  
    st_open = steps[open_idx]  
    new_steps = [st_open] + steps[:open_idx] + steps[open_idx + 1 :]  
    if "reorder_open_to_front" not in applied:  
        applied.append("reorder_open_to_front")  
    return new_steps  
  
  
def apply_optimizations(spec: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:  
    optimized = copy.deepcopy(spec)  
    applied: List[str] = []  
    warnings: List[str] = list(analysis.get("warnings") or [])  
  
    steps = optimized.get("steps")  
    if not isinstance(steps, list):  
        # nothing to optimize structurally  
        optimized["optimized"] = True  
        optimized["optimizations_applied"] = applied  
        optimized["warnings"] = warnings  
        return optimized  
  
    # 1) Reorder (safe)  
    steps2 = _reorder_open_to_front_if_safe(list(steps), applied=applied)  
  
    # 2) Optimize nested blocks + consolidate flaky patterns  
    steps2 = _consolidate_repeated_wait_click_pairs(steps2, applied=applied)  
  
    # 3) Remove low-risk consecutive duplicates  
    steps2 = _dedupe_consecutive_safe(steps2, applied=applied)  
  
    # 4) Insert missing waits before click/type  
    steps2 = _insert_missing_waits(steps2, applied=applied)  
  
    # 5) Export polling loop (safe: repeats only readiness waits)  
    steps2 = _add_export_polling_loop(steps2, applied=applied, warnings=warnings)  
  
    optimized["steps"] = steps2  
  
    # Keep workflow wrapper in sync if present  
    if isinstance(optimized.get("workflow"), dict) and isinstance(optimized["workflow"].get("steps"), list):  
        optimized["workflow"]["steps"] = optimized["steps"]  
  
    optimized["optimized"] = True  
    optimized["optimizations_applied"] = applied  
    optimized["warnings"] = warnings  
    return optimized  
  
  
def optimize_spec(spec: Dict[str, Any]) -> Dict[str, Any]:  
    analysis = analyze_spec(spec)  
    return apply_optimizations(spec, analysis)  