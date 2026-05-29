# PIPE/pipe_1a_run_orchestrator.py  
"""  
PIPE-1A — End-to-end per-run orchestrator (glue module)  
  
Purpose  
-------  
Run an end-to-end Selenium workflow by composing the already-validated modules:  
  
- INPUT-1B: read worklist IDs (source defined by cfg)  
- LOG-1A: initialize structured logging; bind run context (RUN_ID)  
- ENTRY-1A: create Selenium WebDriver  
- LOOP-1B: per-item iteration; inject CURRENT_ID / ITEM_INDEX / TOTAL_ITEMS into cfg  
- ACT-1B: execute steps with automatic step_start/step_success/step_error logs  
- STATE-1B: append per-item outcome to manifest (success/fail + error summary)  
- Always quit the WebDriver  
  
Inputs  
------  
- cfg: MutableMapping[str, Any]  
- steps: list[dict] (already loaded by the caller; e.g., from steps.json)  
  
Outputs  
-------  
Returns a simple summary dict:  
{  
  "run_id": str,  
  "total_items": int,  
  "success": int,  
  "failed": int,  
  "items": [{"item_id": str, "ok": bool, "error": str|None}],  
}  
  
Notes  
-----  
- STOP/CONTINUE behavior for step execution is controlled by cfg["STOP_ON_ERROR"]  
  via ACT-1B (default True). PIPE-1A continues to the next item even if one item  
  fails (it records the failure), unless a non-recoverable exception occurs.  
  
Minimal usage example  
---------------------  
from PIPE.pipe_1a_run_orchestrator import run_worklist  
cfg = {...}  # includes INPUT-1B config and LOG-1A/ENTRY-1A config  
steps = [{"action":"get","url":"https://example.com"}]  
summary = run_worklist(cfg, steps)  
print(summary)  

Status
------
Audited

Architecture Position
---------------------
RUN-1A
    ↓
PIPE-1E
    ↓
PIPE-1A
    ↓
INPUT / LOOP / ENTRY / ACT / STATE / LOG

Notes
-----
Primary orchestration layer responsible for
coordinating worklist execution and item-level
processing.
"""  
  
from __future__ import annotations  
  
import importlib  
from typing import Any, Callable, Iterable, MutableMapping, Optional
  
from ENTRY.entry_1a_webdriver_bootstrap import make_driver  
from ACT.act_1b_logging_integration import run_actions_logged  
from LOG.log_1a_structured_logging import setup_logging, bind_context, log_event, log_exception  
  
import INPUT.input_1b_excel_provider as input_1b  
import LOOP.loop_1b_per_item as loop_1b  
import STATE.state_1b_manifest_jsonl as state_1b  
  
__all__ = [  
    "run_worklist",  
    "manifest_append",  
    "ManifestWriter",  
    "open_manifest",  
    "dev_smoke",  
]  
  
# Re-export STATE-1B conveniences (keeps existing __all__ names valid)  
manifest_append = getattr(state_1b, "append_manifest", None)  
ManifestWriter = getattr(state_1b, "ManifestWriter", None)  
open_manifest = getattr(state_1b, "open_manifest", None)  
  
  
# -------------------------  
# INPUT-1B adapter (introspection; avoids redefining INPUT-1B)  
# -------------------------  
def _load_worklist_ids(cfg: MutableMapping[str, Any]) -> list[str]:  
    candidates = (  
        "get_worklist_ids",  
        "read_worklist_ids",  
        "load_worklist_ids",  
        "iter_worklist_ids",  
        "get_ids",  
        "read_ids",  
        "ids",  
    )  
    for name in candidates:  
        fn = getattr(input_1b, name, None)  
        if callable(fn):  
            ids = fn(cfg)  
            if ids is None:  
                raise RuntimeError(f"INPUT-1B {name} returned None")  
            return [str(x) for x in list(ids)]  
  
    raise RuntimeError(  
        "INPUT-1B API not found. Expected one of: "  
        + ", ".join(candidates)  
        + " in INPUT/input_1b_excel_provider.py"  
    )  
  
  
# -------------------------  
# LOOP-1B adapter  
# -------------------------  
def _iterate_items(cfg: MutableMapping[str, Any], ids: list[str]) -> Iterable[str]:  
    candidates = (  
        "iter_items",  
        "iterate_items",  
        "iter_worklist",  
        "loop_items",  
        "items",  
    )  
    for name in candidates:  
        fn = getattr(loop_1b, name, None)  
        if callable(fn):  
            try:  
                return fn(cfg, ids)  
            except TypeError:  
                return fn(ids, cfg)  
  
    raise RuntimeError(  
        "LOOP-1B API not found. Expected one of: "  
        + ", ".join(candidates)  
        + " in LOOP/loop_1b_per_item.py"  
    )  
  
  
