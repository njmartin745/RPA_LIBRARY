"""
RUN-1B — Workflow Runner With Snapshot Capture

Purpose
-------
Wrap the canonical RUN-1A workflow runner and automatically
capture SNAP-1A failure artifacts whenever execution fails.

This module is additive only and does not modify
RUN-1A execution behavior.

Public API
----------
run_workflow_with_snap(...)

Dependencies
------------
RUN-1A
SNAP-1A

Status
------
Draft

Notes
-----
On workflow failure:
RUN-1A
    ↓
Capture SNAP-1A artifacts
    ↓
Re-raise original exception

Used for diagnostics, replay, healing, and audit workflows.
"""
  
from __future__ import annotations  
  
import traceback  
from typing import Any, Callable, Optional  
  
from SNAP.snap_1a_capture import capture_failure_artifacts  
  
__all__ = [  
    "run_workflow_with_snap",  
]  
  
  
def _import_run_workflow() -> Callable[..., Any]:  
    # Best-effort import of the canonical RUN-1A runner function.  
    candidates = [  
        ("RUN.run_1a_workflow_runner", "run_workflow"),  
        ("RUN.run_1a_run_workflow", "run_workflow"),  
        ("RUN.run_1a_runner", "run_workflow"),  
        ("RUN.run_1a", "run_workflow"),  
    ]  
    last_err: Optional[Exception] = None  
    for mod_name, fn_name in candidates:  
        try:  
            mod = __import__(mod_name, fromlist=[fn_name])  
            fn = getattr(mod, fn_name, None)  
            if callable(fn):  
                return fn  
        except Exception as e:  
            last_err = e  
    raise ValueError(f"Could not import RUN-1A run_workflow. Last error: {last_err}")  
  
  
def run_workflow_with_snap(  
    *args,  
    run_id: str,  
    output_dir: str = "artifacts",  
    workflow_name: str | None = None,  
    step_index: int | None = None,  
    action: str | None = None,  
    driver=None,  
    **kwargs,  
) -> Any:  
    """  
    Calls RUN-1A run_workflow. On exception, captures SNAP-1A artifacts then re-raises.  
  
    Notes:  
    - If your RUN-1A runner creates the driver internally, you may want to pass it in (driver=...)  
      or pass a state dict that includes it; this wrapper will try to discover it.  
    """  
    run_workflow = _import_run_workflow()  
  
    try:  
        return run_workflow(*args, **kwargs)  
    except Exception as e:  
        # Best-effort driver discovery  
        drv = driver  
        if drv is None:  
            st = kwargs.get("state")  
            if isinstance(st, dict):  
                drv = st.get("driver")  
  
        capture_failure_artifacts(  
            run_id=run_id,  
            output_dir=output_dir,  
            driver=drv,  
            workflow_name=workflow_name,  
            step_index=step_index,  
            action=action,  
            error_type=type(e).__name__,  
            error_message=str(e),  
            traceback_text=traceback.format_exc(),  
            extra={"wrapper": "RUN-1B", "note": "Captured by run_workflow_with_snap()"},  
        )  
        raise  