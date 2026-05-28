# CLI/cli_pack_1a.py  
"""  
PACK-1A — Golden-Path CLI (one-command framework usage)  
  
CLI commands:  
- run <workflow_path>        -> calls RUN-1A  
- report <run_id>            -> calls REPORT-1A  
- replay <run_id>            -> calls REPLAY-1A  
- heal <workflow_path> --from-run <run_id> -> loads diagnosis from artifacts/<run_id>, calls HEAL-1A patch generator  
- doctor                     -> calls DOCTOR-1A  
- history                    -> prints summary from HISTORY-1A  
  
Rules:  
- Orchestrate existing modules; do not re-implement their core logic.  
- Human readable output; no stack traces unless failure (or --debug).  
- Exit code 0 on success; 1 on failure.  
"""  
  
from __future__ import annotations  
  
import argparse  
import json  
import os  
import sys  
import traceback  
from pathlib import Path  
from typing import Any, Callable, Optional, Tuple  
  
__all__ = ["main"]  
  
  
# ---------- import helpers (best-effort, additive) ----------  
  
def _import_fn(candidates: list[tuple[str, str]]) -> Callable[..., Any]:  
    last_err: Optional[Exception] = None  
    for mod_name, fn_name in candidates:  
        try:  
            mod = __import__(mod_name, fromlist=[fn_name])  
            fn = getattr(mod, fn_name, None)  
            if callable(fn):  
                return fn  
        except Exception as e:  
            last_err = e  
    raise ValueError(f"Could not import function from candidates: {candidates}. Last error: {last_err}")  
  
  
def _run_workflow_fn() -> Callable[..., Any]:  
    return _import_fn(  
        [  
            ("RUN.run_1a_workflow_runner", "run_workflow"),  
            ("RUN.run_1a_run_workflow", "run_workflow"),  
            ("RUN.run_1a_runner", "run_workflow"),  
            ("RUN.run_1a", "run_workflow"),  
        ]  
    )  
  
  
def _generate_report_fn() -> Callable[..., Any]:  
    return _import_fn(  
        [  
            ("REPORT.report_1a_generate", "generate_report"),  
            ("REPORT.report_1a_report", "generate_report"),  
            ("REPORT.report_1a", "generate_report"),  
        ]  
    )  
  
  
def _replay_fn() -> Callable[..., Any]:  
    return _import_fn(  
        [  
            ("REPLAY.replay_1a_run", "replay_run"),  
            ("REPLAY.replay_1a_replay", "replay_run"),  
            ("REPLAY.replay_1a", "replay_run"),  
            ("REPLAY.replay_1a_run", "main"),  # fallback  
        ]  
    )  
  
  
def _heal_patch_fn() -> Callable[..., Any]:  
    return _import_fn(  
        [  
            ("HEAL.heal_1a_patch_generator", "generate_patch"),  
            ("HEAL.heal_1a_generate_patch", "generate_patch"),  
            ("HEAL.heal_1a", "generate_patch"),  
        ]  
    )  
  
  
def _doctor_fns() -> tuple[Callable[..., Any], Callable[..., Any]]:  
    run_preflight = _import_fn([("DOCTOR.doctor_1a_check", "run_preflight")])  
    format_report = _import_fn([("DOCTOR.doctor_1a_check", "format_preflight_report")])  
    return run_preflight, format_report  
  
  
def _history_fns() -> tuple[Callable[..., Any], Callable[..., Any]]:  
    read_run_history = _import_fn([("HISTORY.history_1a_store", "read_run_history")])  
    summarize_history = _import_fn([("HISTORY.history_1a_store", "summarize_history")])  
    return read_run_history, summarize_history  
  
  
# ---------- utilities ----------  
  
def _load_cfg(cfg_json: Optional[str]) -> dict:  
    if not cfg_json:  
        return {}  
    p = Path(cfg_json)  
    obj = json.loads(p.read_text(encoding="utf-8"))  
    if not isinstance(obj, dict):  
        raise ValueError(f"--cfg-json must contain a JSON object (dict). Got: {type(obj).__name__}")  
    return obj  
  
  
def _print_err(msg: str) -> None:  
    print(msg, file=sys.stderr)  
  
  
def _short_exc(e: BaseException) -> str:  
    return f"{type(e).__name__}: {e}" if str(e) else type(e).__name__  
  
  
