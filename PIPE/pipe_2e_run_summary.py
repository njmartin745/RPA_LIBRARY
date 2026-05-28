"""  
PIPE-2E — Run Summary + Metrics.  
  
Standardized, additive run summary object to describe an automation run.  
No integration into existing runners yet; this module is meant to be attached later.  
  
Summary shape  
-------------  
{  
  "run_id": "...",  
  "start_time": "...",  
  "items_total": 0,  
  "items_success": 0,  
  "items_failed": 0,  
  "artifacts": [],  
  "errors": []  
}  
  
finish_run_summary adds:  
- end_time  
- duration_seconds  
"""  
  
from __future__ import annotations  
  
import time  
from datetime import datetime, timezone  
from typing import Any, Dict, Optional  
  
__all__ = [  
    "start_run_summary",  
    "record_item_success",  
    "record_item_failure",  
    "record_artifact",  
    "finish_run_summary",  
]  
  
  
def _now_utc_ts() -> str:  
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")  
  
  
def start_run_summary(run_id: Optional[str] = None) -> Dict[str, Any]:  
    """  
    Initialize a run summary dict.  
    """  
    return {  
        "run_id": str(run_id) if run_id is not None else None,  
        "start_time": _now_utc_ts(),  
        "_start_monotonic": time.monotonic(),  # internal; removed on finish  
        "items_total": 0,  
        "items_success": 0,  
        "items_failed": 0,  
        "artifacts": [],  
        "errors": [],  
    }  
  
  
def record_item_success(summary: Dict[str, Any], item_id: Optional[str] = None) -> None:  
    if not isinstance(summary, dict):  
        raise TypeError("summary must be a dict")  
    summary["items_total"] = int(summary.get("items_total", 0)) + 1  
    summary["items_success"] = int(summary.get("items_success", 0)) + 1  
    if item_id is not None:  
        summary.setdefault("items", [])  
        summary["items"].append({"item_id": str(item_id), "status": "success"})  
  
  
def record_item_failure(summary: Dict[str, Any], item_id: Optional[str] = None, error: Any = None) -> None:  
    if not isinstance(summary, dict):  
        raise TypeError("summary must be a dict")  
    summary["items_total"] = int(summary.get("items_total", 0)) + 1  
    summary["items_failed"] = int(summary.get("items_failed", 0)) + 1  
  
    entry: Dict[str, Any] = {"item_id": str(item_id) if item_id is not None else None, "status": "fail"}  
    if isinstance(error, dict):  
        # store as-is (expected to already be normalized/safe); no secret processing here  
        entry["error"] = error  
        summary["errors"].append(error)  
    elif error is not None:  
        entry["error"] = {"type": error.__class__.__name__, "message": str(error)}  
        summary["errors"].append(entry["error"])  
  
    summary.setdefault("items", [])  
    summary["items"].append(entry)  
  
  
def record_artifact(summary: Dict[str, Any], artifact_path: str) -> None:  
    if not isinstance(summary, dict):  
        raise TypeError("summary must be a dict")  
    summary["artifacts"].append(str(artifact_path))  
  
  
def finish_run_summary(summary: dict) -> dict:  
    if not isinstance(summary, dict):  
        raise TypeError("summary must be a dict")  
  
    # Add end_time / duration_seconds (idempotent if already present)  
    if summary.get("end_time") is None:  
        summary["end_time"] = _now_utc_ts()  
  
    start_mono = summary.get("_start_monotonic", None)  
    if "duration_seconds" not in summary or summary.get("duration_seconds") is None:  
        if isinstance(start_mono, (int, float)):  
            dur = time.monotonic() - float(start_mono)  
            summary["duration_seconds"] = dur if dur >= 0 else 0.0  
        else:  
            summary["duration_seconds"] = None  
  
    # internal; removed on finish  
    summary.pop("_start_monotonic", None)  
  
    # keep existing end_time/duration/run_id logic as-is above this point  
  
    errors = summary.get("errors", [])  
    if errors is None:  
        errors = []  
    if not isinstance(errors, list):  
        # defensive: preserve structure but ensure len() is meaningful  
        errors = [errors]  
  
    summary["errors"] = errors  
  
    # REQUIRED: success MUST reflect error presence  
    summary["success"] = (len(errors) == 0)  
  
    # Optional compatibility alias (common in other parts of the codebase)  
    summary["ok"] = summary["success"]  
  
    return summary  