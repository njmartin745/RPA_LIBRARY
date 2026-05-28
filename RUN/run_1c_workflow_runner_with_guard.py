# RUN/run_1c_workflow_runner_with_guard.py  
"""  
RUN-1C — Wrapper to enable GUARD-1A without refactoring RUN-1A.  
  
This wrapper is best-effort:  
- Calls existing RUN-1A run_workflow  
- If cfg['GUARD_ENABLED'] true and a step_runner_fn is provided (or supported by RUN-1A),  
  wraps it using GUARD.wrap_step_runner  
  
If RUN-1A does not accept a step runner override, this wrapper will still run (guard may be inactive).  
"""  
  
from __future__ import annotations  
  
from typing import Any, Callable, Optional  
  
from GUARD.guard_1a_runtime import normalize_guard_cfg, wrap_step_runner  
  
__all__ = [  
    "run_workflow_with_guard",  
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
  
  
def run_workflow_with_guard(*args, cfg: dict | None = None, step_runner_fn=None, **kwargs) -> Any:  
    run_workflow = _import_run_workflow()  
  
    cfg_in = cfg if isinstance(cfg, dict) else (kwargs.get("cfg") if isinstance(kwargs.get("cfg"), dict) else {})  
    guard_cfg = normalize_guard_cfg(cfg_in)  
  
    wrapped_step_runner = step_runner_fn  
    if guard_cfg.get("GUARD_ENABLED") and callable(step_runner_fn):  
        wrapped_step_runner = wrap_step_runner(step_runner_fn, cfg=cfg_in)  
  
    # Best-effort: try passing a runner override if RUN-1A supports it; otherwise call unchanged.  
    if wrapped_step_runner is not None:  
        for kw_name in ("step_runner_fn", "step_runner", "pipe_step_runner"):  
            try:  
                return run_workflow(*args, cfg=cfg_in, **{**kwargs, kw_name: wrapped_step_runner})  
            except TypeError:  
                continue  
  
    # Fall back: just run RUN-1A (guard may be applied internally if supported by cfg)  
    try:  
        return run_workflow(*args, cfg=cfg_in, **kwargs)  
    except TypeError:  
        return run_workflow(*args, **kwargs)  