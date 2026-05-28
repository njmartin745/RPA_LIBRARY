# GUARD/guard_1a_runtime.py  
"""  
GUARD-1A — Runtime Guardrails (stability layer)  
  
Pure wrapper utilities:  
- No Selenium driver creation  
- Must NOT duplicate ACT/NAV logic (wrap existing runners only)  
  
Public API:  
  wrap_step_runner(step_runner_fn, *, cfg) -> wrapped_fn  
  guarded_call(fn, *, retries, retry_on, on_retry=None) -> object  
  normalize_guard_cfg(cfg) -> dict  
"""  
  
from __future__ import annotations  
  
from typing import Any, Callable, Dict, Optional, Tuple  
  
__all__ = [  
    "wrap_step_runner",  
    "guarded_call",  
    "normalize_guard_cfg",  
]  
  
# Selenium exceptions are optional at import-time (smoke tests may not have Selenium installed)  
try:  # pragma: no cover  
    from selenium.common.exceptions import (  # type: ignore  
        StaleElementReferenceException,  
        ElementClickInterceptedException,  
        TimeoutException,  
    )  
except Exception:  # pragma: no cover  
    class StaleElementReferenceException(Exception):  
        pass  
  
    class ElementClickInterceptedException(Exception):  
        pass  
  
    class TimeoutException(Exception):  
        pass  
  
  
_DEFAULTS = {  
    "GUARD_ENABLED": True,  
    "GUARD_RETRIES": 1,  
    "GUARD_RETRY_ON": ["StaleElementReferenceException", "ElementClickInterceptedException"],  
    "GUARD_STEP_TIMEOUT_BUMP_PCT": 0.5,  
    "GUARD_MAX_TIMEOUT": 60,  
}  
  
  
_NAME_TO_EXC: Dict[str, type[BaseException]] = {  
    "StaleElementReferenceException": StaleElementReferenceException,  
    "ElementClickInterceptedException": ElementClickInterceptedException,  
    "TimeoutException": TimeoutException,  
}  
  
  
def normalize_guard_cfg(cfg: dict) -> dict:  
    """  
    Returns a normalized guard config dict with defaults applied.  
    Keeps only the guard keys (and leaves caller's cfg untouched).  
    """  
    src = cfg if isinstance(cfg, dict) else {}  
    out: dict = {}  
  
    for k, dv in _DEFAULTS.items():  
        out[k] = src.get(k, dv)  
  
    # Normalize types  
    out["GUARD_ENABLED"] = bool(out["GUARD_ENABLED"])  
  
    try:  
        out["GUARD_RETRIES"] = int(out["GUARD_RETRIES"])  
    except Exception:  
        out["GUARD_RETRIES"] = int(_DEFAULTS["GUARD_RETRIES"])  
    if out["GUARD_RETRIES"] < 0:  
        out["GUARD_RETRIES"] = 0  
  
    try:  
        out["GUARD_STEP_TIMEOUT_BUMP_PCT"] = float(out["GUARD_STEP_TIMEOUT_BUMP_PCT"])  
    except Exception:  
        out["GUARD_STEP_TIMEOUT_BUMP_PCT"] = float(_DEFAULTS["GUARD_STEP_TIMEOUT_BUMP_PCT"])  
    if out["GUARD_STEP_TIMEOUT_BUMP_PCT"] < 0:  
        out["GUARD_STEP_TIMEOUT_BUMP_PCT"] = 0.0  
  
    try:  
        out["GUARD_MAX_TIMEOUT"] = int(out["GUARD_MAX_TIMEOUT"])  
    except Exception:  
        out["GUARD_MAX_TIMEOUT"] = int(_DEFAULTS["GUARD_MAX_TIMEOUT"])  
    if out["GUARD_MAX_TIMEOUT"] <= 0:  
        out["GUARD_MAX_TIMEOUT"] = int(_DEFAULTS["GUARD_MAX_TIMEOUT"])  
  
    retry_on = out.get("GUARD_RETRY_ON")  
    if isinstance(retry_on, str):  
        retry_on_list = [retry_on]  
    elif isinstance(retry_on, list):  
        retry_on_list = [x for x in retry_on if isinstance(x, str)]  
    else:  
        retry_on_list = list(_DEFAULTS["GUARD_RETRY_ON"])  
  
    # Deduplicate deterministically while preserving order  
    seen = set()  
    dedup: list[str] = []  
    for n in retry_on_list:  
        nn = n.strip()  
        if nn and nn not in seen:  
            dedup.append(nn)  
            seen.add(nn)  
    out["GUARD_RETRY_ON"] = dedup  
  
    return out  
  
  
def _retry_on_types(guard_cfg: dict) -> Tuple[type, ...]:  
    names = guard_cfg.get("GUARD_RETRY_ON") or []  
    types: list[type] = []  
    for n in names:  
        t = _NAME_TO_EXC.get(n)  
        if t is not None:  
            types.append(t)  
    # Deterministic fallback: if nothing recognized, use empty tuple (no retry)  
    return tuple(types)  
  
  
