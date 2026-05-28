"""  
PIPE-2B — Step Blocks & Branching (if/else + try blocks).  
  
Adds support for block steps expressed in steps.json without new Python code:  
- action: "if"  
- action: "group"  
- action: "try"  
  
Key requirements:  
- Uses VAR-1A rendering (via PIPE-2A render/execute adapter).  
- Uses ACT-1C conditional guard helpers for if conditions.  
- Leaf steps are executed through existing leaf-step executor via PIPE-2A wrapper.  
- Headless-safe, deterministic.  
- Must not mutate the original steps list.  
  
Public API  
----------  
run_steps(driver, steps: list[dict], cfg: dict) -> list[dict]  
"""  
  
from __future__ import annotations  
  
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple  
  
from ACT.act_1c_conditional_guards import element_exists, text_contains, text_equals  
from PIPE.pipe_2a_var_aware_steps import execute_step_var_aware, render_step  
  
__all__ = ["run_steps"]  
  
  
def _as_bool(v: Any) -> bool:  
    if isinstance(v, bool):  
        return v  
    if isinstance(v, (int, float)):  
        return bool(v)  
    if isinstance(v, str):  
        s = v.strip().lower()  
        if s in {"1", "true", "yes", "y", "on"}:  
            return True  
        if s in {"0", "false", "no", "n", "off"}:  
            return False  
    return bool(v)  
  
  
def _result_ok(res: Any) -> bool:  
    if isinstance(res, Mapping):  
        ok = res.get("ok", None)  
        return bool(ok) if ok is not None else False  
    return bool(res)  
  
  
def _safe_list(x: Any) -> List[Any]:  
    if x is None:  
        return []  
    if isinstance(x, list):  
        return list(x)  
    if isinstance(x, tuple):  
        return list(x)  
    return []  
  
  
def _eval_if_condition(driver: Any, cond: Mapping[str, Any]) -> bool:  
    """  
    cond format:  
      {  
        "type": "exists" | "text_contains" | "text_equals",  
        "by": "css" | "xpath" | ...,  
        "value": "<selector>",  
        "text": "<expected>"   # for text_* only  
      }  
    """  
    try:  
        ctype = str(cond.get("type", "")).strip().lower()  
        by = cond.get("by", "css")  
        sel = cond.get("value", "")  
  
        if ctype == "exists":  
            return element_exists(driver, by, sel)  
  
        if ctype == "text_contains":  
            return text_contains(driver, by, sel, cond.get("text", ""))  
  
        if ctype == "text_equals":  
            return text_equals(driver, by, sel, cond.get("text", ""))  
  
        return False  
    except Exception:  
        return False  
  
  
def _run_leaf(  
    driver: Any,  
    step: Mapping[str, Any],  
    cfg: MutableMapping[str, Any],  
    *,  
    step_index: int,  
) -> Dict[str, Any]:  
    """  
    Execute a normal (leaf) step through PIPE-2A so ${VAR} substitution is applied.  
    """  
    leaf_executor = cfg.get("LEAF_EXECUTOR")  
    if leaf_executor is not None and not callable(leaf_executor):  
        leaf_executor = None  
  
    res = execute_step_var_aware(driver, step, cfg, step_index=step_index, executor=leaf_executor)  
    if isinstance(res, dict):  
        return res  
    return {"ok": bool(res), "action": step.get("action"), "result": res}  
  
  
