"""  
CLI-1A — Command Line Pipeline Runner.  
  
Provides:  
- run_pipeline(cfg) -> run summary dict (PIPE-2E)  
- __main__ runnable entry point (uses an inline config for now)  
  
Integrations:  
- ENTRY-1A: WebDriver creation (best-effort resolution)  
- LOG-1A: logging init + structured events (best-effort resolution)  
- PIPE orchestration: prefer PIPE-2C wrapper; fallback to PIPE runner (PIPE-1E/PIPE-2B)  
- PIPE-2E: run summary object  
"""  
  
from __future__ import annotations  

import argparse   
import importlib  
import pkgutil  
from typing import Any, Callable, Dict, List, Optional, Tuple  
  
from PIPE.pipe_2e_run_summary import (  
    finish_run_summary,  
    record_artifact,  
    record_item_failure,  
    record_item_success,  
    start_run_summary,  
)  
  
__all__ = ["run_pipeline"]  
  
  
# ---------------------------  
# Best-effort resolvers  
# ---------------------------  
  
def _resolve_entry_driver_factory() -> Callable[..., Any]:  
    fn_names = (  
        "create_driver",  
        "make_driver",  
        "build_driver",  
        "get_driver",  
        "create_webdriver",  
        "make_webdriver",  
        "build_webdriver",  
        "get_webdriver",  
    )  
  
    # common module first  
    try:  
        m = importlib.import_module("ENTRY.entry_1a_webdriver_bootstrap")  
        for n in fn_names:  
            fn = getattr(m, n, None)  
            if callable(fn):  
                return fn  
    except Exception:  
        pass  
  
    # scan ENTRY.*  
    pkg = importlib.import_module("ENTRY")  
    for mi in pkgutil.iter_modules(pkg.__path__, prefix=pkg.__name__ + "."):  
        try:  
            mod = importlib.import_module(mi.name)  
        except Exception:  
            continue  
        for n in fn_names:  
            fn = getattr(mod, n, None)  
            if callable(fn):  
                return fn  
  
    raise RuntimeError("Could not resolve ENTRY-1A WebDriver factory.")  
  
  
def _make_driver(factory: Callable[..., Any], cfg: Dict[str, Any]) -> Any:  
    try:  
        return factory(cfg)  
    except TypeError:  
        return factory()  
  
  
