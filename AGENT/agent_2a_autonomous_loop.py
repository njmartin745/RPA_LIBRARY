"""  
AGENT-2A — Autonomous Execution Loop (orchestration only)  
  
Coordinates: RUN → (on failure) SNAP → REASON → HEAL → retry → (on success) REPORT  
Then runs LEARN analysis over HISTORY to produce recommendations.  
  
Constraints:  
- No direct Selenium logic here (delegates to existing modules).  
- Deterministic behavior (no randomness).  
- Additive module; does not modify existing modules.  
"""  
  
from __future__ import annotations  
  
import copy  
import importlib  
import json  
from pathlib import Path  
from typing import Any, Callable, Dict, List, Optional, Tuple  
  
from LEARN.learn_1a_failure_patterns import (  
    extract_failure_patterns,  
    generate_recommendations,  
    load_history,  
    rank_patterns,  
)  
  
__all__ = [  
    "run_autonomous",  
]  
  
  
# -----------------------  
# generic resolution / calls  
# -----------------------  
  
def _resolve_callable(module_path: str, candidate_names: Tuple[str, ...]) -> Optional[Callable[..., Any]]:  
    try:  
        mod = importlib.import_module(module_path)  
    except Exception:  
        return None  
    for name in candidate_names:  
        fn = getattr(mod, name, None)  
        if callable(fn):  
            return fn  
    return None  
  
  
def _call_with_fallbacks(fn: Callable[..., Any], attempts: List[Tuple[tuple, dict]]) -> Any:  
    last_err: Optional[Exception] = None  
    for args, kwargs in attempts:  
        try:  
            return fn(*args, **kwargs)  
        except TypeError as e:  
            last_err = e  
            continue  
    if last_err:  
        raise last_err  
    return fn()  
  
  
def _append_jsonl(path: Path, row: Dict[str, Any]) -> None:  
    path.parent.mkdir(parents=True, exist_ok=True)  
    with path.open("a", encoding="utf-8") as f:  
        f.write(json.dumps(row, ensure_ascii=False) + "\n")  
  
  
def _ensure_path(p: str | Path) -> Path:  
    return p if isinstance(p, Path) else Path(p)  
  
  
def _normalize_run_result(run_result: Any, *, attempt: int) -> Dict[str, Any]:  
    if isinstance(run_result, dict):  
        out = dict(run_result)  
    else:  
        out = {"raw_result": run_result}  
  
    # Normalize keys we rely on  
    if "success" not in out:  
        # common alternatives  
        if isinstance(out.get("ok"), bool):  
            out["success"] = bool(out["ok"])  
        elif isinstance(out.get("status"), str):  
            out["success"] = out["status"].lower() in {"ok", "success", "passed"}  
        else:  
            out["success"] = False  
  
    if not out.get("run_id"):  
        out["run_id"] = f"attempt-{attempt}"  
  
    return out  
  
  
def _default_fns() -> Dict[str, Callable[..., Any]]:  
    """  
    Resolve default functions from existing milestone modules.  
    Resolution is lazy and best-effort; orchestrator can be fully driven by cfg overrides.  
    """  
    run_fn = _resolve_callable(  
        "RUN.run_1a_workflow_runner",  
        ("run_workflow", "run", "run_workflow_runner"),  
    )  
    snap_fn = _resolve_callable(  
        "SNAP.snap_1a_capture",  
        ("capture_snap", "capture", "snap_capture"),  
    )  
    reason_fn = _resolve_callable(  
        "REASON.reason_1a_diagnose",  
        ("diagnose", "run_diagnose", "reason_diagnose"),  
    )  
    heal_fn = _resolve_callable(  
        "HEAL.heal_1a_patch_workflow",  
        ("generate_patch", "patch_workflow", "heal_patch_workflow"),  
    )  
    report_fn = _resolve_callable(  
        "REPORT.report_1a_generate",  
        ("generate_report", "build_report", "report_generate"),  
    )  
    history_fn = _resolve_callable(  
        "HISTORY.history_1a_store",  
        ("append_row", "append_history", "record_run", "store_row", "write_row"),  
    )  
  
    fns: Dict[str, Callable[..., Any]] = {}  
    if run_fn:  
        fns["run_fn"] = run_fn  
    if snap_fn:  
        fns["snap_fn"] = snap_fn  
    if reason_fn:  
        fns["reason_fn"] = reason_fn  
    if heal_fn:  
        fns["heal_fn"] = heal_fn  
    if report_fn:  
        fns["report_fn"] = report_fn  
    if history_fn:  
        fns["history_fn"] = history_fn  
    return fns  
  
  
