"""  
CLI-2B — Unified Automation Command Interface (orchestration only)  
  
Commands:  
- auto <natural_language>   -> BUILD-2C (build bundle) then optional AGENT-2A run  
- run <workflow_path>       -> RUN-1A (best effort)  
- doctor                    -> DOCTOR-1A (best effort)  
- history                   -> print history summary (reads jsonl)  
- replay <run_id>           -> REPLAY-1A (best effort)  
- report <run_id>           -> REPORT-1A (best effort)  
  
UX constraints:  
- no stack traces shown to user  
- clear success/failure messages  
"""  
  
from __future__ import annotations  
  
import argparse  
import importlib  
import json  
import os  
import sys  
import tempfile  
from pathlib import Path  
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple  
  
__all__ = ["main"]  
  
  
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
  
  
def _call_with_fallbacks(fn: Callable[..., Any], attempts: Sequence[Tuple[tuple, dict]]) -> Any:  
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
  
  
def _safe_json(x: Any) -> str:  
    try:  
        return json.dumps(x, indent=2, ensure_ascii=False)  
    except Exception:  
        return str(x)  
  
  
def _print_header(title: str) -> None:  
    print(f"== {title} ==")  
  
  
def _ensure_path(p: str | Path) -> Path:  
    return p if isinstance(p, Path) else Path(p)  
  
  
# ----------------------------  
# Step log helpers (CLI-side passthrough/augmentation)  
# ----------------------------  
  
  
def _ensure_cli_log_path_in_cfg(cfg: Dict[str, Any]) -> Optional[str]:  
    """  
    Ensure a deterministic-to-locate LOG_PATH so the runner/pipeline has a place to write JSONL.  
    This allows CLI to read the file post-run and attach step_logs even if RUN-1A drops them.  
    """  
    v = cfg.get("LOG_PATH") or cfg.get("LOG_JSONL_PATH")  
    if isinstance(v, str) and v.strip():  
        cfg.setdefault("LOG_PATH", v.strip())  
        cfg.setdefault("LOG_JSONL_PATH", v.strip())  
        return v.strip()  
  
    try:  
        fd, p = tempfile.mkstemp(prefix="cli_2b_run_log_", suffix=".jsonl")  
        os.close(fd)  
        cfg["LOG_PATH"] = p  
        cfg["LOG_JSONL_PATH"] = p  
        return p  
    except Exception:  
        return None  
  
  
def _load_workflow_steps(workflow_path: str) -> List[Dict[str, Any]]:  
    """  
    Best-effort extraction of steps from a workflow JSON file.  
    Supports common shapes:  
      - {"steps": [...]}  
      - {"workflow": {..., "steps":[...]}}  
    """  
    p = Path(workflow_path)  
    data = json.loads(p.read_text(encoding="utf-8"))  
  
    if isinstance(data, dict) and isinstance(data.get("steps"), list):  
        steps = data["steps"]  
        return [s for s in steps if isinstance(s, dict)]  
  
    wf = data.get("workflow") if isinstance(data, dict) else None  
    if isinstance(wf, dict) and isinstance(wf.get("steps"), list):  
        steps = wf["steps"]  
        return [s for s in steps if isinstance(s, dict)]  
  
    return []  
  
  
def _read_jsonl_events(path: Optional[str]) -> List[Dict[str, Any]]:  
    events: List[Dict[str, Any]] = []  
    if not path or not isinstance(path, str) or not path.strip():  
        return events  
    p = path.strip()  
    if not os.path.exists(p):  
        return events  
  
    try:  
        with open(p, "r", encoding="utf-8", errors="replace") as f:  
            for line in f:  
                s = line.strip()  
                if not s:  
                    continue  
                if not (s.startswith("{") and s.endswith("}")):  
                    continue  
                try:  
                    obj = json.loads(s)  
                except Exception:  
                    continue  
                if isinstance(obj, dict):  
                    events.append(obj)  
    except Exception:  
        return events  
  
    return events  
  
  
