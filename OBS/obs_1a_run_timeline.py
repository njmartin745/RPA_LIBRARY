# OBS/obs_1a_run_timeline.py  
"""  
OBS-1A — Run Observability Timeline  
  
Provides a structured execution timeline for workflow runs that can be consumed by humans,  
logs, or AI agents.  
  
Public API:  
- create_run_timeline(run_id: str, workflow_name: str) -> dict  
- record_step_event(timeline: dict, step_index: int, action: str, status: str, *,  
    selector: str|None=None, url: str|None=None, duration_ms: int|None=None, metadata: dict|None=None) -> None  
- finalize_timeline(timeline: dict) -> dict  
"""  
  
from __future__ import annotations  
  
import time  
from datetime import datetime, timezone  
from typing import Any, Dict, Optional  
  
__all__ = [  
    "create_run_timeline",  
    "record_step_event",  
    "finalize_timeline",  
]  
  
  
def _utc_now_iso() -> str:  
    return datetime.now(timezone.utc).isoformat()  
  
  
def create_run_timeline(run_id: str, workflow_name: str) -> dict:  
    if not isinstance(run_id, str) or not run_id.strip():  
        raise ValueError("run_id must be a non-empty string")  
    if not isinstance(workflow_name, str) or not workflow_name.strip():  
        raise ValueError("workflow_name must be a non-empty string")  
  
    return {  
        "run_id": run_id,  
        "workflow_name": workflow_name,  
        "start_time": _utc_now_iso(),  
        "steps": [],  
        # internal timing anchor (still JSON-serializable)  
        "_start_perf": time.perf_counter(),  
        "summary": None,  
    }  
  
  
def record_step_event(  
    timeline: dict,  
    step_index: int,  
    action: str,  
    status: str,  
    *,  
    selector: Optional[str] = None,  
    url: Optional[str] = None,  
    duration_ms: Optional[int] = None,  
    metadata: Optional[dict] = None,  
) -> None:  
    if not isinstance(timeline, dict):  
        raise ValueError("timeline must be a dict created by create_run_timeline()")  
    if "steps" not in timeline or not isinstance(timeline["steps"], list):  
        raise ValueError("timeline['steps'] must be a list")  
    if not isinstance(step_index, int) or step_index < 0:  
        raise ValueError("step_index must be a non-negative int")  
    if not isinstance(action, str) or not action.strip():  
        raise ValueError("action must be a non-empty string")  
    if not isinstance(status, str) or not status.strip():  
        raise ValueError("status must be a non-empty string")  
    if selector is not None and not isinstance(selector, str):  
        raise ValueError("selector must be str|None")  
    if url is not None and not isinstance(url, str):  
        raise ValueError("url must be str|None")  
    if duration_ms is not None and (not isinstance(duration_ms, int) or duration_ms < 0):  
        raise ValueError("duration_ms must be a non-negative int or None")  
    if metadata is not None and not isinstance(metadata, dict):  
        raise ValueError("metadata must be dict|None")  
  
    rec: Dict[str, Any] = {  
        "ts": _utc_now_iso(),  
        "step_index": step_index,  
        "action": action,  
        "status": status,  
    }  
    if selector:  
        rec["selector"] = selector  
    if url:  
        rec["url"] = url  
    if duration_ms is not None:  
        rec["duration_ms"] = duration_ms  
    if metadata:  
        rec["metadata"] = metadata  
  
    timeline["steps"].append(rec)  
  
  
def finalize_timeline(timeline: dict) -> dict:  
    if not isinstance(timeline, dict):  
        raise ValueError("timeline must be a dict created by create_run_timeline()")  
    steps = timeline.get("steps")  
    if not isinstance(steps, list):  
        raise ValueError("timeline['steps'] must be a list")  
  
    end_time = _utc_now_iso()  
    start_perf = timeline.get("_start_perf")  
    if isinstance(start_perf, (int, float)):  
        duration_seconds = max(0.0, time.perf_counter() - float(start_perf))  
    else:  
        duration_seconds = 0.0  
  
    steps_total = len(steps)  
  
    ok_statuses = {"ok", "success", "passed", "pass"}  
    fail_statuses = {"failed", "fail", "error", "exception"}  
  
    steps_ok = 0  
    steps_failed = 0  
    for s in steps:  
        if not isinstance(s, dict):  
            continue  
        st = s.get("status")  
        if isinstance(st, str):  
            st_norm = st.strip().lower()  
            if st_norm in ok_statuses:  
                steps_ok += 1  
            elif st_norm in fail_statuses:  
                steps_failed += 1  
  
    summary = {  
        "steps_total": steps_total,  
        "steps_ok": steps_ok,  
        "steps_failed": steps_failed,  
        "duration_seconds": duration_seconds,  
    }  
  
    timeline["end_time"] = end_time  
    timeline["summary"] = summary  
    return timeline  