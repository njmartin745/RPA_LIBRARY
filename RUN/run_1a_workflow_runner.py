# RUN/run_1a_workflow_runner.py  
"""  
RUN-1A — Unified Workflow Runner  
  
Single entry point that executes workflows produced by WORKFLOW-1A using the existing  
PIPE orchestration system.  
  
Execution flow:  
1) Load workflow via WORKFLOW-1A loader  
2) Validate steps using LINT-1A  
3) Merge cfg defaults + overrides  
4) Initialize VAR store (seeded from workflow vars)  
5) Call PIPE orchestrator/runner (no duplicated logic)  
6) Return structured summary  
"""  
  
from __future__ import annotations  
  
import inspect  
import json  
import uuid  
from copy import deepcopy  
from pathlib import Path  
from typing import Any, Callable, Dict, List, Optional, Tuple  
  
from LINT.lint_1a_steps_validator import validate_steps_file  
from WORKFLOWS.workflow_1a_loader import load_validate_normalize_workflow  
  
import VAR.var_1a_runtime_store as var_store_mod  
  
__all__ = [  
    "run_workflow",  
]  
  
  
def _looks_like_repo_root(p: Path) -> bool:  
    return (p / "SCHEMA" / "steps_schema.json").exists() and (p / "PIPE").is_dir()  
  
  
def _find_repo_root(start: Path) -> Path:  
    s = start.parent if start.is_file() else start  
    for cand in [s, *s.parents]:  
        if _looks_like_repo_root(cand):  
            return cand  
    return s  
  
  
def _write_json(path: Path, obj: Any) -> None:  
    path.parent.mkdir(parents=True, exist_ok=True)  
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")  
  
  
def _lint_steps_or_raise(steps_path: Path) -> None:  
    report = validate_steps_file(steps_path)  
    if not isinstance(report, dict) or report.get("valid") is not True:  
        raise ValueError(  
            "Steps failed LINT-1A validation.\n"  
            f"steps_path: {steps_path}\n"  
            f"report: {json.dumps(report, indent=2, ensure_ascii=False)}"  
        )  
  
  
def _init_var_store(seed: Optional[dict]) -> Any:  
    """  
    Best-effort initialization using VAR-1A without assuming an exact API.  
    Returns a store object (may be a dict or a class instance depending on VAR-1A).  
    """  
    seed = seed if isinstance(seed, dict) else {}  
  
    # Prefer a factory if present  
    for fn_name in ("create_var_store", "new_var_store", "make_var_store", "create_store", "new_store"):  
        fn = getattr(var_store_mod, fn_name, None)  
        if callable(fn):  
            try:  
                return fn(seed)  
            except TypeError:  
                try:  
                    store = fn()  
                    _seed_var_store(store, seed)  
                    return store  
                except Exception:  
                    pass  
  
    # Prefer a class if present  
    for cls_name in ("RuntimeVarStore", "VarStore", "VarStore1A"):  
        cls = getattr(var_store_mod, cls_name, None)  
        if cls is None:  
            continue  
        try:  
            return cls(seed)  # type: ignore[misc]  
        except TypeError:  
            try:  
                store = cls()  # type: ignore[misc]  
                _seed_var_store(store, seed)  
                return store  
            except Exception:  
                pass  
  
    # Fallback to plain dict (still satisfies "initialized")  
    return deepcopy(seed)  
  
  
def _seed_var_store(store: Any, seed: dict) -> None:  
    if not seed:  
        return  
    # common patterns  
    if isinstance(store, dict):  
        store.update(seed)  
        return  
    for meth in ("seed", "update", "set_many", "merge"):  
        m = getattr(store, meth, None)  
        if callable(m):  
            try:  
                m(seed)  
                return  
            except Exception:  
                pass  
    set_fn = getattr(store, "set", None)  
    if callable(set_fn):  
        ok = False  
        for k, v in seed.items():  
            try:  
                set_fn(k, v)  
                ok = True  
            except Exception:  
                pass  
        if ok:  
            return  
    # last-ditch: attribute bag  
    data = getattr(store, "data", None)  
    if isinstance(data, dict):  
        data.update(seed)  
  
  
