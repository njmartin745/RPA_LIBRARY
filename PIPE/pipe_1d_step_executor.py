"""  
PIPE-1D — Step Execution Adapter  
  
Goal  
----  
Normalize step dictionaries from PIPE-1C and safely route them to the ACT engine.  
  
Public API  
----------  
execute_step(driver, step: dict, cfg: dict) -> dict  
    Returns:  
        {  
            "ok": bool,  
            "result": Any,  
            "error": str | None  
        }  
  
Notes  
-----  
- Does not duplicate ACT logic; delegates execution to ACT.act_1a_action_engine.run_actions  
  for supported actions.  
- Performs minimal normalization for common step shapes (e.g., by/value -> selector).  
"""  
  
from __future__ import annotations  
  
from typing import Any, Dict, Mapping, MutableMapping, Optional  
  
from ACT.act_1a_action_engine import run_actions  # type: ignore  
  
  
__all__ = ["execute_step"]  
  
  
_ACTION_ALIASES = {  
    # get  
    "navigate": "get",  
    "open": "get",  
    "go": "get",  
    # wait_for_element  
    "wait": "wait_for_element",  
    "wait_for": "wait_for_element",  
    # js  
    "javascript": "js",  
    "eval": "js",  
    # click  
    "tap": "click",  
    # download_wait  
    "wait_for_download": "download_wait",  
}  
  
  
_SUPPORTED_ACTIONS = {"get", "wait_for_element", "click", "js", "download_wait"}  
  
  
def _as_str(v: Any) -> Optional[str]:  
    if v is None:  
        return None  
    if isinstance(v, str):  
        s = v.strip()  
        return s if s else None  
    return str(v)  
  
  
def _build_selector(by: str, value: str) -> str:  
    by_norm = by.strip().lower()  
    val = value.strip()  
  
    if by_norm in {"css", "css_selector", "cssselector"}:  
        # ACT-1A commonly treats a bare string as a CSS selector.  
        return val  
    if by_norm == "xpath":  
        # Common convention used across many internal RPA libs.  
        return f"xpath={val}"  
    return f"{by_norm}={val}"  
  
  
def _normalize_step(step: Mapping[str, Any]) -> Dict[str, Any]:  
    """  
    Normalize common user-friendly shapes into the schema ACT expects.  
  
    Supported actions:  
      - get: requires url  
      - wait_for_element: requires selector (or by/value)  
      - click: requires selector (or by/value)  
      - js: requires script  
      - download_wait: requires pattern  
    """  
    normalized: Dict[str, Any] = dict(step)  
  
    action_raw = _as_str(normalized.get("action"))  
    if not action_raw:  
        raise ValueError("Step is missing required key 'action' (string).")  
  
    action = _ACTION_ALIASES.get(action_raw.strip().lower(), action_raw.strip().lower())  
    normalized["action"] = action  
  
    if action not in _SUPPORTED_ACTIONS:  
        raise ValueError(  
            f"Unsupported action '{action}'. Supported actions: {sorted(_SUPPORTED_ACTIONS)}"  
        )  
  
    if action == "get":  
        url = _as_str(normalized.get("url")) or _as_str(normalized.get("href"))  
        if not url:  
            raise ValueError("Action 'get' requires 'url' (or 'href').")  
        normalized["url"] = url  
  
    elif action in {"wait_for_element", "click"}:  
        selector = _as_str(normalized.get("selector")) or _as_str(normalized.get("css"))  
        if not selector:  
            by = _as_str(normalized.get("by"))  
            value = _as_str(normalized.get("value"))  
            if by and value:  
                selector = _build_selector(by, value)  
                normalized["selector"] = selector  
            else:  
                raise ValueError(  
                    f"Action '{action}' requires 'selector' (or 'by' + 'value'). "  
                    f"Got keys: {sorted(normalized.keys())}"  
                )  
        else:  
            normalized["selector"] = selector  
  
    elif action == "js":  
        script = _as_str(normalized.get("script")) or _as_str(normalized.get("code"))  
        if not script:  
            raise ValueError("Action 'js' requires 'script' (or 'code').")  
        normalized["script"] = script  
  
    elif action == "download_wait":  
        pattern = _as_str(normalized.get("pattern")) or _as_str(normalized.get("glob"))  
        if not pattern:  
            raise ValueError("Action 'download_wait' requires 'pattern' (or 'glob').")  
        normalized["pattern"] = pattern  
  
    return normalized  
  
  
def execute_step(driver: Any, step: dict, cfg: dict) -> dict:  
    """  
    Execute a single step via the ACT engine with normalization and safe error capture.  
  
    Returns:  
        {  
            "ok": bool,  
            "result": any,  
            "error": str | None  
        }  
    """  
    try:  
        if not isinstance(step, dict):  
            raise ValueError(f"Step must be a dict. Got: {type(step).__name__}")  
  
        # Do not mutate caller's step; normalize into a fresh dict.  
        norm_step = _normalize_step(step)  
  
        # Delegate to ACT engine (no duplication of action implementations).  
        outcomes = run_actions(driver, [norm_step], cfg, fail_fast=True)  
  
        # Be defensive about outcome shape.  
        if isinstance(outcomes, list) and outcomes:  
            out0 = outcomes[0]  
            if isinstance(out0, dict):  
                ok = bool(out0.get("ok", True))  
                err = out0.get("error")  
                err_s = _as_str(err)  
                return {"ok": ok, "result": out0.get("result", out0), "error": (None if ok else (err_s or "Step failed"))}  
            # Unknown outcome structure; treat as success unless exception was raised.  
            return {"ok": True, "result": out0, "error": None}  
  
        # No outcomes returned; treat as success but note emptiness in result.  
        return {"ok": True, "result": outcomes, "error": None}  
  
    except Exception as e:  
        return {"ok": False, "result": None, "error": f"{type(e).__name__}: {e}"}  