# -------------------------  
# STATE-1B adapter  
# -------------------------  
class _StateSink:  
    def __init__(  
        self,  
        writer: Any = None,  
        append_fn: Optional[Callable[[MutableMapping[str, Any], dict[str, Any]], None]] = None,  
    ) -> None:  
        self.writer = writer  
        self.append_fn = append_fn  
  
    def append(self, cfg: MutableMapping[str, Any], record: dict[str, Any]) -> None:  
        if self.append_fn is not None:  
            self.append_fn(cfg, record)  
            return  
  
        w = self.writer  
        if w is None:  
            raise RuntimeError("STATE-1B sink not initialized")  
  
        for meth in ("append", "write", "record", "record_item", "write_record", "add"):  
            fn = getattr(w, meth, None)  
            if callable(fn):  
                fn(record)  
                return  
  
        raise RuntimeError("STATE-1B writer does not support append/write/record methods")  
  
    def close(self) -> None:  
        w = self.writer  
        if w is None:  
            return  
        fn = getattr(w, "close", None)  
        if callable(fn):  
            try:  
                fn()  
            except Exception:  
                pass  
  
  
def _open_state_sink(cfg: MutableMapping[str, Any]) -> _StateSink:  
    fn_candidates = (  
        "append_manifest",  
        "append_manifest_record",  
        "write_manifest_record",  
        "record_item_outcome",  
        "record_outcome",  
    )  
    for name in fn_candidates:  
        fn = getattr(state_1b, name, None)  
        if callable(fn):  
            return _StateSink(writer=None, append_fn=fn)  
  
    if callable(getattr(state_1b, "open_manifest", None)):  
        return _StateSink(writer=state_1b.open_manifest(cfg))  
  
    cls = getattr(state_1b, "ManifestWriter", None)  
    if cls is not None:  
        try:  
            return _StateSink(writer=cls(cfg))  
        except TypeError:  
            pass  
  
    raise RuntimeError(  
        "STATE-1B API not found. Expected a manifest append function or open_manifest/ManifestWriter."  
    )  
  
  
def _cfg_bool(v: Any, default: bool) -> bool:  
    if v is None:  
        return default  
    if isinstance(v, bool):  
        return v  
    if isinstance(v, (int, float)):  
        return bool(v)  
    if isinstance(v, str):  
        s = v.strip().lower()  
        if s in ("1", "true", "yes", "y", "on"):  
            return True  
        if s in ("0", "false", "no", "n", "off", ""):  
            return False  
    return default  
  
  