def _find_pipe_entrypoint() -> Tuple[Callable[..., Any], str]:  
    """  
    Finds an existing PIPE runner/orchestrator function by importing PIPE modules  
    (no side-effect-free guarantee is stated for PIPE, but this is the intended integration layer).  
  
    Returns (callable, label) or raises ValueError.  
    """  
    candidates: List[Tuple[str, str]] = [  
        ("PIPE.pipe_1e_runner", "run_pipeline"),  
        ("PIPE.pipe_1e_runner", "run"),  
        ("PIPE.pipe_1e_runner", "run_steps"),  
        ("PIPE.pipe_1a_run_orchestrator", "run_orchestrator"),  
        ("PIPE.pipe_1a_run_orchestrator", "run"),  
        ("PIPE.pipe_1d_step_executor", "execute_steps"),  
    ]  
  
    last_err: Optional[Exception] = None  
    for mod_name, fn_name in candidates:  
        try:  
            mod = __import__(mod_name, fromlist=[fn_name])  
            fn = getattr(mod, fn_name, None)  
            if callable(fn):  
                return fn, f"{mod_name}.{fn_name}"  
        except Exception as e:  
            last_err = e  
  
    raise ValueError(  
        "Could not locate a PIPE runner entrypoint.\n"  
        "Tried common candidates in PIPE (pipe_1e_runner/pipe_1a_run_orchestrator/pipe_1d_step_executor).\n"  
        f"Last import error (if any): {last_err}"  
    )  
  
  
def _call_pipeline(fn: Callable[..., Any], *, cfg: dict, steps: List[dict], steps_path: Path, workflow_path: Path) -> Any:  
    """  
    Calls the discovered PIPE entrypoint with a best-effort argument mapping via signature inspection.  
    """  
    sig = inspect.signature(fn)  
    params = sig.parameters  
  
    # If it accepts **kwargs, we can safely provide a richer set.  
    has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())  
  
    # Build a conservative kwargs set.  
    candidate_kwargs = {  
        "cfg": cfg,  
        "config": cfg,  
        "config_dict": cfg,  
        "steps": steps,  
        "steps_list": steps,  
        "steps_path": str(steps_path),  
        "workflow_path": str(workflow_path),  
    }  
  
    # Filter to accepted params unless **kwargs exists  
    kwargs: Dict[str, Any] = {}  
    if has_varkw:  
        # include a small set only (avoid surprising keys)  
        kwargs = {  
            "cfg": cfg,  
            "steps": steps,  
            "steps_path": str(steps_path),  
            "workflow_path": str(workflow_path),  
        }  
    else:  
        for k, v in candidate_kwargs.items():  
            if k in params:  
                kwargs[k] = v  
  
    # If no kwargs matched, try positional patterns  
    if not kwargs:  
        # Common: fn(cfg) or fn(cfg, steps)  
        try:  
            return fn(cfg, steps)  # type: ignore[misc]  
        except TypeError:  
            try:  
                return fn(cfg)  # type: ignore[misc]  
            except TypeError:  
                try:  
                    return fn(str(steps_path), cfg)  # type: ignore[misc]  
                except TypeError as e:  
                    raise ValueError(  
                        f"PIPE entrypoint signature not supported: {fn}\n"  
                        f"Signature: {sig}\n"  
                        f"Error: {e}"  
                    )  
  
    return fn(**kwargs)  # type: ignore[misc]  
  
  