def guarded_call(  
    fn: Callable[[], Any],  
    *,  
    retries: int,  
    retry_on: Tuple[type, ...],  
    on_retry: Optional[Callable[[BaseException, int], None]] = None,  
) -> Any:  
    """  
    Calls fn(); retries on exceptions in retry_on up to `retries` times.  
    - retries=1 means: at most 1 retry (2 total attempts).  
    - re-raises the last exception if exhausted.  
    """  
    if retries < 0:  
        retries = 0  
  
    attempt = 0  
    while True:  
        try:  
            return fn()  
        except BaseException as e:  
            if retry_on and isinstance(e, retry_on) and attempt < retries:  
                attempt += 1  
                if callable(on_retry):  
                    try:  
                        on_retry(e, attempt)  
                    except Exception:  
                        # guardrails should not introduce new failures here  
                        pass  
                continue  
            raise  
  
  
def _infer_step_index_from_exception(exc: BaseException) -> Optional[int]:  
    for k in ("step_index", "failing_step_index", "index"):  
        v = getattr(exc, k, None)  
        if isinstance(v, int) and v >= 0:  
            return v  
    return None  
  
  
def _build_failure_notes_for_timeout(  
    *,  
    steps: list[dict],  
    guard_cfg: dict,  
    exc: BaseException,  
) -> dict:  
    bump_pct = float(guard_cfg["GUARD_STEP_TIMEOUT_BUMP_PCT"])  
    max_timeout = int(guard_cfg["GUARD_MAX_TIMEOUT"])  
  
    idx = _infer_step_index_from_exception(exc)  
    suggestions: list[dict] = []  
  
    def suggest_for(i: int, step: dict) -> None:  
        t = step.get("timeout")  
        if isinstance(t, (int, float)):  
            old = float(t)  
            new = min(float(max_timeout), max(0.0, old) * (1.0 + bump_pct))  
            suggestions.append(  
                {  
                    "step_index": i,  
                    "old_timeout": int(round(old)),  
                    "suggested_timeout": int(round(new)),  
                    "cap": max_timeout,  
                    "bump_pct": bump_pct,  
                }  
            )  
  
    if idx is not None and 0 <= idx < len(steps):  
        suggest_for(idx, steps[idx])  
    else:  
        # Best-effort (no step index): suggest for steps that already have timeout  
        for i, s in enumerate(steps):  
            if isinstance(s, dict) and "timeout" in s:  
                suggest_for(i, s)  
  
    return {  
        "category": "TIMEOUT",  
        "timeout_suggestions": suggestions,  
        "note": "Suggested timeout bumps only (workflow not modified).",  
    }  
  
  
def _build_iframe_note_if_suspected(steps: list[dict]) -> Optional[dict]:  
    # Heuristic-only, no new reasoning: look for hints in step fields.  
    for i, s in enumerate(steps):  
        if not isinstance(s, dict):  
            continue  
        if any(k in s for k in ("frame_ref", "iframe", "frame", "frame_index")):  
            return {  
                "category": "IFRAME_CONTEXT",  
                "step_index_hint": i,  
                "note": "Step appears to reference an iframe/frame; consider inserting a schema-supported switch_to_frame step before the failing step.",  
            }  
    return None  
  
  
def wrap_step_runner(step_runner_fn: Callable[..., Any], *, cfg: dict):  
    """  
    Returns a wrapped runner function with guardrails applied.  
  
    step_runner_fn signature expected:  
      (driver, steps: list[dict], cfg: dict) -> dict|None  
  
    Best-effort behavior without refactoring:  
    - Wraps the entire step_runner_fn call in guarded_call() (no per-step refactor).  
    - Retries on configured transient Selenium exceptions.  
    - On final failure, attaches exc.guard_diagnostics if possible, then re-raises.  
    """  
    guard_cfg_base = normalize_guard_cfg(cfg)  
  
    def wrapped(driver, steps: list[dict], cfg_in: dict) -> Any:  
        # Merge + normalize at call-time deterministically  
        merged = dict(cfg_in) if isinstance(cfg_in, dict) else {}  
        for k, v in guard_cfg_base.items():  
            merged.setdefault(k, v)  
        guard_cfg = normalize_guard_cfg(merged)  
  
        if not guard_cfg["GUARD_ENABLED"]:  
            return step_runner_fn(driver, steps, cfg_in)  
  
        retry_on_types = _retry_on_types(guard_cfg)  
        retries = int(guard_cfg["GUARD_RETRIES"])  
  
        retry_count = 0  
  
        def _on_retry(exc: BaseException, attempt_no: int) -> None:  
            nonlocal retry_count  
            retry_count = attempt_no  
  
        def _call():  
            return step_runner_fn(driver, steps, cfg_in)  
  
        try:  
            return guarded_call(_call, retries=retries, retry_on=retry_on_types, on_retry=_on_retry)  
        except BaseException as e:  
            diag: dict = {  
                "category": "GUARD_RETRY_EXHAUSTED" if retry_count > 0 else "GUARD_FAILURE",  
                "retry_count": int(retry_count),  
                "retries_configured": int(retries),  
                "retry_on": list(guard_cfg.get("GUARD_RETRY_ON") or []),  
            }  
  
            # TIMEOUT-style suggestions (no workflow rewrite)  
            if isinstance(e, TimeoutException) or "timeout" in type(e).__name__.lower():  
                diag["timeout"] = _build_failure_notes_for_timeout(steps=steps, guard_cfg=guard_cfg, exc=e)  
  
            # Iframe hints (no action invention)  
            iframe_note = _build_iframe_note_if_suspected(steps)  
            if iframe_note:  
                diag["iframe"] = iframe_note  
  
            # Attach to exception if possible, then re-raise  
            try:  
                setattr(e, "guard_diagnostics", diag)  
            except Exception:  
                pass  
            raise  
  
    return wrapped  