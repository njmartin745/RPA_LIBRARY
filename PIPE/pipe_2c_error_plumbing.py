"""  
PIPE-2C — Error Plumbing Integration (LOG-1B + LOG-1A + STATE).  
  
Additive wrapper to ensure any step/item failure produces:  
- normalized error dict (LOG-1B.classify_exception)  
- structured log event (LOG-1A, best-effort resolved emitter)  
- manifest row update (STATE writer, if provided)  
  
No changes required to existing modules for this milestone.  
"""  
  
from __future__ import annotations  
  
import importlib  
import pkgutil  
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Union  
  
from LOG.log_1b_error_taxonomy import classify_exception, format_error_for_manifest  
  
__all__ = ["run_with_error_plumbing"]  
  
  
def _resolve_log_emitter() -> Optional[Callable[..., Any]]:  
    """  
    Best-effort resolver for a LOG-1A structured event emitter.  
    Tries common module/function names, then scans LOG.*.  
    """  
    candidates: List[Tuple[str, Tuple[str, ...]]] = [  
        ("LOG.log_1a_structured_logger", ("log_event", "emit_event", "write_event")),  
        ("LOG.log_1a_event_logger", ("log_event", "emit_event", "write_event")),  
        ("LOG.log_1a_logger", ("log_event", "emit_event", "write_event")),  
        ("LOG.log_1a", ("log_event", "emit_event", "write_event")),  
    ]  
    for mod_name, fn_names in candidates:  
        try:  
            m = importlib.import_module(mod_name)  
        except Exception:  
            continue  
        for fn in fn_names:  
            f = getattr(m, fn, None)  
            if callable(f):  
                return f  
  
    # Scan LOG package for a plausible emitter  
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
    """  
    Emit a structured log event using LOG-1A if available; otherwise print.  
    Never includes secrets/cookies (caller must pass safe payload).  
    """  
    if _LOG_EMITTER is None:  
        # fallback: still deterministic and visible in smoke tests  
        print(f"LOG_EVENT: {event}")  
        return  
  
    try:  
        # flexible signatures  
        try:  
            _LOG_EMITTER(event=event)  
        except TypeError:  
            try:  
                _LOG_EMITTER(event)  
            except TypeError:  
                _LOG_EMITTER(**event)  
    except Exception:  
        # never let logging crash the run  
        print(f"LOG_EVENT_FALLBACK: {event}")  
  
  
def _maybe_set_item_context(cfg: Dict[str, Any], item: Any, item_id: Optional[str]) -> None:  
    cfg["WORK_ITEM"] = item  
    if item_id is not None:  
        cfg["ITEM_ID"] = item_id  
        cfg["item_id"] = item_id  # convenience for templating and downstream code  
  
    # If VAR-1A is present, also set runtime var (best-effort; no duplication).  
    try:  
        from VAR.var_1a_runtime_store import set_var  # type: ignore  
  
        if item_id is not None:  
            set_var(cfg, "item_id", item_id)  
    except Exception:  
        pass  
  
  
def _coerce_work_items(work_items: Any) -> List[Dict[str, Any]]:  
    if work_items is None:  
        return [{"item_id": None, "item": None}]  
    if isinstance(work_items, list):  
        out: List[Dict[str, Any]] = []  
        for x in work_items:  
            if isinstance(x, str):  
                out.append({"item_id": x, "item": x})  
            elif isinstance(x, dict):  
                item_id = x.get("item_id", None)  
                if item_id is None:  
                    item_id = x.get("id", None)  
                if item_id is None:  
                    item_id = x.get("name", None)  
                out.append({"item_id": item_id, "item": x})  
            else:  
                out.append({"item_id": str(x), "item": x})  
        return out  
    # single scalar  
    return [{"item_id": str(work_items), "item": work_items}]  
  
  
def _resolve_pipeline_runner(cfg: Dict[str, Any]) -> Callable[..., Any]:  
    """  
    Prefer PIPE-1E runner if resolvable; otherwise fall back to PIPE-2B run_steps.  
    Caller may override via cfg["PIPE_RUNNER"] as a callable.  
    """  
    override = cfg.get("PIPE_RUNNER")  
    if callable(override):  
        return override  # type: ignore  
  
    candidates: List[Tuple[str, Tuple[str, ...]]] = [  
        ("PIPE.pipe_1e_pipeline_runner", ("run", "run_pipeline", "run_steps", "execute")),  
        ("PIPE.pipe_1e_runner", ("run", "run_pipeline", "run_steps", "execute")),  
        ("PIPE.pipe_1e", ("run", "run_pipeline", "run_steps", "execute")),  
    ]  
    for mod_name, fn_names in candidates:  
        try:  
            m = importlib.import_module(mod_name)  
        except Exception:  
            continue  
        for fn in fn_names:  
            f = getattr(m, fn, None)  
            if callable(f):  
                return f  # type: ignore  
  
    from PIPE.pipe_2b_step_blocks import run_steps as pipe_2b_run_steps  
  
    return pipe_2b_run_steps  
  
  