def _try_call_run_workflow(run_workflow: Callable[..., Any], workflow_path: str, cfg: dict) -> Any:  
    """  
    Best-effort calling patterns to avoid refactors/assumptions about RUN-1A signature.  
    """  
    # Try common signatures  
    try:  
        return run_workflow(workflow_path, cfg=cfg)  
    except TypeError:  
        pass  
    try:  
        return run_workflow(workflow_path=workflow_path, cfg=cfg)  
    except TypeError:  
        pass  
    try:  
        return run_workflow(workflow_path, cfg)  
    except TypeError:  
        pass  
    # Last resort: no cfg kw  
    return run_workflow(workflow_path)  
  
  
def _infer_run_id(result: Any) -> Optional[str]:  
    if isinstance(result, dict):  
        rid = result.get("run_id") or result.get("id")  
        if isinstance(rid, str) and rid.strip():  
            return rid.strip()  
    return None  
  
  
def _infer_artifacts_path(result: Any, run_id: Optional[str]) -> Optional[str]:  
    if isinstance(result, dict):  
        for k in ("artifacts_dir", "artifacts_path", "artifacts"):  
            v = result.get(k)  
            if isinstance(v, str) and v.strip():  
                return v.strip()  
    if run_id:  
        return str(Path("artifacts") / run_id)  
    return None  
  
  
def _load_diagnosis_from_artifacts(run_id: str) -> dict:  
    """  
    Best-effort: loads a diagnosis-like JSON file from artifacts/<run_id>/.  
    """  
    base = Path("artifacts") / run_id  
    candidates = [  
        base / "diagnosis.json",  
        base / "reason.json",  
        base / "failure.json",  
        base / "report.json",  
    ]  
    for p in candidates:  
        if p.exists() and p.is_file():  
            try:  
                obj = json.loads(p.read_text(encoding="utf-8"))  
                if isinstance(obj, dict):  
                    return obj  
            except Exception:  
                continue  
    raise FileNotFoundError(  
        f"Could not find a diagnosis JSON under {base.as_posix()} (tried: {', '.join([c.name for c in candidates])})"  
    )  
  
  
# ---------- command handlers ----------  
  
def _cmd_doctor(args: argparse.Namespace) -> int:  
    run_preflight, format_report = _doctor_fns()  
    res = run_preflight(root=".", strict=bool(args.strict), cfg=None)  
    txt = format_report(res)  
    print(txt.rstrip())  
    return 0 if res.get("ok") is True else 1  
  
  
def _cmd_history(args: argparse.Namespace) -> int:  
    read_run_history, summarize_history = _history_fns()  
    rows = read_run_history(history_path=args.history_path, limit=int(args.limit))  
    summ = summarize_history(rows)  
  
    print("HISTORY Summary")  
    print(f"- total_runs: {summ.get('total_runs')}")  
    print(f"- success_rate: {summ.get('success_rate')}")  
    print(f"- last_run_ts: {summ.get('last_run_ts')}")  
    print("- top_workflows:")  
    for it in (summ.get("top_workflows") or [])[:10]:  
        print(f"  - {it.get('workflow')}: {it.get('count')}")  
    print("- top_failure_categories:")  
    for it in (summ.get("top_failure_categories") or [])[:10]:  
        print(f"  - {it.get('category')}: {it.get('count')}")  
    return 0  
  
  
def _cmd_run(args: argparse.Namespace) -> int:  
    run_workflow = _run_workflow_fn()  
    cfg = _load_cfg(args.cfg_json)  
  
    if args.dry_run:  
        # Pass-through to RUN-1A if it supports dry-run; still a RUN-1A call.  
        cfg = dict(cfg)  
        cfg.setdefault("DRY_RUN", True)  
  
    workflow_path = args.workflow_path  
    if not Path(workflow_path).exists():  
        _print_err(f"Workflow not found: {workflow_path}")  
        return 1  
  
    result = _try_call_run_workflow(run_workflow, workflow_path, cfg)  
    run_id = _infer_run_id(result)  
    artifacts_path = _infer_artifacts_path(result, run_id)  
  
    print("RUN complete")  
    if run_id:  
        print(f"- run_id: {run_id}")  
    if artifacts_path:  
        print(f"- artifacts: {artifacts_path}")  
    return 0  
  
  
def _cmd_report(args: argparse.Namespace) -> int:  
    generate_report = _generate_report_fn()  
    run_id = args.run_id.strip()  
  
    # Try common call styles  
    try:  
        res = generate_report(run_id)  
    except TypeError:  
        res = generate_report(run_id=run_id)  
  
    report_dir = None  
    if isinstance(res, dict):  
        report_dir = res.get("reports_dir") or res.get("report_dir") or res.get("out_dir")  
    if not report_dir:  
        report_dir = str(Path("reports") / run_id)  
  
    print("REPORT generated")  
    print(f"- report_dir: {report_dir}")  
    return 0  
  
  