def _resolve_log_init() -> Optional[Callable[..., Any]]:  
    """  
    Best-effort LOG-1A initialization (if the project exposes one).  
    """  
    candidates: Tuple[Tuple[str, Tuple[str, ...]], ...] = (  
        ("LOG.log_1a_structured_logger", ("init_logging", "setup_logging", "configure_logging")),  
        ("LOG.log_1a_logger", ("init_logging", "setup_logging", "configure_logging")),  
        ("LOG.log_1a", ("init_logging", "setup_logging", "configure_logging")),  
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
  
  
def _resolve_log_emitter() -> Optional[Callable[..., Any]]:  
    """  
    Best-effort LOG-1A structured event emitter.  
    """  
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
  
  
def _emit_log(emitter: Optional[Callable[..., Any]], event: Dict[str, Any]) -> None:  
    if emitter is None:  
        print(f"LOG_EVENT: {event}")  
        return  
    try:  
        try:  
            emitter(event=event)  
        except TypeError:  
            try:  
                emitter(event)  
            except TypeError:  
                emitter(**event)  
    except Exception:  
        print(f"LOG_EVENT_FALLBACK: {event}")  
  
  
def _resolve_pipe_2c_runner() -> Optional[Callable[..., Any]]:  
    try:  
        from PIPE.pipe_2c_error_plumbing import run_with_error_plumbing  # type: ignore  
  
        return run_with_error_plumbing  
    except Exception:  
        return None  
  
  
def _resolve_pipeline_runner(cfg: Dict[str, Any]) -> Callable[..., Any]:  
    """  
    Prefer PIPE-1E runner if resolvable; otherwise fall back to PIPE-2B run_steps.  
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
  
  
def _coerce_steps(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:  
    s = cfg.get("STEPS", None)  
    if s is None:  
        s = cfg.get("steps", None)  
    if s is None:  
        return []  
    if not isinstance(s, list):  
        raise TypeError("cfg['STEPS'] must be a list of step dicts")  
    return [dict(x) for x in s]  
  
  
# ---------------------------  
# Public API  
# ---------------------------  
  
def run_pipeline(cfg: Dict[str, Any]) -> Dict[str, Any]:  
    """  
    Execute the pipeline based on cfg and return a standardized run summary (PIPE-2E).  
    """  
    run_id = cfg.get("RUN_ID", cfg.get("run_id", None))  
    summary = start_run_summary(run_id=run_id)  
  
    log_init = _resolve_log_init()  
    if callable(log_init):  
        try:  
            log_init(cfg=cfg)  
        except TypeError:  
            try:  
                log_init(cfg)  
            except TypeError:  
                log_init()  
  
    log_emit = _resolve_log_emitter()  
    _emit_log(log_emit, {"event": "run_started", "run_id": summary.get("run_id"), "start_time": summary.get("start_time")})  
  
    driver = None  
    try:  
        factory = _resolve_entry_driver_factory()  
        driver = _make_driver(factory, cfg)  
  
        steps = _coerce_steps(cfg)  
  
        # Prefer PIPE-2C (error plumbing wrapper) when available  
        pipe_2c = _resolve_pipe_2c_runner()  
        if callable(pipe_2c):  
            pipe_res = pipe_2c(  
                driver=driver,  
                cfg=cfg,  
                steps=steps,  
                work_items=cfg.get("WORK_ITEMS", None),  
                writer=None,  
            )  
            # Map PIPE-2C counts into summary  
            items_total = int(pipe_res.get("items_total", 0))  
            items_ok = int(pipe_res.get("items_ok", 0))  
            items_failed = int(pipe_res.get("items_failed", 0))  
            summary["items_total"] = items_total  
            summary["items_success"] = items_ok  
            summary["items_failed"] = items_failed  
  
            last_err = pipe_res.get("last_error")  
            if isinstance(last_err, dict):  
                summary["errors"].append(last_err)  
  
        else:  
            # Fallback: run once as a single "item"  
            runner = _resolve_pipeline_runner(cfg)  
            results = _call_runner(runner, driver, steps, cfg)  
  
            # If per-step results list exists, treat any ok=False as failure  
            failed = False  
            if isinstance(results, list):  
                for r in results:  
                    if isinstance(r, dict) and ("ok" in r) and not bool(r.get("ok")):  
                        failed = True  
                        break  
  
            if failed:  
                record_item_failure(summary, item_id=cfg.get("ITEM_ID", None), error={"code": "UNKNOWN_ERROR", "type": "StepFailure", "message": "One or more steps failed"})  
            else:  
                record_item_success(summary, item_id=cfg.get("ITEM_ID", None))  
  
        # Optional artifact integration (if caller put artifacts in cfg)  
        # (Additive; does not perform any artifact normalization here.)  
        for ap in cfg.get("ARTIFACT_PATHS", []) or []:  
            record_artifact(summary, str(ap))  
  
    except Exception as exc:  
        # Keep CLI resilient: record a failure and re-raise only if requested.  
        record_item_failure(summary, item_id=cfg.get("ITEM_ID", None), error=exc)  
        _emit_log(  
            log_emit,  
            {"event": "run_exception", "run_id": summary.get("run_id"), "error_type": exc.__class__.__name__, "error_message": str(exc)},  
        )  
        if bool(cfg.get("RAISE_ON_ERROR", False)):  
            raise  
    finally:  
        try:  
            if driver is not None:  
                driver.quit()  
        except Exception:  
            pass  
  
    summary = finish_run_summary(summary)  
    _emit_log(  
        log_emit,  
        {  
            "event": "run_finished",  
            "run_id": summary.get("run_id"),  
            "items_total": summary.get("items_total"),  
            "items_success": summary.get("items_success"),  
            "items_failed": summary.get("items_failed"),  
            "duration_seconds": summary.get("duration_seconds"),  
        },  
    )  
    return summary  
  
  
def _print_summary(summary: Dict[str, Any]) -> None:  
    print("\nRUN SUMMARY")  
    print("----------")  
    print(f"items_total:       {summary.get('items_total')}")  
    print(f"items_success:     {summary.get('items_success')}")  
    print(f"items_failed:      {summary.get('items_failed')}")  
    print(f"duration_seconds:  {summary.get('duration_seconds')}")  
  
  
if __name__ == "__main__":  
    parser = argparse.ArgumentParser(description="Run the automation pipeline.")  
    parser.add_argument("--config", help="Path to config YAML/JSON file", default=None)  
    args = parser.parse_args()  
  
    # Simple inline defaults for now; config file overrides these.  
    cfg = {  
        "BROWSER": "edge",  
        "HEADLESS": True,  
        "STEPS": [],  
        "STOP_ON_ERROR": False,  
        "RAISE_ON_ERROR": False,  
    }  
  
    if args.config:  
        from CLI.cli_1b_config_loader import load_config  
  
        loaded = load_config(args.config)  
        cfg.update(loaded)  
  
    s = run_pipeline(cfg)  
    _print_summary(s)   