def _safe_step_inputs(step: Dict[str, Any]) -> Dict[str, Any]:  
    # keep minimal, omit secrets  
    allow = (  
        "name",  
        "url",  
        "selector_ref",  
        "selector",  
        "by",  
        "timeout",  
        "condition",  
        "seconds",  
        "path",  
        "save_as",  
    )  
    out: Dict[str, Any] = {}  
    for k in allow:  
        if k in step and step.get(k) not in (None, ""):  
            out[k] = step.get(k)  
  
    # explicitly exclude common secret-bearing fields  
    for sk in ("secret", "text", "password", "token", "api_key"):  
        if sk in out:  
            out.pop(sk, None)  
  
    return out  
  
  
def _event_to_step_result(e: Dict[str, Any]) -> Optional[Tuple[int, str, Optional[str]]]:  
    """  
    Normalize various possible event shapes to:  
      (step_index, status, error_message)  
    status is "success" or "failure"  
    """  
    idx = e.get("step_index", None)  
    if idx is None:  
        idx = e.get("index", None)  
    try:  
        step_index = int(idx)  
    except Exception:  
        return None  
  
    # Prefer explicit event/type  
    ev = str(e.get("event") or e.get("type") or "").strip().lower()  
  
    # Common patterns  
    if ev in {"step_success", "action_success"}:  
        return (step_index, "success", None)  
    if ev in {"step_error", "action_error", "step_failure", "action_failure"}:  
        msg = e.get("error_message") or e.get("message") or e.get("error") or e.get("exception")  
        return (step_index, "failure", str(msg) if msg else None)  
  
    # Fallback: ok/status fields  
    st = e.get("status")  
    if isinstance(st, str) and st.strip().lower() in {"success", "ok", "passed"}:  
        return (step_index, "success", None)  
    if isinstance(st, str) and st.strip().lower() in {"failure", "failed", "error"}:  
        msg = e.get("error_message") or e.get("message") or e.get("error") or e.get("exception")  
        return (step_index, "failure", str(msg) if msg else None)  
  
    ok = e.get("ok")  
    if isinstance(ok, bool):  
        if ok:  
            return (step_index, "success", None)  
        msg = e.get("error_message") or e.get("message") or e.get("error") or e.get("exception")  
        return (step_index, "failure", str(msg) if msg else None)  
  
    return None  
  
  