def _cmd_replay(args: argparse.Namespace) -> int:  
    replay_run = _replay_fn()  
    run_id = args.run_id.strip()  
  
    try:  
        res = replay_run(run_id)  
    except TypeError:  
        res = replay_run(run_id=run_id)  
  
    print("REPLAY complete")  
    if isinstance(res, dict) and res.get("run_id"):  
        print(f"- run_id: {res.get('run_id')}")  
    else:  
        print(f"- run_id: {run_id}")  
    return 0  
  
  
def _cmd_heal(args: argparse.Namespace) -> int:  
    generate_patch = _heal_patch_fn()  
    workflow_path = args.workflow_path  
    from_run = args.from_run.strip()  
  
    if not Path(workflow_path).exists():  
        _print_err(f"Workflow not found: {workflow_path}")  
        return 1  
  
    diagnosis = _load_diagnosis_from_artifacts(from_run)  
  
    # Try common call patterns  
    try:  
        patch = generate_patch(workflow_path=workflow_path, diagnosis=diagnosis, run_id=from_run)  
    except TypeError:  
        try:  
            patch = generate_patch(workflow_path, diagnosis, from_run)  
        except TypeError:  
            patch = generate_patch(workflow_path=workflow_path, diagnosis=diagnosis)  
  
    patch_path = None  
    if isinstance(patch, dict):  
        patch_path = patch.get("patch_path") or patch.get("path")  
    if isinstance(patch, str):  
        patch_path = patch  
  
    print("HEAL patch generated")  
    if patch_path:  
        print(f"- patch_path: {patch_path}")  
    else:  
        print("- patch_path: (unknown)")  
    return 0  
  
  
# ---------- argparse / main ----------  
  
def main(argv: Optional[list[str]] = None) -> int:  
    parser = argparse.ArgumentParser(prog="pack", description="PACK-1A Golden-Path CLI")  
    parser.add_argument("--debug", action="store_true", help="Print stack traces on failure.")  
  
    sub = parser.add_subparsers(dest="cmd", required=True)  
  
    p_run = sub.add_parser("run", help="Run a workflow via RUN-1A")  
    p_run.add_argument("workflow_path", help="Path to workflow JSON")  
    p_run.add_argument("--cfg-json", default=None, help="Path to JSON config object passed to RUN-1A")  
    p_run.add_argument("--dry-run", action="store_true", help="Request dry-run mode (passes cfg DRY_RUN=true to RUN-1A)")  
    p_run.set_defaults(_handler=_cmd_run)  
  
    p_report = sub.add_parser("report", help="Generate report for a run via REPORT-1A")  
    p_report.add_argument("run_id", help="Run id")  
    p_report.set_defaults(_handler=_cmd_report)  
  
    p_replay = sub.add_parser("replay", help="Replay a run via REPLAY-1A")  
    p_replay.add_argument("run_id", help="Run id")  
    p_replay.set_defaults(_handler=_cmd_replay)  
  
    p_heal = sub.add_parser("heal", help="Generate heal patch via HEAL-1A using artifacts from a prior run")  
    p_heal.add_argument("workflow_path", help="Path to workflow JSON to patch")  
    p_heal.add_argument("--from-run", required=True, dest="from_run", help="Run id to load diagnosis from artifacts/<run_id>/")  
    p_heal.set_defaults(_handler=_cmd_heal)  
  
    p_doctor = sub.add_parser("doctor", help="Run preflight checks via DOCTOR-1A")  
    p_doctor.add_argument("--strict", action="store_true", help="Treat warnings as failures")  
    p_doctor.set_defaults(_handler=_cmd_doctor)  
  
    p_hist = sub.add_parser("history", help="Show run history summary via HISTORY-1A")  
    p_hist.add_argument("--history-path", default="history/run_history.jsonl", help="Path to run history JSONL")  
    p_hist.add_argument("--limit", type=int, default=200, help="Read last N rows")  
    p_hist.set_defaults(_handler=_cmd_history)  
  
    args = parser.parse_args(argv)  
  
    try:  
        return int(args._handler(args))  
    except SystemExit:  
        raise  
    except Exception as e:  
        _print_err(f"FAIL: {_short_exc(e)}")  
        if getattr(args, "debug", False):  
            _print_err(traceback.format_exc())  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  