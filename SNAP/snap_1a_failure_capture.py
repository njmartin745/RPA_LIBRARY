"""  
SNAP-1A — Failure capture (10.1.1)  
  
Single responsibility:  
- Build a minimal, JSON-serializable snapshot payload containing:  
  - browser state (URL, title, DOM/page_source, optional readyState)  
  - step context (redacted / minimal)  
  - error summary (class + message)  
  - optional workflow/step index context  
  
This module does NOT persist artifacts (10.1.3) and does NOT take screenshots (10.1.2).  
"""  
  
from __future__ import annotations  
  
import datetime as _dt  
from typing import Any, Mapping  
  
__all__ = [  
    "capture_failure_snapshot",  
    "dev_smoke",  
]  
  
  
_REDACT_KEYS = {  
    # Common sensitive keys we never want to log verbatim if they appear  
    "text",  
    "value",  
    "password",  
    "secret",  
    "token",  
    "api_key",  
    "apikey",  
    "authorization",  
}  
  
  
def _utc_now_iso() -> str:  
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()  
  
  
def _safe_getattr(obj: Any, name: str) -> Any:  
    try:  
        return getattr(obj, name)  
    except Exception:  
        return None  
  
  
def _safe_call(func, *args, **kwargs) -> Any:  
    try:  
        return func(*args, **kwargs)  
    except Exception:  
        return None  
  
  
def _redact_step(step: Mapping[str, Any]) -> dict[str, Any]:  
    """  
    Return a redacted shallow copy of the step mapping.  
    - Does not attempt to interpret full schema; only prevents obvious leakage.  
    - Keeps 'secret_ref' intact (it is a reference, not secret content).  
    """  
    out: dict[str, Any] = {}  
    for k, v in step.items():  
        lk = str(k).lower()  
        if lk in _REDACT_KEYS:  
            out[str(k)] = "<redacted>"  
        else:  
            out[str(k)] = v  
    return out  
  
  
def _capture_browser_state(driver: Any) -> dict[str, Any]:  
    """  
    Best-effort capture of browser state without raising.  
    """  
    current_url = _safe_getattr(driver, "current_url")  
    title = _safe_getattr(driver, "title")  
    page_source = _safe_getattr(driver, "page_source")  
  
    ready_state = None  
    exec_script = _safe_getattr(driver, "execute_script")  
    if callable(exec_script):  
        ready_state = _safe_call(exec_script, "return document.readyState")  
  
    return {  
        "url": current_url,  
        "title": title,  
        "dom_html": page_source,  
        "ready_state": ready_state,  
    }  
  
  
def capture_failure_snapshot(  
    *,  
    driver: Any,  
    step: Mapping[str, Any],  
    error: BaseException,  
    workflow_name: str | None = None,  
    step_index: int | None = None,  
    captured_at_utc: str | None = None,  
    extra_context: Mapping[str, Any] | None = None,  
) -> dict[str, Any]:  
    """  
    Build a minimal failure snapshot payload (JSON-serializable dict).  
  
    Parameters:  
      driver: selenium-like driver (needs current_url/title/page_source; execute_script optional)  
      step: the step dict that failed  
      error: caught exception  
      workflow_name: optional workflow identifier  
      step_index: optional index of the step in workflow  
      captured_at_utc: optional ISO timestamp override for determinism/testing  
      extra_context: optional extra key/values (kept shallow and JSON-friendly)  
  
    Returns:  
      dict suitable for writing to JSON (persistence handled elsewhere).  
    """  
    if captured_at_utc is None:  
        captured_at_utc = _utc_now_iso()  
  
    step_redacted = _redact_step(step)  
    action = step_redacted.get("action")  
  
    payload: dict[str, Any] = {  
        "schema": "SNAP-1A",  
        "captured_at_utc": captured_at_utc,  
        "context": {  
            "workflow_name": workflow_name,  
            "step_index": step_index,  
            "action": action,  
        },  
        "step": step_redacted,  
        "error": {  
            "class": error.__class__.__name__,  
            "message": str(error),  
        },  
        "browser": _capture_browser_state(driver),  
    }  
  
    if extra_context:  
        # Keep deterministic key types; do not deep-copy/mutate nested content.  
        payload["extra_context"] = {str(k): v for k, v in extra_context.items()}  
  
    return payload  
  
  
def dev_smoke() -> None:  
    class _FakeDriver:  
        current_url = "https://example.com/login"  
        title = "Login"  
        page_source = "<html><body><h1>Login</h1></body></html>"  
  
        def execute_script(self, script: str) -> str | None:  
            if script == "return document.readyState":  
                return "complete"  
            return None  
  
    driver = _FakeDriver()  
    step = {  
        "action": "type_selector_secret",  
        "selector_ref": "login.password",  
        "secret_ref": "PASSWORD_MAIN",  
        # if a generator accidentally put plaintext, it must be redacted in snapshot:  
        "text": "SHOULD_NOT_LEAK",  
    }  
  
    err = RuntimeError("Forced failure for snapshot capture test")  
    snap = capture_failure_snapshot(  
        driver=driver,  
        step=step,  
        error=err,  
        workflow_name="smoke_workflow",  
        step_index=3,  
        captured_at_utc="2026-01-01T00:00:00+00:00",  
        extra_context={"run_id": "RUN123"},  
    )  
  
    # Minimal assertions  
    assert snap["schema"] == "SNAP-1A"  
    assert snap["captured_at_utc"] == "2026-01-01T00:00:00+00:00"  
    assert snap["context"]["workflow_name"] == "smoke_workflow"  
    assert snap["context"]["step_index"] == 3  
    assert snap["context"]["action"] == "type_selector_secret"  
  
    assert snap["browser"]["url"] == "https://example.com/login"  
    assert "<h1>Login</h1>" in (snap["browser"]["dom_html"] or "")  
    assert snap["browser"]["ready_state"] == "complete"  
  
    assert snap["error"]["class"] == "RuntimeError"  
    assert "Forced failure" in snap["error"]["message"]  
  
    # Redaction check  
    assert snap["step"]["text"] == "<redacted>"  
    assert snap["step"]["secret_ref"] == "PASSWORD_MAIN"  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: SNAP.snap_1a_failure_capture")  