def _get_step_runner(logger: Any) -> Callable[[Any, dict[str, Any], MutableMapping[str, Any]], Any]:  
    """  
    Return a callable run_action(driver, step, cfg).  
  
    Prefer a real ACT run_action; otherwise fallback to ACT-1B run_actions_logged([step])  
    and raise on non-ok outcome so PIPE can emit step_error deterministically.  
    """  
    candidates = (  
        ("ACT.act_1a_dispatch", "run_action"),  
        ("ACT.act_1a_run_action", "run_action"),  
        ("ACT.act_1a_actions", "run_action"),  
        ("ACT.act_1b_logging_integration", "run_action"),  
    )  
    for mod_name, attr in candidates:  
        try:  
            mod = importlib.import_module(mod_name)  
        except Exception:  
            continue  
        fn = getattr(mod, attr, None)  
        if callable(fn):  
  
            def _wrapped(driver: Any, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
                try:  
                    return fn(driver, step, cfg)  
                except TypeError:  
                    # tolerate alternate ACT signatures without changing ACT  
                    return fn(driver, step, cfg, logger=logger)  
  
            return _wrapped  
  
    def _fallback(driver: Any, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
        outcomes = run_actions_logged(driver, [step], cfg, logger=logger)  
        for o in outcomes:  
            if not getattr(o, "ok", True):  
                raise RuntimeError(getattr(o, "error_message", None) or "step_failed")  
        return outcomes  
  
    return _fallback  
  
  
def _safe_step_inputs(step: dict[str, Any]) -> dict[str, Any]:  
    allow = (  
        "name",  
        "url",  
        "selector_ref",  
        "selector",  
        "by",  
        "strategy",  
        "timeout",  
        "condition",  
        "seconds",  
        "path",  
        "save_as",  
    )  
    out: dict[str, Any] = {}  
    for k in allow:  
        if k in step and step.get(k) not in (None, ""):  
            out[k] = step.get(k)  
    # never include common secret-bearing keys  
    for sk in ("secret", "text", "password", "token", "api_key"):  
        out.pop(sk, None)  
    return out  
  
  
def _outcome_ok(o: Any) -> Optional[bool]:  
    # dict outcomes  
    if isinstance(o, dict):  
        v = o.get("ok")  
        if isinstance(v, bool):  
            return v  
        v = o.get("success")  
        if isinstance(v, bool):  
            return v  
        v = o.get("passed")  
        if isinstance(v, bool):  
            return v  
        st = o.get("status")  
        if isinstance(st, str):  
            s = st.strip().lower()  
            if s in {"success", "ok", "passed"}:  
                return True  
            if s in {"failure", "failed", "error"}:  
                return False  
        return None  
  
    # object outcomes  
    for attr in ("ok", "success", "passed"):  
        v = getattr(o, attr, None)  
        if isinstance(v, bool):  
            return v  
  
    st = getattr(o, "status", None)  
    if isinstance(st, str):  
        s = st.strip().lower()  
        if s in {"success", "ok", "passed"}:  
            return True  
        if s in {"failure", "failed", "error"}:  
            return False  
  
    return None   
  
  
def _outcome_error(o: Any) -> Optional[str]:  
    if isinstance(o, dict):  
        for k in ("error_message", "error", "message", "exception"):  
            v = o.get(k)  
            if v:  
                return str(v)  
        return None  
    for k in ("error_message", "error", "message", "exception"):  
        v = getattr(o, k, None)  
        if v:  
            return str(v)  
    return None  
  
  
def _step_logs_from_outcomes(steps: list[dict[str, Any]], outcomes: Any) -> list[dict[str, Any]]:  
    outs = list(outcomes) if outcomes is not None else []  
    logs: list[dict[str, Any]] = []  
    for i, st in enumerate(steps):  
        row: dict[str, Any] = {  
            "index": i,  
            "action": str(st.get("action", "")).strip(),  
            "inputs": _safe_step_inputs(st),  
            "status": "unknown",  
        }  
        if i < len(outs):  
            ok = _outcome_ok(outs[i])  
            if isinstance(ok, bool):  
                row["status"] = "success" if ok else "failure"  
                if not ok:  
                    err = _outcome_error(outs[i])  
                    if err:  
                        row["error"] = err  
        logs.append(row)  
    return logs  
  
  
def run_worklist(cfg: MutableMapping[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:   
    """  
    Run the workflow for all IDs from INPUT-1B using LOOP-1B + ACT, recording to STATE-1B.  
    """  
    from ACT.act_1a_action_engine import ActionEngineError  
  
    logger = setup_logging(cfg)  
    bind_context(cfg, run_id=cfg.get("RUN_ID"))
  
    try:  
        ids = _load_worklist_ids(cfg)  
    except Exception as e:  
        ids = []  
        log_exception(  
            logger,  
            e,  
            event="worklist_error",  
            milestone="PIPE-1A",  
            tag="worklist_load_failure",  
        )  
  
    if not ids:  
        # Allow steps-only workflows (e.g., CLI truth tests) to run once.  
        ids = [str(cfg.get("CURRENT_ID") or "SINGLE")]  
        
    cfg["TOTAL_ITEMS"] = len(ids)   
  
    sink = _open_state_sink(cfg)  
  
    log_event(logger, "run_start", total_items=len(ids), total_steps=len(steps))  
  
    stop_on_error = _cfg_bool(cfg.get("STOP_ON_ERROR"), True)   
  
    driver = make_driver(cfg)  
    items: list[dict[str, Any]] = []  
    run_errors: list[str] = []  
  
    try:  
        for item_id in _iterate_items(cfg, ids):  
            # LOOP-1B should inject these; ensure CURRENT_ID exists at minimum.  
            if not cfg.get("CURRENT_ID"):  
                cfg["CURRENT_ID"] = str(item_id)  
  
            # Bind per-item context for logs across modules (ACT may also bind opportunistically).  
            bind_context(  
                cfg,  
                current_id=cfg.get("CURRENT_ID"),  
                item_index=cfg.get("ITEM_INDEX"),  
                total_items=cfg.get("TOTAL_ITEMS"),  
            )  
  
            item_ok = True  
            err_summary: Optional[str] = None  
  
            # Execute steps via ACT-1B (wraps ACT-1A). This prevents silent failure masking.  
            run_id = cfg.get("RUN_ID")  
            step_logs: Optional[list[dict[str, Any]]] = None  
            try:  
                outcomes = run_actions_logged(driver, steps, cfg, logger=logger)  
                step_logs = _step_logs_from_outcomes(steps, outcomes)  
                item_ok = all((_outcome_ok(o) is True) for o in outcomes)  
  
                if not item_ok:  
                    first_err = next((o for o in outcomes if _outcome_ok(o) is not True), None)    
                    err_summary = (  
                        str(getattr(first_err, "error_message", None))  
                        if first_err is not None and getattr(first_err, "error_message", None)  
                        else "step_failed"  
                    )  
                    run_errors.append(err_summary)  
  
            except ActionEngineError as ae:  
                item_ok = False  
                cfg["ACT_LOGGED_ALL_OK"] = False  
                cfg["ACT_ANY_FAILED"] = True  
                cause = ae.__cause__ if getattr(ae, "__cause__", None) is not None else ae  
                err_summary = f"{type(cause).__name__}: {cause}"  
                run_errors.append(err_summary)  
  
                # Guarantee PIPE-1E sees a canonical step_error event  
                def _extract_step_index(err: Any) -> Optional[int]:  
                    for k in ("step_index", "index", "failed_step_index"):  
                        v = getattr(err, k, None)  
                        if isinstance(v, int) and not isinstance(v, bool):  
                            return v  
                        if isinstance(v, str) and v.strip().isdigit():  
                            return int(v.strip())  
                    return None  
  
                si = _extract_step_index(ae)  
  
                # Only emit a step_error if we actually know the failing step index.  
                # (ACT already emits the canonical step_error with the correct index.)  
                if si is not None:  
                    act = None  
                    try:  
                        if 0 <= si < len(steps):  
                            act = steps[si].get("action")  
                    except Exception:  
                        act = None  
  
                    log_event(  
                        logger,  
                        "step_error",  
                        step_index=si,  
                        action=act,  
                        run_id=run_id,  
                        error_message=err_summary,  
                    )  
  
                if step_logs is None:  
                    step_logs = _step_logs_from_outcomes(steps, [])  
  
                # Never guess: only mark a step as failed if we know its index.  
                if si is not None and 0 <= si < len(step_logs):  
                    step_logs[si]["status"] = "failure"  
                    step_logs[si]["error"] = err_summary   
   
            except Exception as e:  
                item_ok = False  
                err_summary = f"{type(e).__name__}: {e}"  
                run_errors.append(err_summary)  
  
                log_exception(  
                    logger,  
                    e,  
                    event="item_error",  
                    milestone="PIPE-1A",  
                    tag="item_failure",  
                    current_id=cfg.get("CURRENT_ID"),  
                    item_index=cfg.get("ITEM_INDEX"),  
                )  
                if step_logs is None:  
                    step_logs = _step_logs_from_outcomes(steps, [])   
  
            # Preserve prior behavior: non-recoverable exceptions for the item are recorded.  
            # (This block mostly guards unexpected errors outside the per-step loop.)  
            if not item_ok and err_summary is None:  
                err_summary = "step_failed"  
  
            record = {  
                "run_id": cfg.get("RUN_ID"),  
                "item_id": str(cfg.get("CURRENT_ID", item_id)),  
                "ok": bool(item_ok),  
                "error": err_summary,  
            }  
            if step_logs is not None:  
                record["step_logs"] = step_logs   
  
            try:  
                sink.append(cfg, record)  
            except BaseException as e:  
                # STATE sink failure should be visible and non-silent  
                log_exception(  
                    logger,  
                    e,  
                    event="item_error",  
                    milestone="PIPE-1A",  
                    tag="state_sink_failure",  
                    current_id=cfg.get("CURRENT_ID"),  
                    item_index=cfg.get("ITEM_INDEX"),  
                )  
                raise  
  
            items.append(record)  
  
    finally:  
        try:  
            driver.quit()  
        finally:  
            sink.close()  
  
    success_count = sum(1 for r in items if r["ok"])  
    failed_count = len(items) - success_count  
    ok = (failed_count == 0)  
  
    summary: dict[str, Any] = {  
        "run_id": cfg.get("RUN_ID"),  
        "total_items": len(items),  
  
        # IMPORTANT: boolean success flag (some downstream code treats "success" as a bool)  
        "success": ok,  
        "failed": failed_count,  
        "ok": ok,  
  
        # Preserve counts explicitly  
        "success_count": success_count,  
        "failed_count": failed_count,  
  
        "items": items,  
    }  
    if len(items) == 1 and isinstance(items[0].get("step_logs"), list):  
        summary.setdefault("step_logs", items[0]["step_logs"])  
    if run_errors:  
        summary["errors"] = run_errors    
  
    log_event(logger, "run_end", **summary)  
    return summary  
  
  
def dev_smoke() -> None:  
    # Import-level smoke + basic callable checks (no Selenium session).  
    assert callable(run_worklist)  
    assert "run_worklist" in __all__  
    # Re-exports should exist as attributes (may be None depending on STATE-1B implementation).  
    assert hasattr(state_1b, "__name__")  
    assert "open_manifest" in __all__  
    assert "ManifestWriter" in __all__  
    assert "manifest_append" in __all__  
  
  
if __name__ == "__main__":  
    dev_smoke()  