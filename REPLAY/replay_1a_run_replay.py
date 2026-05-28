# REPLAY/replay_1a_run_replay.py  
"""  
REPLAY-1A — Deterministic Run Replayer  
  
Replays (or plans) a previous workflow run using SNAP-1A artifacts.  
  
Public API:  
  replay_run(run_id: str, *, artifacts_dir="artifacts", override_cfg=None, dry_run=False) -> dict  
"""  
  
from __future__ import annotations  
  
import json  
from pathlib import Path  
from typing import Any, Callable, Dict, List, Optional, Tuple  
  
__all__ = [  
    "replay_run",  
]  
  
  
def _read_json(path: Path) -> dict:  
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))  
  
  
def _shallow_merge(base: dict, overrides: Optional[dict]) -> dict:  
    out = dict(base) if isinstance(base, dict) else {}  
    if isinstance(overrides, dict):  
        for k, v in overrides.items():  
            out[k] = v  
    return out  
  
  
def _extract_cfg_snapshot(failure: dict) -> Tuple[dict, List[str]]:  
    notes: List[str] = []  
    extra = failure.get("extra") if isinstance(failure, dict) else None  
    if not isinstance(extra, dict):  
        notes.append("No extra field found in failure.json; cfg snapshot unavailable.")  
        return {}, notes  
  
    for k in ("cfg", "cfg_snapshot", "config", "runtime_cfg"):  
        v = extra.get(k)  
        if isinstance(v, dict):  
            notes.append(f"Using cfg snapshot from failure.json extra['{k}'].")  
            return v, notes  
  
    notes.append("No cfg snapshot keys found in failure.json extra; using empty cfg.")  
    return {}, notes  
  
  
def _resolve_workflow_path_via_workflow_1a(workflow_name: str) -> Tuple[Optional[Path], List[str]]:  
    """  
    Best-effort resolver that prefers WORKFLOW-1A loader/registry if present.  
    Falls back to conventional locations if not.  
    """  
    notes: List[str] = []  
    wn = (workflow_name or "").strip()  
    if not wn:  
        return None, ["workflow_name missing/empty in failure.json"]  
  
    # If it already looks like a path, accept it.  
    maybe_path = Path(wn)  
    if maybe_path.suffix.lower() in {".json", ".yaml", ".yml"}:  
        if maybe_path.exists():  
            notes.append("workflow_name looked like a path; using it directly.")  
            return maybe_path.resolve(), notes  
  
    # Try WORKFLOW-1A functions (best-effort; deterministic attempts).  
    candidates: List[Tuple[str, str]] = [  
        ("WORKFLOW.workflow_1a_loader", "resolve_workflow_path"),  
        ("WORKFLOW.workflow_1a_loader", "get_workflow_path"),  
        ("WORKFLOW.workflow_1a_registry", "resolve_workflow_path"),  
        ("WORKFLOW.workflow_1a_registry", "get_workflow_path"),  
        ("WORKFLOW.workflow_1a_load", "resolve_workflow_path"),  
    ]  
    for mod_name, fn_name in candidates:  
        try:  
            mod = __import__(mod_name, fromlist=[fn_name])  
            fn = getattr(mod, fn_name, None)  
            if callable(fn):  
                p = fn(wn)  # type: ignore[misc]  
                if isinstance(p, (str, Path)):  
                    pp = Path(p)  
                    if pp.exists():  
                        notes.append(f"Resolved workflow path via {mod_name}.{fn_name}().")  
                        return pp.resolve(), notes  
        except Exception as e:  
            notes.append(f"Resolver attempt failed: {mod_name}.{fn_name}: {type(e).__name__}")  
  
    # Fallback: conventional workflows directory  
    for ext in (".json", ".yaml", ".yml"):  
        p = Path("workflows") / f"{wn}{ext}"  
        if p.exists():  
            notes.append(f"Resolved workflow via fallback path: {p.as_posix()}")  
            return p.resolve(), notes  
  
    # Fallback: exact name under workflows/  
    p2 = Path("workflows") / wn  
    if p2.exists():  
        notes.append(f"Resolved workflow via fallback path: {p2.as_posix()}")  
        return p2.resolve(), notes  
  
    notes.append("Could not resolve workflow path using WORKFLOW-1A or fallback conventions.")  
    return None, notes  
  
  
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
  
  
def _call_run_workflow(run_workflow: Callable[..., Any], workflow_path: Path, cfg: dict, replay_run_id: str) -> Any:  
    """  
    Try a small set of common RUN-1A call shapes without refactoring existing modules.  
    Deterministic order; re-raises if none match.  
    """  
    attempts = [  
        ((), {"workflow_path": str(workflow_path), "cfg": cfg, "run_id": replay_run_id}),  
        ((str(workflow_path),), {"cfg": cfg, "run_id": replay_run_id}),  
        ((), {"workflow": str(workflow_path), "cfg": cfg, "run_id": replay_run_id}),  
        ((str(workflow_path), cfg), {"run_id": replay_run_id}),  
        ((str(workflow_path),), {}),  
    ]  
    last: Optional[Exception] = None  
    for a, kw in attempts:  
        try:  
            return run_workflow(*a, **kw)  
        except TypeError as e:  
            last = e  
            continue  
    if last is not None:  
        raise last  
    return run_workflow(str(workflow_path))  
  
  
