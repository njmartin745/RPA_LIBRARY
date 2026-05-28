# SNAP/snap_1a_capture.py  
"""  
SNAP-1A — Evidence Capture on Failure (artifacts bundle)  
  
Selenium-safe utility:  
- May accept a driver, but must not create a driver.  
- Resilient: never raises due to artifact capture failures.  
- Writes compact evidence bundle to artifacts/<run_id>/.  
  
Public API:  
  capture_failure_artifacts(...)  
"""  
  
from __future__ import annotations  
  
import json  
import traceback as _traceback  
from datetime import datetime, timezone  
from pathlib import Path  
from typing import Any, Dict, Optional  
  
__all__ = [  
    "capture_failure_artifacts",  
]  
  
  
def _utc_now_iso() -> str:  
    return datetime.now(timezone.utc).isoformat()  
  
  
def _safe_write_text(path: Path, content: str, errors: list) -> None:  
    try:  
        path.parent.mkdir(parents=True, exist_ok=True)  
        path.write_text(content, encoding="utf-8", errors="replace")  
    except Exception as e:  
        errors.append(f"write_text_failed:{path.name}:{type(e).__name__}:{e}")  
  
  
def _safe_write_json(path: Path, obj: Any, errors: list) -> None:  
    try:  
        path.parent.mkdir(parents=True, exist_ok=True)  
        path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")  
    except Exception as e:  
        errors.append(f"write_json_failed:{path.name}:{type(e).__name__}:{e}")  
  
  
def capture_failure_artifacts(  
    *,  
    run_id: str,  
    output_dir: str | Path = "artifacts",  
    driver=None,  
    workflow_name: str | None = None,  
    step_index: int | None = None,  
    action: str | None = None,  
    error_type: str | None = None,  
    error_message: str | None = None,  
    traceback_text: str | None = None,  
    extra: dict | None = None,  
) -> dict:  
    """  
    Creates artifacts/<run_id>/ with:  
      - failure.json (always)  
      - traceback.txt (if traceback_text provided)  
      - screenshot.png, page.html, page.json (best-effort if driver provided)  
  
    Never raises due to capture failures; errors recorded in failure.json under "capture_errors".  
    """  
    capture_errors: list[str] = []  
    created_paths: Dict[str, str] = {}  
  
    # Validate run_id (best-effort; do not raise on minor issues)  
    rid = (run_id or "").strip()  
    if not rid:  
        rid = "unknown-run-id"  
        capture_errors.append("invalid_run_id:empty")  
  
    base_dir = Path(output_dir) / rid  
    try:  
        base_dir.mkdir(parents=True, exist_ok=True)  
    except Exception as e:  
        capture_errors.append(f"mkdir_failed:{type(e).__name__}:{e}")  
        # Best-effort fallback: use output_dir directly  
        base_dir = Path(output_dir)  
        try:  
            base_dir.mkdir(parents=True, exist_ok=True)  
        except Exception as e2:  
            capture_errors.append(f"mkdir_fallback_failed:{type(e2).__name__}:{e2}")  
  
    # Optional traceback file  
    if isinstance(traceback_text, str) and traceback_text.strip():  
        tb_path = base_dir / "traceback.txt"  
        _safe_write_text(tb_path, traceback_text, capture_errors)  
        if tb_path.exists():  
            created_paths["traceback_txt"] = str(tb_path)  
  
    # Driver-based artifacts (best-effort)  
    driver_unavailable = driver is None  
    if driver is not None:  
        # Screenshot  
        ss_path = base_dir / "screenshot.png"  
        try:  
            ok = False  
            fn = getattr(driver, "get_screenshot_as_file", None)  
            if callable(fn):  
                ok = bool(fn(str(ss_path)))  
            if ok and ss_path.exists():  
                created_paths["screenshot_png"] = str(ss_path)  
            else:  
                # If method exists but returned False or file missing  
                if callable(fn):  
                    capture_errors.append("screenshot_failed:returned_false_or_missing_file")  
        except Exception as e:  
            capture_errors.append(f"screenshot_failed:{type(e).__name__}:{e}")  
  
        # Page source  
        html_path = base_dir / "page.html"  
        try:  
            src = getattr(driver, "page_source", None)  
            if isinstance(src, str):  
                _safe_write_text(html_path, src, capture_errors)  
                if html_path.exists():  
                    created_paths["page_html"] = str(html_path)  
            else:  
                capture_errors.append("page_source_unavailable")  
        except Exception as e:  
            capture_errors.append(f"page_source_failed:{type(e).__name__}:{e}")  
  
        # Page info  
        page_json_path = base_dir / "page.json"  
        page_info: Dict[str, Any] = {}  
        try:  
            cur_url = getattr(driver, "current_url", None)  
            if isinstance(cur_url, str):  
                page_info["url"] = cur_url  
        except Exception as e:  
            capture_errors.append(f"current_url_failed:{type(e).__name__}:{e}")  
        try:  
            title = getattr(driver, "title", None)  
            if isinstance(title, str):  
                page_info["title"] = title  
        except Exception as e:  
            capture_errors.append(f"title_failed:{type(e).__name__}:{e}")  
  
        if page_info:  
            _safe_write_json(page_json_path, page_info, capture_errors)  
            if page_json_path.exists():  
                created_paths["page_json"] = str(page_json_path)  
  
    # Always write failure.json (best-effort)  
    failure_json_path = base_dir / "failure.json"  
    failure_obj: Dict[str, Any] = {  
        "run_id": rid,  
        "workflow_name": workflow_name,  
        "step_index": step_index,  
        "action": action,  
        "error_type": error_type,  
        "error_message": error_message,  
        "timestamp_utc": _utc_now_iso(),  
        "driver_unavailable": bool(driver_unavailable),  
        "paths": created_paths,  
        "capture_errors": capture_errors,  
    }  
    if isinstance(extra, dict) and extra:  
        # Do not attempt to sanitize; caller must avoid secrets.  
        failure_obj["extra"] = extra  
  
    _safe_write_json(failure_json_path, failure_obj, capture_errors)  
    if failure_json_path.exists():  
        created_paths["failure_json"] = str(failure_json_path)  
        # Re-write once more so failure.json includes its own path and any late capture_errors  
        failure_obj["paths"] = created_paths  
        failure_obj["capture_errors"] = capture_errors  
        _safe_write_json(failure_json_path, failure_obj, capture_errors)  
  
    return {  
        "run_id": rid,  
        "base_dir": str(base_dir),  
        "paths": created_paths,  
        "driver_unavailable": bool(driver_unavailable),  
        "capture_errors": capture_errors,  
    }  