def run_workflow(workflow_path: str | Path, cfg_overrides: Optional[dict] = None) -> dict:  
    """  
    Executes a workflow file using WORKFLOW-1A + LINT-1A + PIPE + VAR.  
  
    Returns:  
      {  
        "workflow": "...",  
        "run_id": "...",  
        "steps_executed": N,  
        "success": bool,  
        "errors": [...],  
        "artifacts": [...]  
      }  
    """  
    wf_path = Path(workflow_path)  
    repo_root = _find_repo_root(wf_path)  
  
    workflow_norm, cfg_out, steps_out = load_validate_normalize_workflow(wf_path, repo_root=repo_root)  
  
    # Merge overrides  
    cfg = deepcopy(cfg_out)  
    if cfg_overrides is not None:  
        if not isinstance(cfg_overrides, dict):  
            raise ValueError("cfg_overrides must be a dict if provided")  
        cfg.update(cfg_overrides)  
  
    run_id = uuid.uuid4().hex  
  
    # Write steps to a temp-ish repo-local location (useful for debugging + PIPE compatibility)  
    tmp_dir = repo_root / ".dev_tmp"  
    tmp_dir.mkdir(parents=True, exist_ok=True)  
    steps_path = tmp_dir / f"run_1a_steps_{run_id}.json"  
    _write_json(steps_path, steps_out)  
  
    # LINT-1A validation  
    _lint_steps_or_raise(steps_path)  
  
    # VAR store init  
    vars_seed = workflow_norm.get("vars")  
    if not isinstance(vars_seed, dict):  
        vars_seed = cfg.get("vars_seed")  
    var_store = _init_var_store(vars_seed if isinstance(vars_seed, dict) else {})  
    cfg.setdefault("var_store", var_store)  
  
    # Provide useful metadata to PIPE (non-breaking if ignored)  
    # Ensure PIPE/LOG bind to the same run id (PIPE expects RUN_ID).  
    cfg.setdefault("RUN_ID", run_id)  
    cfg.setdefault("run_id", run_id)  
  
    cfg.setdefault("workflow_name", workflow_norm.get("name"))  
  
    # Ensure PIPE-1E/PIPE-1C can load the steps (they key off STEPS_PATH / STEPS).  
    cfg["STEPS_PATH"] = str(steps_path)  
    steps_inline = steps_out.get("steps") if isinstance(steps_out, dict) else steps_out  
    if isinstance(steps_inline, list):  
        cfg["STEPS"] = steps_inline   
  
    # Call PIPE  
    pipe_fn, pipe_label = _find_pipe_entrypoint()  
    pipe_result: Any = _call_pipeline(  
        pipe_fn, cfg=cfg, steps=steps_out, steps_path=steps_path, workflow_path=wf_path  
    )  
  
    # Normalize PIPE result shapes:  
    # - PIPE-1E run_pipeline(cfg) -> (summary_dict, exit_code)  
    # - other entrypoints may return summary_dict directly  
    pipe_summary: Dict[str, Any] = {}  
    exit_code: Optional[int] = None  
  
    if (  
        isinstance(pipe_result, tuple)  
        and len(pipe_result) == 2  
        and isinstance(pipe_result[0], dict)  
        and isinstance(pipe_result[1], int)  
    ):  
        pipe_summary = pipe_result[0]  
        exit_code = pipe_result[1]  
    elif isinstance(pipe_result, dict):  
        pipe_summary = pipe_result  
        if isinstance(pipe_summary.get("exit_code"), int):  
            exit_code = int(pipe_summary["exit_code"])  
  
    # Normalize summary fields for CLI  
    errors: List[Any] = []  
    artifacts: List[Any] = []  
    success: bool  
  
    steps_inline = steps_out.get("steps") if isinstance(steps_out, dict) else steps_out  
    steps_executed = len(steps_inline) if isinstance(steps_inline, list) else 0  
  
    if isinstance(pipe_summary.get("errors"), list):  
        errors = pipe_summary["errors"]  
  
    # PIPE fatal errors are often a single string under "error"  
    if not errors and isinstance(pipe_summary.get("error"), str) and pipe_summary.get("error"):  
        errors = [pipe_summary["error"]]   
    if isinstance(pipe_summary.get("artifacts"), list):  
        artifacts = pipe_summary["artifacts"]  
  
    # Success resolution order: explicit bools -> failed count -> exit_code -> errors fallback  
    if isinstance(pipe_summary.get("success"), bool):  
        success = bool(pipe_summary["success"])  
    elif isinstance(pipe_summary.get("ok"), bool):  
        success = bool(pipe_summary["ok"])  
    elif isinstance(pipe_summary.get("failed"), int):  
        success = int(pipe_summary["failed"]) == 0  
    elif isinstance(exit_code, int):  
        success = exit_code == 0  
    else:  
        success = (len(errors) == 0)  
  
    summary = {  
        "workflow": workflow_norm.get("name"),  
        "run_id": run_id,  
        "steps_executed": steps_executed,  
        "success": bool(success),  
        "errors": errors,  
        "artifacts": artifacts,  
        "pipe_entrypoint": pipe_label,  
    }  
    if exit_code is not None:  
        summary["exit_code"] = int(exit_code)  
    if isinstance(pipe_summary.get("step_logs"), list):  
        summary["step_logs"] = pipe_summary["step_logs"]  
         
    return summary  