def replay_run(  
    run_id: str,  
    *,  
    artifacts_dir: str | Path = "artifacts",  
    override_cfg: dict | None = None,  
    dry_run: bool = False,  
) -> dict:  
    rid = (run_id or "").strip()  
    if not rid:  
        raise ValueError("run_id must be a non-empty string")  
  
    base = Path(artifacts_dir) / rid  
    failure_path = base / "failure.json"  
    if not failure_path.exists():  
        raise ValueError(f"Missing failure.json: {failure_path.as_posix()}")  
  
    failure = _read_json(failure_path)  
  
    workflow_name = failure.get("workflow_name") if isinstance(failure, dict) else None  
    step_index = failure.get("step_index") if isinstance(failure, dict) else None  
    action = failure.get("action") if isinstance(failure, dict) else None  
  
    cfg0, cfg_notes = _extract_cfg_snapshot(failure)  
    cfg = _shallow_merge(cfg0, override_cfg)  
  
    wf_path, wf_notes = _resolve_workflow_path_via_workflow_1a(str(workflow_name or ""))  
  
    notes: List[str] = []  
    notes.extend(cfg_notes)  
    notes.extend(wf_notes)  
  
    replay_id = f"{rid}__replay"  
  
    if wf_path is None:  
        return {  
            "run_id": replay_id,  
            "replay_of": rid,  
            "workflow": None,  
            "success": False,  
            "steps_executed": 0,  
            "notes": notes + ["Replay aborted: workflow could not be resolved."],  
        }  
  
    if dry_run:  
        plan = {  
            "replay_of": rid,  
            "replay_run_id": replay_id,  
            "workflow_path": str(wf_path),  
            "workflow_name": workflow_name,  
            "failing_step_index": step_index,  
            "failing_action": action,  
            "cfg_effective_keys": sorted(list(cfg.keys())) if isinstance(cfg, dict) else [],  
        }  
        print("REPLAY-1A dry_run plan:")  
        print(json.dumps(plan, indent=2, sort_keys=True))  
        return {  
            "run_id": replay_id,  
            "replay_of": rid,  
            "workflow": str(wf_path),  
            "success": True,  
            "steps_executed": 0,  
            "notes": notes + ["dry_run=true (no execution performed)"],  
        }  
  
    run_workflow = _import_run_workflow()  
    result = _call_run_workflow(run_workflow, wf_path, cfg, replay_id)  
  
    # Normalize output  
    steps_executed = 0  
    success = True  
    if isinstance(result, dict):  
        # common patterns  
        if isinstance(result.get("steps_executed"), int):  
            steps_executed = int(result["steps_executed"])  
        if isinstance(result.get("success"), bool):  
            success = bool(result["success"])  
  
    return {  
        "run_id": replay_id,  
        "replay_of": rid,  
        "workflow": str(wf_path),  
        "success": bool(success),  
        "steps_executed": int(steps_executed),  
        "notes": notes,  
    }  