def _write_patched_workflow(  
    patch_obj: Dict[str, Any],  
    *,  
    base_workflow_path: Path,  
    attempt: int,  
    out_dir: Path,  
) -> Path:  
    """  
    Create a patched workflow file deterministically.  
    Accepts either:  
      - patch_obj["patched_workflow"] (dict)  
      - patch_obj["workflow"] (dict)  
      - patch_obj itself  
    """  
    out_dir.mkdir(parents=True, exist_ok=True)  
    stem = base_workflow_path.stem or "workflow"  
    patched_path = out_dir / f"{stem}.patched.attempt_{attempt}.json"  
  
    content = (  
        patch_obj.get("patched_workflow")  
        if isinstance(patch_obj.get("patched_workflow"), dict)  
        else patch_obj.get("workflow")  
        if isinstance(patch_obj.get("workflow"), dict)  
        else patch_obj  
    )  
  
    patched_path.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")  
    return patched_path  
  
  
# -----------------------  
# public orchestration API  
# -----------------------  
  
def run_autonomous(  
    workflow_path: str | Path,  
    *,  
    max_attempts: int = 3,  
    cfg: Dict[str, Any] | None = None,  
) -> Dict[str, Any]:  
    cfg = copy.deepcopy(cfg or {})  
    wf_path = _ensure_path(workflow_path)  
  
    # Allow overrides (for tests / deterministic simulation)  
    # Supported override keys: run_fn, snap_fn, reason_fn, heal_fn, report_fn, history_fn  
    resolved = _default_fns()  
    for k in ("run_fn", "snap_fn", "reason_fn", "heal_fn", "report_fn", "history_fn"):  
        if callable(cfg.get(k)):  
            resolved[k] = cfg[k]  
  
    history_path = _ensure_path(cfg.get("history_path", "history/run_history.jsonl"))  
    patched_dir = _ensure_path(cfg.get("patched_workflows_dir", ".dev_tmp/patched_workflows"))  
  
    run_ids: List[str] = []  
    patches_applied: List[Dict[str, Any]] = []  
    final_report: Optional[str] = None  
    success = False  
  
    current_wf_path = wf_path  
  
    for attempt in range(1, max_attempts + 1):  
        print(f"[AGENT-2A] attempt={attempt}/{max_attempts} workflow={current_wf_path}")  
  
        if "run_fn" not in resolved:  
            raise RuntimeError("AGENT-2A: RUN-1A callable not resolved and no cfg['run_fn'] override provided.")  
  
        run_raw = _call_with_fallbacks(  
            resolved["run_fn"],  
            attempts=[  
                ((str(current_wf_path),), {"cfg": cfg}),  
                ((str(current_wf_path), cfg), {}),  
                ((str(current_wf_path),), {}),  
                ((), {"workflow_path": str(current_wf_path), "cfg": cfg}),  
            ],  
        )  
        run_result = _normalize_run_result(run_raw, attempt=attempt)  
        run_id = str(run_result.get("run_id"))  
        run_ids.append(run_id)  
  
        # Record history (best effort; fallback to JSONL append)  
        history_row = {  
            "run_id": run_id,  
            "workflow_path": str(current_wf_path),  
            "workflow_name": cfg.get("workflow_name") or wf_path.stem,  
            "attempt": attempt,  
            "status": "success" if run_result.get("success") else "failed",  
            "error_category": run_result.get("error_category") or run_result.get("failure_category"),  
            "selector_ref": run_result.get("selector_ref"),  
            "diff_fingerprint": run_result.get("diff_fingerprint"),  
        }  
        if "history_fn" in resolved:  
            try:  
                _call_with_fallbacks(  
                    resolved["history_fn"],  
                    attempts=[  
                        ((history_row,), {"history_path": str(history_path)}),  
                        ((history_row,), {}),  
                        ((), {"row": history_row, "history_path": str(history_path)}),  
                        ((), {"row": history_row}),  
                    ],  
                )  
            except Exception:  
                _append_jsonl(history_path, history_row)  
        else:  
            _append_jsonl(history_path, history_row)  
  
        if run_result.get("success") is True:  
            success = True  
            print(f"[AGENT-2A] run_id={run_id} SUCCESS")  
  
            if "report_fn" in resolved:  
                try:  
                    rep = _call_with_fallbacks(  
                        resolved["report_fn"],  
                        attempts=[  
                            ((run_result,), {"cfg": cfg}),  
                            ((run_result,), {}),  
                            ((run_id,), {"cfg": cfg}),  
                            ((run_id,), {}),  
                        ],  
                    )  
                    final_report = rep if isinstance(rep, str) else json.dumps(rep, ensure_ascii=False)  
                except Exception as e:  
                    final_report = f"(report generation failed) {type(e).__name__}: {e}"  
            break  
  
        # Failure path  
        print(f"[AGENT-2A] run_id={run_id} FAILURE")  
  
        if "snap_fn" in resolved:  
            try:  
                _call_with_fallbacks(  
                    resolved["snap_fn"],  
                    attempts=[  
                        ((run_result,), {"cfg": cfg}),  
                        ((run_result,), {}),  
                        ((), {"run_result": run_result, "cfg": cfg}),  
                    ],  
                )  
            except Exception:  
                pass  
  
        diagnosis: Dict[str, Any] = {}  
        if "reason_fn" in resolved:  
            try:  
                diag_raw = _call_with_fallbacks(  
                    resolved["reason_fn"],  
                    attempts=[  
                        ((run_result,), {"cfg": cfg}),  
                        ((run_result,), {}),  
                        ((run_id,), {"cfg": cfg}),  
                        ((run_id,), {}),  
                    ],  
                )  
                if isinstance(diag_raw, dict):  
                    diagnosis = diag_raw  
                else:  
                    diagnosis = {"raw_diagnosis": diag_raw}  
            except Exception as e:  
                diagnosis = {"reason_error": f"{type(e).__name__}: {e}"}  
  
        patch_obj: Optional[Dict[str, Any]] = None  
        if "heal_fn" in resolved:  
            try:  
                patch_raw = _call_with_fallbacks(  
                    resolved["heal_fn"],  
                    attempts=[  
                        ((str(current_wf_path), diagnosis), {"cfg": cfg}),  
                        ((str(current_wf_path),), {"diagnosis": diagnosis, "cfg": cfg}),  
                        ((), {"workflow_path": str(current_wf_path), "diagnosis": diagnosis, "cfg": cfg}),  
                        ((str(current_wf_path), diagnosis), {}),  
                        ((), {"workflow_path": str(current_wf_path), "diagnosis": diagnosis}),  
                    ],  
                )  
                if isinstance(patch_raw, dict):  
                    patch_obj = patch_raw  
            except Exception:  
                patch_obj = None  
  
        if patch_obj:  
            # Prefer explicit patched path  
            patched_path_val = patch_obj.get("patched_workflow_path") or patch_obj.get("workflow_path")  
            if patched_path_val:  
                current_wf_path = _ensure_path(patched_path_val)  
                patches_applied.append(  
                    {"attempt": attempt, "run_id": run_id, "patched_workflow_path": str(current_wf_path)}  
                )  
                print(f"[AGENT-2A] patch applied: {current_wf_path}")  
            else:  
                # If heal returned a patched workflow object, serialize it.  
                current_wf_path = _write_patched_workflow(  
                    patch_obj,  
                    base_workflow_path=wf_path,  
                    attempt=attempt,  
                    out_dir=patched_dir,  
                )  
                patches_applied.append(  
                    {"attempt": attempt, "run_id": run_id, "patched_workflow_path": str(current_wf_path)}  
                )  
                print(f"[AGENT-2A] patch materialized: {current_wf_path}")  
        else:  
            print("[AGENT-2A] no patch available; retrying without patch")  
  
    # Learning pass (always runs)  
    rows = load_history(history_path)  
    patterns = extract_failure_patterns(rows)  
    ranked = rank_patterns(patterns)  
    recommendations = generate_recommendations(ranked)  
  
    return {  
        "success": bool(success),  
        "attempts": len(run_ids),  
        "run_ids": run_ids,  
        "final_report": final_report,  
        "patches_applied": patches_applied,  
        "recommendations": recommendations,  
    }  