def _run_steps_inner(  
    driver: Any,  
    steps: Sequence[Mapping[str, Any]],  
    cfg: MutableMapping[str, Any],  
    *,  
    stop_on_error: bool,  
) -> List[Dict[str, Any]]:  
    """  
    Run a list of steps (top-level or nested). Returns per-step results.  
    Does not mutate the input steps.  
    """  
    results: List[Dict[str, Any]] = []  
  
    for i, raw_step in enumerate(list(steps)):  
        # Render the step dict itself (block metadata, selectors, etc.) without mutating original.  
        step = render_step(raw_step, cfg, step_index=i)  
        action = step.get("action") if isinstance(step, Mapping) else None  
  
        if not isinstance(step, Mapping):  
            r = {"ok": False, "action": action, "error": "Invalid step type: expected dict"}  
            results.append(r)  
            if stop_on_error:  
                break  
            continue  
  
        if action == "group":  
            name = step.get("name")  
            sub = _safe_list(step.get("steps"))  
            sub_results = _run_steps_inner(driver, sub, cfg, stop_on_error=stop_on_error)  
            ok = all(_result_ok(x) for x in sub_results) if sub_results else True  
            r = {"ok": ok, "name": name, "results": sub_results}  
            results.append(r)  
            if stop_on_error and not ok:  
                break  
            continue  
  
        if action == "if":  
            cond = step.get("condition") or {}  
            cond = cond if isinstance(cond, Mapping) else {}  
            taken: str = "none"  
  
            if _eval_if_condition(driver, cond):  
                taken = "then"  
                branch = _safe_list(step.get("then"))  
            else:  
                taken = "else"  
                branch = _safe_list(step.get("else"))  
  
            branch_results = _run_steps_inner(driver, branch, cfg, stop_on_error=stop_on_error) if branch else []  
            ok = all(_result_ok(x) for x in branch_results) if branch_results else True  
            r = {"ok": ok, "taken": taken, "results": branch_results}  
            results.append(r)  
            if stop_on_error and not ok:  
                break  
            continue  
  
        if action == "try":  
            main_steps = _safe_list(step.get("steps"))  
            catch_steps = _safe_list(step.get("catch"))  
            finally_steps = _safe_list(step.get("finally"))  
  
            main_results: List[Dict[str, Any]] = []  
            catch_results: List[Dict[str, Any]] = []  
            finally_results: List[Dict[str, Any]] = []  
  
            main_failed = False  
            # In STOP_ON_ERROR mode, "try" should not contain the error.  
            contain_errors = not stop_on_error  
  
            # Run main  
            for j, s in enumerate(main_steps):  
                rr = _run_steps_inner(driver, [s], cfg, stop_on_error=False)[0]  
                main_results.append(rr)  
                if not _result_ok(rr):  
                    main_failed = True  
                    if not contain_errors:  
                        break  # do not run catch; will still run finally  
                    # contain: stop main section, proceed to catch/finally  
                    break  
  
            # Run catch if contained failure  
            if main_failed and contain_errors and catch_steps:  
                catch_results = _run_steps_inner(driver, catch_steps, cfg, stop_on_error=False)  
  
            # Run finally always if present (even when STOP_ON_ERROR True)  
            if finally_steps:  
                finally_results = _run_steps_inner(driver, finally_steps, cfg, stop_on_error=False)  
  
            # Determine ok  
            ok_main = (not main_failed) and all(_result_ok(x) for x in main_results)  
            ok_catch = all(_result_ok(x) for x in catch_results) if catch_results else (True if contain_errors else True)  
            ok_finally = all(_result_ok(x) for x in finally_results) if finally_results else True  
  
            if not main_failed:  
                ok_try = ok_main and ok_finally  
            else:  
                # contained failure => ok depends on catch+finally; uncontained => fail  
                ok_try = (ok_catch and ok_finally) if contain_errors else False  
  
            r = {  
                "ok": ok_try,  
                "results": main_results,  
                "catch_results": catch_results,  
                "finally_results": finally_results,  
                "contained": bool(contain_errors and main_failed),  
            }  
            results.append(r)  
  
            if stop_on_error and not ok_try:  
                break  
            continue  
  
        # Leaf step  
        r = _run_leaf(driver, step, cfg, step_index=i)  
        results.append(r)  
        if stop_on_error and not _result_ok(r):  
            break  
  
    return results  
  
  
def run_steps(driver: Any, steps: List[Dict[str, Any]], cfg: Dict[str, Any]) -> List[Dict[str, Any]]:  
    """  
    Execute a steps list supporting:  
      - leaf steps (delegated to PIPE-2A var-aware execution + leaf executor)  
      - blocks: if/group/try  
  
    Returns per-step result dicts.  
    """  
    stop_on_error = _as_bool(cfg.get("STOP_ON_ERROR", False))  
    # Ensure we don't mutate caller's cfg store outside intended vars/keys; run uses cfg as runtime context.  
    return _run_steps_inner(driver, steps, cfg, stop_on_error=stop_on_error)  