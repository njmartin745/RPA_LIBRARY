"""  
PIPE-2A — Variable-aware Step Execution (VAR-1A integration).  
  
Goal  
----  
Ensure ${VAR} substitution works end-to-end inside rendered steps at execution time:  
- URLs  
- selectors  
- expected text  
- JS script snippets (string substitution only)  
- output paths (manifest/log/download dirs) via optional cfg-key rendering  
  
This module is an additive, thin adapter:  
- imports and uses VAR-1A (does not duplicate it)  
- does not redefine ACT/VAL/NAV modules  
- renders every step (deep) prior to execution  
  
Public API  
----------  
render_step(step, cfg, *, step_index=None) -> Any  
render_cfg_inplace(cfg, *, keys=None) -> dict  
execute_step_var_aware(driver, step, cfg, *, step_index, executor=None) -> Any  
execute_steps_var_aware(driver, steps, cfg, *, executor=None, render_cfg_keys=None) -> list  
  
Missing-variable errors  
-----------------------  
If a variable is missing during rendering, raises a ValueError with:  
- step index  
- action  
- missing var name  
"""  
  
from __future__ import annotations  
  
import importlib  
import pkgutil  
import re  
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence  
  
from VAR.var_1a_runtime_store import render_vars  
  
__all__ = [  
    "render_step",  
    "render_cfg_inplace",  
    "execute_step_var_aware",  
    "execute_steps_var_aware",  
]  
  
_MISSING_VAR_RE = re.compile(r"Missing runtime variable:\s*'([^']+)'")  
  
  
def _missing_var_name(exc: BaseException) -> Optional[str]:  
    msg = str(exc) if exc is not None else ""  
    m = _MISSING_VAR_RE.search(msg)  
    return m.group(1) if m else None  
  
  
def render_step(step: Any, cfg: Mapping[str, Any], *, step_index: Optional[int] = None) -> Any:  
    """  
    Deep-render a step through VAR-1A.  
  
    Raises ValueError with step context if a variable is missing.  
    """  
    try:  
        return render_vars(step, cfg)  
    except KeyError as e:  
        # Enhance error with step context.  
        idx = "?" if step_index is None else str(step_index)  
        action = None  
        try:  
            if isinstance(step, Mapping):  
                action = step.get("action")  
        except Exception:  
            action = None  
  
        missing = _missing_var_name(e) or "UNKNOWN_VAR"  
        raise ValueError(f"Missing variable {missing!r} while rendering step[{idx}] action={action!r}") from e  
  
  
def render_cfg_inplace(cfg: MutableMapping[str, Any], *, keys: Optional[Iterable[str]] = None) -> Dict[str, Any]:  
    """  
    Render selected cfg keys in-place via VAR-1A.  
  
    This supports placeholder substitution for output paths (manifest/log/download dirs)  
    without changing other module interfaces.  
  
    By default, renders a conservative set of common path-like keys if present.  
    """  
    if keys is None:  
        keys = (  
            "OUTPUT_DIR",  
            "ARTIFACT_DIR",  
            "DOWNLOAD_DIR",  
            "DOWNLOAD_PATH",  
            "LOG_DIR",  
            "LOG_PATH",  
            "MANIFEST_DIR",  
            "MANIFEST_PATH",  
        )  
  
    for k in keys:  
        if k in cfg:  
            v = cfg.get(k)  
            # Render only simple renderable types to avoid surprising behavior.  
            if isinstance(v, (str, dict, list, tuple)):  
                cfg[k] = render_vars(v, cfg)  
    return dict(cfg)  
  
  
def _resolve_default_executor() -> Optional[Callable[..., Any]]:  
    """  
    Best-effort resolution of an existing step executor from PIPE/ACT packages.  
  
    This is intentionally heuristic and non-invasive. If not found, caller should  
    provide an executor.  
    """  
    candidate_modules = [  
        # likely PIPE-1D style names  
        "PIPE.pipe_1d_step_executor",  
        "PIPE.pipe_1d_execute_steps",  
        "PIPE.pipe_1d_step_execution",  
        "PIPE.pipe_1d_step_runner",  
        # likely ACT engine names  
        "ACT.act_1b_step_executor",  
        "ACT.act_1a_step_executor",  
        "ACT.act_1a_actions",  
    ]  
    candidate_fns = ["execute_step", "run_step", "do_step", "apply_step"]  
  
    for mod_name in candidate_modules:  
        try:  
            m = importlib.import_module(mod_name)  
        except Exception:  
            continue  
        for fn_name in candidate_fns:  
            fn = getattr(m, fn_name, None)  
            if callable(fn):  
                return fn  
  
    # scan PIPE.* then ACT.* for a plausible function name  
    for pkg_name in ("PIPE", "ACT"):  
        try:  
            pkg = importlib.import_module(pkg_name)  
        except Exception:  
            continue  
        if not hasattr(pkg, "__path__"):  
            continue  
        for mi in pkgutil.iter_modules(pkg.__path__, prefix=pkg.__name__ + "."):  
            try:  
                m = importlib.import_module(mi.name)  
            except Exception:  
                continue  
            for fn_name in candidate_fns:  
                fn = getattr(m, fn_name, None)  
                if callable(fn):  
                    return fn  
  
    return None  
  
  
def _call_executor(executor: Callable[..., Any], driver: Any, step: Any, cfg: Mapping[str, Any], step_index: int) -> Any:  
    """  
    Call an executor with flexible signatures, without requiring refactors elsewhere.  
    """  
    # Try common keyword signature first.  
    try:  
        return executor(driver=driver, step=step, cfg=cfg, step_index=step_index)  
    except TypeError:  
        pass  
    try:  
        return executor(driver, step, cfg, step_index)  
    except TypeError:  
        pass  
    try:  
        return executor(driver, step, cfg)  
    except TypeError:  
        pass  
    # last resort: driver, step  
    return executor(driver, step)  
  
  
def execute_step_var_aware(  
    driver: Any,  
    step: Any,  
    cfg: MutableMapping[str, Any],  
    *,  
    step_index: int,  
    executor: Optional[Callable[..., Any]] = None,  
) -> Any:  
    """  
    Render a single step through VAR-1A, then execute it using the provided executor  
    (or a best-effort resolved default executor).  
    """  
    rendered = render_step(step, cfg, step_index=step_index)  
  
    exec_fn = executor or _resolve_default_executor()  
    if exec_fn is None:  
        action = rendered.get("action") if isinstance(rendered, Mapping) else None  
        raise RuntimeError(  
            "No step executor provided and none could be resolved. "  
            f"Cannot execute step[{step_index}] action={action!r}. "  
            "Pass executor=... (e.g., PIPE-1D or ACT engine execute_step)."  
        )  
  
    return _call_executor(exec_fn, driver, rendered, cfg, step_index)  
  
  
def execute_steps_var_aware(  
    driver: Any,  
    steps: Sequence[Any],  
    cfg: MutableMapping[str, Any],  
    *,  
    executor: Optional[Callable[..., Any]] = None,  
    render_cfg_keys: Optional[Iterable[str]] = None,  
) -> List[Any]:  
    """  
    Render cfg path-like keys (optional), then render+execute each step in order.  
    Returns list of per-step results (whatever the underlying executor returns).  
    """  
    if render_cfg_keys is not None:  
        render_cfg_inplace(cfg, keys=render_cfg_keys)  
    else:  
        # default behavior: render a small set of path-like keys  
        render_cfg_inplace(cfg)  
  
    results: List[Any] = []  
    for i, step in enumerate(steps):  
        results.append(execute_step_var_aware(driver, step, cfg, step_index=i, executor=executor))  
    return results  