def _build_step_logs(steps: List[Dict[str, Any]], events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:  
    """  
    Build step_logs with required fields:  
      - index  
      - action  
      - inputs  
      - status: success|failure  
      - error (if any)  
    Default status is "success" unless an error event is observed for that step.  
    """  
    logs: List[Dict[str, Any]] = []  
    by_index: Dict[int, Dict[str, Any]] = {}  
  
    for i, st in enumerate(steps):  
        action = str(st.get("action", "")).strip()  
        row: Dict[str, Any] = {  
            "index": i,  
            "action": action,  
            "inputs": _safe_step_inputs(st),  
            "status": "unknown",  
        }  
        logs.append(row)  
        by_index[i] = row  
  
    for e in events:  
        norm = _event_to_step_result(e)  
        if not norm:  
            continue  
        idx, status, err = norm  
        row = by_index.get(idx)  
        if not row:  
            continue  
        row["status"] = status  
        if status == "failure":  
            row["error"] = err or "step failed"  
  
    return logs  
  
  
def _cmd_auto(args: argparse.Namespace) -> int:  
    _print_header("AUTO (build bundle from natural language)")  
  
    build_fn = _resolve_callable(  
        "BUILD.build_2c_full_bundle",  
        ("build_from_nl",),  
    )  
    if not build_fn:  
        print("ERROR: BUILD-2C not available (BUILD.build_2c_full_bundle.build_from_nl not found).")  
        return 1  
  
    out_dir = _ensure_path(args.output_dir)  
    cfg: Dict[str, Any] = {}  
    if args.cfg_json:  
        try:  
            cfg = json.loads(args.cfg_json)  
        except Exception:  
            print("ERROR: --cfg-json must be valid JSON.")  
            return 1  
  
    print("[cli] stage=build (BUILD-2C)")  
    try:  
        build_out = _call_with_fallbacks(  
            build_fn,  
            attempts=(  
                ((args.description,), {"output_dir": str(out_dir), "run_after_build": False, "cfg": cfg}),  
                ((args.description,), {"output_dir": str(out_dir), "cfg": cfg}),  
                ((args.description,), {"output_dir": str(out_dir)}),  
                ((args.description,), {}),  
            ),  
        )  
    except Exception as e:  
        print(f"ERROR: build failed: {type(e).__name__}: {e}")  
        return 1  
  
    ok = bool(isinstance(build_out, dict) and build_out.get("ok") is True)  
    workflow_path = (build_out or {}).get("workflow_path") if isinstance(build_out, dict) else None  
    smoke_test_path = (build_out or {}).get("smoke_test_path") if isinstance(build_out, dict) else None  
  
    print(f"[cli] build ok={ok}")  
    if workflow_path:  
        print(f"[cli] workflow_path: {workflow_path}")  
    if smoke_test_path:  
        print(f"[cli] smoke_test_path: {smoke_test_path}")  
  
    if not ok:  
        print("[cli] build output:")  
        print(_safe_json(build_out))  
        return 1  
  
    if args.run:  
        _print_header("AUTO (execute via AGENT-2A)")  
        agent_fn = _resolve_callable(  
            "AGENT.agent_2a_autonomous_loop",  
            ("run_autonomous",),  
        )  
        if not agent_fn:  
            print("ERROR: AGENT-2A not available (AGENT.agent_2a_autonomous_loop.run_autonomous not found).")  
            return 1  
        if not workflow_path:  
            print("ERROR: missing workflow_path from build output; cannot run.")  
            return 1  
  
        try:  
            run_out = _call_with_fallbacks(  
                agent_fn,  
                attempts=(  
                    ((workflow_path,), {"max_attempts": args.max_attempts, "cfg": cfg}),  
                    ((workflow_path,), {"cfg": cfg}),  
                    ((workflow_path,), {}),  
                ),  
            )  
        except Exception as e:  
            print(f"ERROR: execution failed: {type(e).__name__}: {e}")  
            return 1  
  
        print("[cli] run summary:")  
        print(_safe_json(run_out))  
        if isinstance(run_out, dict) and run_out.get("success") is True:  
            print("[cli] SUCCESS")  
            return 0  
        print("[cli] FAILURE")  
        return 1  
  
    print("[cli] SUCCESS (build completed)")  
    return 0  
  
  
def _cmd_run(args: argparse.Namespace) -> int:  
    _print_header("RUN (execute workflow)")  
  
    run_fn = _resolve_callable(  
        "RUN.run_1a_workflow_runner",  
        ("run_workflow", "run", "run_workflow_runner"),  
    )  
    if not run_fn:  
        print("ERROR: RUN-1A not available.")  
        return 1  
  
    cfg: Dict[str, Any] = {}  
    if args.cfg_json:  
        try:  
            cfg = json.loads(args.cfg_json)  
        except Exception:  
            print("ERROR: --cfg-json must be valid JSON.")  
            return 1  
  
    # Ensure we control the log location so we can attach step_logs post-run.  
    log_path = _ensure_cli_log_path_in_cfg(cfg)  
  
    # Best-effort: load steps from workflow JSON so we can always output one log row per step.  
    steps: List[Dict[str, Any]] = []  
    try:  
        steps = _load_workflow_steps(args.workflow_path)  
    except Exception:  
        steps = []  
  
    try:  
        out = _call_with_fallbacks(  
            run_fn,  
            attempts=(  
                ((args.workflow_path,), {"cfg": cfg}),  
                ((args.workflow_path, cfg), {}),  
                ((args.workflow_path,), {}),  
            ),  
        )  
    except Exception as e:  
        print(f"ERROR: run failed: {type(e).__name__}: {e}")  
        return 1  
  
    # Normalize common runner return shapes: (summary_dict, exit_code)  
    exit_code: Optional[int] = None  
    if isinstance(out, (tuple, list)) and len(out) == 2 and isinstance(out[1], int) and isinstance(out[0], dict):  
        exit_code = int(out[1])  
        out = out[0]  
        out.setdefault("exit_code", exit_code)  
  
    # Attach step_logs (additive) if we can.  
    try:  
        if isinstance(out, dict) and "step_logs" not in out and steps:  
            events = _read_jsonl_events(log_path)  
            out["step_logs"] = _build_step_logs(steps, events)  
    except Exception as e:  
        # UX: keep clean; but do not fail the whole run just because logs couldn't be built.  
        if isinstance(out, dict):  
            out.setdefault("warnings", [])  
            if isinstance(out["warnings"], list):  
                out["warnings"].append(f"step_logs_build_failed: {type(e).__name__}: {e}")  
  
    print(_safe_json(out))  
  
    # Prefer explicit exit codes if provided.  
    if isinstance(out, dict) and isinstance(out.get("exit_code"), int):  
        return int(out["exit_code"])  
    if isinstance(exit_code, int):  
        return exit_code  
  
    # Determine success using explicit flags first, then fall back to step_logs if present.  
    if isinstance(out, dict):  
        if isinstance(out.get("success"), bool):  
            return 0 if out["success"] else 1  
        if isinstance(out.get("ok"), bool):  
            return 0 if out["ok"] else 1  
  
        for fk in ("failed", "failed_count"):  
            failed = out.get(fk)  
            if isinstance(failed, int) and not isinstance(failed, bool):  
                return 0 if failed == 0 else 1  
  
        sl = out.get("step_logs")  
        if isinstance(sl, list):  
            if any(isinstance(r, dict) and r.get("status") == "failure" for r in sl):  
                return 1  
            if any(isinstance(r, dict) and r.get("status") == "unknown" for r in sl):  
                return 1  
  
    # Default: no explicit success indicator => failure (prevents silent pass)  
    return 1   
  
  
def _cmd_doctor(_: argparse.Namespace) -> int:  
    _print_header("DOCTOR")  
  
    doctor_fn = (  
        _resolve_callable("DOCTOR.doctor_1a_health_check", ("run_doctor", "doctor", "check"))  
        or _resolve_callable("DOCTOR.doctor_1a_doctor", ("run_doctor", "doctor", "check"))  
    )  
    if not doctor_fn:  
        print("ERROR: DOCTOR-1A not available.")  
        return 1  
  
    try:  
        out = _call_with_fallbacks(  
            doctor_fn,  
            attempts=(  
                ((), {}),  
                ((), {"cfg": {}}),  
            ),  
        )  
    except Exception as e:  
        print(f"ERROR: doctor failed: {type(e).__name__}: {e}")  
        return 1  
  
    print(_safe_json(out))  
    # Keep CLI deterministic across environments: success means "doctor ran", not "all checks passed".  
    return 0  
  
  
def _cmd_history(args: argparse.Namespace) -> int:  
    _print_header("HISTORY")  
  
    # Prefer existing loader (LEARN-1A) for compatibility  
    load_fn = _resolve_callable(  
        "LEARN.learn_1a_failure_patterns",  
        ("load_history",),  
    )  
    if not load_fn:  
        print("ERROR: history loader not available (LEARN.learn_1a_failure_patterns.load_history).")  
        return 1  
  
    path = _ensure_path(args.path)  
    if not path.exists():  
        print(f"ERROR: history file not found: {path}")  
        return 1  
  
    try:  
        rows = load_fn(path)  
    except Exception as e:  
        print(f"ERROR: failed to read history: {type(e).__name__}: {e}")  
        return 1  
  
    rows = rows if isinstance(rows, list) else []  
    total = len(rows)  
    limit = max(1, int(args.limit))  
    tail = rows[-limit:]  
  
    # Simple summary  
    success_n = sum(  
        1  
        for r in rows  
        if isinstance(r, dict) and str(r.get("status", "")).lower() in {"success", "ok", "passed"}  
    )  
    fail_n = total - success_n  
  
    print(f"[cli] history_path: {path}")  
    print(f"[cli] rows: {total}  success: {success_n}  failed: {fail_n}")  
    print(f"[cli] last {min(limit, total)} rows:")  
    print(_safe_json(tail))  
    return 0  
  
  
def _cmd_replay(args: argparse.Namespace) -> int:  
    _print_header("REPLAY")  
  
    replay_fn = (  
        _resolve_callable("REPLAY.replay_1a_replay", ("replay", "replay_run", "run_replay"))  
        or _resolve_callable("REPLAY.replay_1a_player", ("replay", "replay_run", "run_replay"))  
    )  
    if not replay_fn:  
        print("ERROR: REPLAY-1A not available.")  
        return 1  
  
    try:  
        out = _call_with_fallbacks(  
            replay_fn,  
            attempts=(  
                ((args.run_id,), {}),  
                ((), {"run_id": args.run_id}),  
            ),  
        )  
    except Exception as e:  
        print(f"ERROR: replay failed: {type(e).__name__}: {e}")  
        return 1  
  
    print(_safe_json(out))  
    return 0  
  
  
def _cmd_report(args: argparse.Namespace) -> int:  
    _print_header("REPORT")  
  
    report_fn = _resolve_callable(  
        "REPORT.report_1a_generate",  
        ("generate_report", "build_report", "report_generate"),  
    )  
    if not report_fn:  
        print("ERROR: REPORT-1A not available.")  
        return 1  
  
    try:  
        out = _call_with_fallbacks(  
            report_fn,  
            attempts=(  
                ((args.run_id,), {}),  
                ((), {"run_id": args.run_id}),  
            ),  
        )  
    except Exception as e:  
        print(f"ERROR: report failed: {type(e).__name__}: {e}")  
        return 1  
  
    print(_safe_json(out))  
    return 0  
  
  
def main(argv: Optional[Sequence[str]] = None) -> int:  
    parser = argparse.ArgumentParser(prog="rpa", add_help=True)  
    sub = parser.add_subparsers(dest="cmd", required=True)  
  
    p_auto = sub.add_parser("auto", help='Build from NL: rpa auto "..."')  
    p_auto.add_argument("description", type=str)  
    p_auto.add_argument("--output-dir", type=str, default=".")  
    p_auto.add_argument("--run", action="store_true", help="Execute built workflow using AGENT-2A")  
    p_auto.add_argument("--max-attempts", type=int, default=3)  
    p_auto.add_argument("--cfg-json", type=str, default="", help="JSON string merged into cfg for submodules")  
    p_auto.set_defaults(func=_cmd_auto)  
  
    p_run = sub.add_parser("run", help="Run a workflow JSON")  
    p_run.add_argument("workflow_path", type=str)  
    p_run.add_argument("--cfg-json", type=str, default="")  
    p_run.set_defaults(func=_cmd_run)  
  
    p_doctor = sub.add_parser("doctor", help="Run diagnostics")  
    p_doctor.set_defaults(func=_cmd_doctor)  
  
    p_hist = sub.add_parser("history", help="Show history summary")  
    p_hist.add_argument("--path", type=str, default="history/run_history.jsonl")  
    p_hist.add_argument("--limit", type=int, default=20)  
    p_hist.set_defaults(func=_cmd_history)  
  
    p_replay = sub.add_parser("replay", help="Replay a prior run")  
    p_replay.add_argument("run_id", type=str)  
    p_replay.set_defaults(func=_cmd_replay)  
  
    p_report = sub.add_parser("report", help="Generate/print report for a run")  
    p_report.add_argument("run_id", type=str)  
    p_report.set_defaults(func=_cmd_report)  
  
    ns = parser.parse_args(list(argv) if argv is not None else None)  
  
    try:  
        code = int(ns.func(ns))  
        return code  
    except Exception as e:  
        # UX requirement: no stack trace; just a clean error line.  
        print(f"ERROR: {type(e).__name__}: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  