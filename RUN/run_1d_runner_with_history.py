# RUN/run_1d_runner_with_history.py  
"""  
RUN-1D — Wrapper to append HISTORY-1A records after running RUN-1A / REPORT-1A.  
  
- Additive only (no RUN-1A refactors)  
- Best-effort: if run fails (exception), still attempts to append a failure record.  
- If DIFF fingerprint (overall_hash) is provided or computable, include it.  
"""  
  
from __future__ import annotations  
  
from pathlib import Path  
from typing import Any, Callable, Optional  
  
from HISTORY.history_1a_store import append_run_history  
  
__all__ = [  
    "run_workflow_with_history",  
]  
  
  
def _import_run_workflow() -> Callable[..., Any]:  
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
  
  
def _best_effort_report(run_id: str, artifacts_dir: str | Path, reports_dir: str | Path) -> Optional[dict]:  
    try:  
        mod = __import__("REPORT.report_1a_generate", fromlist=["generate_report"])  
        gen = getattr(mod, "generate_report", None)  
        if callable(gen):  
            return gen(run_id, artifacts_dir=artifacts_dir, reports_dir=reports_dir, include_json=True, include_md=False, include_html=False)  
    except Exception:  
        return None  
    return None  
  
  
def run_workflow_with_history(  
    *args,  
    cfg: dict | None = None,  
    history_path: str | Path = "history/run_history.jsonl",  
    artifacts_dir: str | Path = "artifacts",  
    reports_dir: str | Path = "reports",  
    fingerprint: dict | None = None,  
    **kwargs,  
) -> Any:  
    """  
    Calls RUN-1A run_workflow then appends a sanitized history record.  
  
    - `fingerprint` (optional): DIFF-1A fingerprint dict. If provided, uses fingerprint["overall_hash"].  
    - If run_id is not known, tries to infer from result dict.  
    """  
    run_workflow = _import_run_workflow()  
    cfg_in = cfg if isinstance(cfg, dict) else (kwargs.get("cfg") if isinstance(kwargs.get("cfg"), dict) else {})  
    overall_hash = None  
    if isinstance(fingerprint, dict):  
        overall_hash = fingerprint.get("overall_hash")  
    if overall_hash is None and isinstance(cfg_in, dict):  
        overall_hash = cfg_in.get("overall_hash")  
  
    run_id_hint = cfg_in.get("run_id") or kwargs.get("run_id")  
  
    try:  
        result = run_workflow(*args, cfg=cfg_in, **kwargs)  
        rid = run_id_hint  
        if isinstance(result, dict) and result.get("run_id"):  
            rid = result.get("run_id")  
  
        report_res = None  
        if isinstance(rid, str) and rid.strip():  
            report_res = _best_effort_report(rid.strip(), artifacts_dir=artifacts_dir, reports_dir=reports_dir)  
  
        rec = {  
            "ts_utc": None,  
            "run_id": rid,  
            "workflow": (result.get("workflow") if isinstance(result, dict) else None) or kwargs.get("workflow") or kwargs.get("workflow_path"),  
            "success": (result.get("success") if isinstance(result, dict) else True),  
            "duration_ms": (result.get("duration_ms") if isinstance(result, dict) else None),  
            "failure_category": (result.get("failure_category") if isinstance(result, dict) else None),  
            "artifacts_dir": str(artifacts_dir),  
            "report_dir": (report_res.get("reports_dir") if isinstance(report_res, dict) else str(Path(reports_dir) / str(rid))) if rid else str(reports_dir),  
            "patch_path": None,  
            "overall_hash": overall_hash,  
            "notes": (result.get("notes") if isinstance(result, dict) else []),  
        }  
        append_run_history(rec, history_path=history_path)  
        return result  
    except Exception as e:  
        rid = run_id_hint  
        # Attempt report generation only if we have a run_id and artifacts exist  
        if isinstance(rid, str) and rid.strip():  
            _best_effort_report(rid.strip(), artifacts_dir=artifacts_dir, reports_dir=reports_dir)  
  
        rec = {  
            "run_id": rid,  
            "workflow": kwargs.get("workflow") or kwargs.get("workflow_path"),  
            "success": False,  
            "failure_category": type(e).__name__,  
            "artifacts_dir": str(artifacts_dir),  
            "report_dir": str(Path(reports_dir) / str(rid)) if rid else str(reports_dir),  
            "overall_hash": overall_hash,  
            "notes": [str(e)],  
        }  
        append_run_history(rec, history_path=history_path)  
        raise  