def _call_runner(runner: Callable[..., Any], driver: Any, steps: List[Dict[str, Any]], cfg: Dict[str, Any]) -> Any:  
    # flexible signatures  
    try:  
        return runner(driver=driver, steps=steps, cfg=cfg)  
    except TypeError:  
        pass  
    try:  
        return runner(driver, steps, cfg)  
    except TypeError:  
        pass  
    try:  
        return runner(driver, steps)  
    except TypeError:  
        pass  
    return runner(steps)  
  
  
def _find_first_failed_step(results: Any) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:  
    if not isinstance(results, list):  
        return None, None  
    for i, r in enumerate(results):  
        if isinstance(r, Mapping) and ("ok" in r) and not bool(r.get("ok")):  
            return i, dict(r)  
    return None, None  
  
  
def _append_manifest_failure(writer: Any, row: Dict[str, Any]) -> None:  
    """  
    Generic writer hook (STATE-1B writer or compatible).  
    """  
    if writer is None:  
        return  
  
    # common method names  
    for meth in ("append_row", "write_row", "add_row", "append", "write"):  
        fn = getattr(writer, meth, None)  
        if callable(fn):  
            try:  
                fn(row)  
                return  
            except Exception:  
                return  
  
    # callable writer(row)  
    if callable(writer):  
        try:  
            writer(row)  
        except Exception:  
            pass  
  
  
def run_with_error_plumbing(  
    *,  
    driver: Any,  
    cfg: Dict[str, Any],  
    steps: List[Dict[str, Any]],  
    work_items: Union[List[Dict[str, Any]], List[str], None],  
    writer: Any = None,  
) -> Dict[str, Any]:  
    """  
    Wrapper runner with error normalization + logging + manifest row updates.  
  
    Returns summary:  
      {  
        "ok": bool,  
        "items_total": int,  
        "items_ok": int,  
        "items_failed": int,  
        "errors_total": int,  
        "last_error": dict|None  
      }  
    """  
    stop_on_error = bool(cfg.get("STOP_ON_ERROR", False))  
    stop_on_item_error = bool(cfg.get("STOP_ON_ITEM_ERROR", False))  
  
    runner = _resolve_pipeline_runner(cfg)  
    items = _coerce_work_items(work_items)  
  
    items_ok = 0  
    items_failed = 0  
    errors_total = 0  
    last_error: Optional[Dict[str, Any]] = None  
  
    for item_idx, it in enumerate(items):  
        item_id = it.get("item_id")  
        item_obj = it.get("item")  
  
        _maybe_set_item_context(cfg, item_obj, item_id)  
  
        try:  
            results = _call_runner(runner, driver, list(steps), cfg)  
  
            # If runner returned per-step results, treat ok=false as an item failure (non-exception).  
            step_i, failed = _find_first_failed_step(results)  
            if failed is None:  
                items_ok += 1  
                continue  
  
            # Create a normalized error from a synthetic exception (safe message only).  
            msg = failed.get("error") or failed.get("message") or "Step failed"  
            action = failed.get("action")  
            exc = RuntimeError(f"Step failed action={action!r}: {msg}")  
  
            err = classify_exception(exc)  
            last_error = err  
            errors_total += 1  
            items_failed += 1  
  
            _emit_log(  
                {  
                    "event": "step_failed",  
                    "error_code": err.get("code"),  
                    "error_type": err.get("type"),  
                    "error_message": err.get("message"),  
                    "item_id": item_id,  
                    "step_index": step_i,  
                    "item_index": item_idx,  
                }  
            )  
  
            if writer is not None:  
                row = {"item_id": item_id, "status": "FAIL"}  
                row.update(format_error_for_manifest(err))  
                _append_manifest_failure(writer, row)  
  
            if stop_on_error:  
                raise RuntimeError(f"STOP_ON_ERROR: {err.get('code')}") from exc  
            if stop_on_item_error:  
                break  
  
        except Exception as exc:  
            err = classify_exception(exc if isinstance(exc, Exception) else Exception(str(exc)))  
            last_error = err  
            errors_total += 1  
            items_failed += 1  
  
            _emit_log(  
                {  
                    "event": "exception",  
                    "error_code": err.get("code"),  
                    "error_type": err.get("type"),  
                    "error_message": err.get("message"),  
                    "item_id": item_id,  
                    "step_index": None,  
                    "item_index": item_idx,  
                }  
            )  
  
            if writer is not None:  
                row = {"item_id": item_id, "status": "FAIL"}  
                row.update(format_error_for_manifest(err))  
                _append_manifest_failure(writer, row)  
  
            if stop_on_error:  
                raise  
            if stop_on_item_error:  
                break  
            # else: continue to next item  
  
    summary = {  
        "ok": (errors_total == 0),  
        "items_total": len(items),  
        "items_ok": items_ok,  
        "items_failed": items_failed,  
        "errors_total": errors_total,  
        "last_error": last_error,  
    }  
    return summary  