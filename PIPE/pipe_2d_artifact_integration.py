"""  
PIPE-2D — Artifact + Manifest Integration.  
  
Automatically normalize and record downloaded artifacts during pipeline execution.  
  
Must use:  
- OUT-1A (best-effort validation hook if available; consumes its output Path)  
- OUT-1B (normalize_download)  
- STATE-1D (row_success/row_failure + write_row)  
- LOG-1A (structured event emission, best-effort resolved)  
  
No refactors required; additive helper only.  
"""  
  
from __future__ import annotations  
  
import importlib  
import pkgutil  
from pathlib import Path  
from typing import Any, Callable, Dict, Optional, Tuple  
  
from LOG.log_1b_error_taxonomy import classify_exception  
from OUT.out_1b_artifact_manager import normalize_download  
from STATE.state_1d_manifest_row_helpers import row_failure, row_success, write_row  
  
__all__ = ["handle_download_artifact"]  
  
  
def _resolve_log_emitter() -> Optional[Callable[..., Any]]:  
    candidates: Tuple[Tuple[str, Tuple[str, ...]], ...] = (  
        ("LOG.log_1a_structured_logger", ("log_event", "emit_event", "write_event")),  
        ("LOG.log_1a_event_logger", ("log_event", "emit_event", "write_event")),  
        ("LOG.log_1a_logger", ("log_event", "emit_event", "write_event")),  
        ("LOG.log_1a", ("log_event", "emit_event", "write_event")),  
    )  
    for mod_name, fn_names in candidates:  
        try:  
            m = importlib.import_module(mod_name)  
        except Exception:  
            continue  
        for fn in fn_names:  
            f = getattr(m, fn, None)  
            if callable(f):  
                return f  
  
    try:  
        pkg = importlib.import_module("LOG")  
        if hasattr(pkg, "__path__"):  
            for mi in pkgutil.iter_modules(pkg.__path__, prefix=pkg.__name__ + "."):  
                try:  
                    m = importlib.import_module(mi.name)  
                except Exception:  
                    continue  
                for fn in ("log_event", "emit_event", "write_event"):  
                    f = getattr(m, fn, None)  
                    if callable(f):  
                        return f  
    except Exception:  
        pass  
  
    return None  
  
  
_LOG_EMITTER = _resolve_log_emitter()  
  
  
def _emit_log(event: Dict[str, Any]) -> None:  
    if _LOG_EMITTER is None:  
        print(f"LOG_EVENT: {event}")  
        return  
    try:  
        try:  
            _LOG_EMITTER(event=event)  
        except TypeError:  
            try:  
                _LOG_EMITTER(event)  
            except TypeError:  
                _LOG_EMITTER(**event)  
    except Exception:  
        print(f"LOG_EVENT_FALLBACK: {event}")  
  
  
def _resolve_out_1a_validator() -> Optional[Callable[..., Any]]:  
    """  
    Best-effort hook into OUT-1A for download readiness/validation if it exists.  
    This keeps PIPE-2D consuming OUT-1A output without duplicating its logic.  
    """  
    candidates: Tuple[Tuple[str, Tuple[str, ...]], ...] = (  
        ("OUT.out_1a_download_watch", ("validate_download", "assert_download_ready", "ensure_download_ready")),  
        ("OUT.out_1a_download_detector", ("validate_download", "assert_download_ready", "ensure_download_ready")),  
        ("OUT.out_1a", ("validate_download", "assert_download_ready", "ensure_download_ready")),  
    )  
    for mod_name, fn_names in candidates:  
        try:  
            m = importlib.import_module(mod_name)  
        except Exception:  
            continue  
        for fn in fn_names:  
            f = getattr(m, fn, None)  
            if callable(f):  
                return f  
    return None  
  
  
_OUT_1A_VALIDATE = _resolve_out_1a_validator()  
  
  
def _cfg_str(cfg: Dict[str, Any], *keys: str, default: Optional[str] = None) -> Optional[str]:  
    for k in keys:  
        v = cfg.get(k)  
        if v is not None and str(v).strip():  
            return str(v)  
    return default  
  
  
def _resolve_out_dir(cfg: Dict[str, Any]) -> Path:  
    p = _cfg_str(cfg, "ARTIFACT_OUT_DIR", "OUT_DIR", "OUTPUT_DIR", default="./out")  
    return Path(p)  
  
  
def handle_download_artifact(  
    *,  
    download_path: Any,  
    cfg: Dict[str, Any],  
    run_id: Optional[str] = None,  
    item_id: Optional[str] = None,  
    writer: Any = None,  
) -> Dict[str, Any]:  
    """  
    Normalize a downloaded artifact (detected by OUT-1A) and record it.  
  
    Responsibilities:  
    1) Normalize artifact using OUT-1B normalize_download  
    2) Determine output directory from cfg  
    3) Write success row via STATE-1D row_success including artifact path  
    4) Emit structured log event via LOG-1A  
    5) Return:  
       {"ok": True, "artifact_path": "<path>", "normalized_name": "<file>"}  
  
    On failure:  
    - classify error via LOG-1B  
    - write manifest fail row (if writer provided)  
    - emit log event  
    - return ok=False + error  
    """  
    dl = Path(download_path) if not isinstance(download_path, Path) else download_path  
    rid = run_id if run_id is not None else _cfg_str(cfg, "RUN_ID", "run_id", default=None)  
    iid = item_id if item_id is not None else _cfg_str(cfg, "ITEM_ID", "item_id", default=None)  
  
    out_dir = _resolve_out_dir(cfg)  
    archive_dir_s = _cfg_str(cfg, "ARTIFACT_ARCHIVE_DIR", "ARCHIVE_DIR", default=None)  
    archive_dir = Path(archive_dir_s) if archive_dir_s else None  
  
    overwrite = bool(cfg.get("ARTIFACT_OVERWRITE", False))  
    base_name = _cfg_str(cfg, "ARTIFACT_BASE_NAME", default=dl.stem) or dl.stem  
  
    try:  
        # Optional OUT-1A readiness validation if the project provides it.  
        if callable(_OUT_1A_VALIDATE):  
            try:  
                _OUT_1A_VALIDATE(dl, cfg=cfg)  
            except TypeError:  
                _OUT_1A_VALIDATE(dl)  
  
        final_path = normalize_download(  
            dl,  
            out_dir=out_dir,  
            run_id=rid,  
            item_id=iid,  
            base_name=base_name,  
            overwrite=overwrite,  
            archive_dir=archive_dir,  
        )  
  
        result = {  
            "ok": True,  
            "artifact_path": str(final_path),  
            "normalized_name": final_path.name,  
        }  
  
        if writer is not None:  
            write_row(  
                writer,  
                row_success(  
                    run_id=rid,  
                    item_id=iid,  
                    step="artifact",  
                    details={  
                        "artifact_path": str(final_path),  
                        "normalized_name": final_path.name,  
                    },  
                ),  
            )  
  
        _emit_log(  
            {  
                "event": "artifact_normalized",  
                "run_id": rid,  
                "item_id": iid,  
                "artifact_path": str(final_path),  
                "normalized_name": final_path.name,  
            }  
        )  
  
        return result  
  
    except Exception as exc:  
        err = classify_exception(exc if isinstance(exc, Exception) else Exception(str(exc)))  
  
        if writer is not None:  
            write_row(  
                writer,  
                row_failure(  
                    run_id=rid,  
                    item_id=iid,  
                    step="artifact",  
                    error=err,  
                    details={"download_path": str(dl)},  
                ),  
            )  
  
        _emit_log(  
            {  
                "event": "artifact_error",  
                "run_id": rid,  
                "item_id": iid,  
                "download_path": str(dl),  
                "error_code": err.get("code"),  
                "error_type": err.get("type"),  
                "error_message": err.get("message"),  
            }  
        )  
  
        return {"ok": False, "error": err}  