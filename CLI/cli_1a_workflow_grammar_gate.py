"""  
CLI-1A: Workflow grammar gate CLI.  
  
Single responsibility:  
- Parse argv, load optional baseline/meta JSON, call RUN-1A, print compact output,  
  and return an exit code (no sys.exit inside core function).  
  
This is a thin wrapper over RUN/run_1a_workflow_grammar_gate_run.py.  
"""  
  
from __future__ import annotations  
  
import argparse  
import json  
from pathlib import Path  
from typing import Any, Dict, List, Mapping, Optional, Sequence, TextIO  
  
from REPORT.report_1c_workflow_grammar_gate_report_summary import format_grammar_gate_summary_line  
from RUN.run_1a_workflow_grammar_gate_run import run_workflow_grammar_gate  
  
__all__ = [  
    "cli_workflow_grammar_gate",  
]  
  
  
def _read_json_dict(path: str) -> Dict[str, Any]:  
    p = Path(path)  
    data = json.loads(p.read_text(encoding="utf-8"))  
    if not isinstance(data, dict):  
        raise ValueError(f"JSON at {path!r} must be an object/dict")  
    return data  
  
  
def _build_parser() -> argparse.ArgumentParser:  
    ap = argparse.ArgumentParser(prog="workflow-grammar-gate", add_help=True)  
  
    ap.add_argument("root_dir")  
  
    ap.add_argument("--mode", choices=["check", "fix"], default="check")  
    ap.add_argument("--in-place", dest="in_place", action="store_true", default=True)  
    ap.add_argument("--no-in-place", dest="in_place", action="store_false")  
    ap.add_argument("--output-dir", default=None)  
  
    ap.add_argument("--include-ok-files", action="store_true", default=False)  
    ap.add_argument("--max-files", type=int, default=200)  
    ap.add_argument("--max-violations-per-file", type=int, default=200)  
  
    ap.add_argument("--baseline-report", default=None, help="Path to baseline report JSON")  
    ap.add_argument("--max-total-violations", type=int, default=0)  
    ap.add_argument("--max-files-with-violations", type=int, default=0)  
    ap.add_argument("--max-delta-total-violations", type=int, default=0)  
  
    ap.add_argument(  
        "--apply-guard",  
        dest="apply_guard",  
        action="store_true",  
        default=None,  
        help='Force guard on (default: on for mode="check", off for mode="fix")',  
    )  
    ap.add_argument(  
        "--no-apply-guard",  
        dest="apply_guard",  
        action="store_false",  
        default=None,  
        help="Force guard off",  
    )  
  
    ap.add_argument("--history-jsonl", default=None)  
    ap.add_argument("--history-meta-json", default=None, help="Path to meta JSON object to include in history records")  
  
    return ap  
  
  
def cli_workflow_grammar_gate(  
    argv: Optional[Sequence[str]] = None,  
    *,  
    out: Optional[TextIO] = None,  
    err: Optional[TextIO] = None,  
) -> int:  
    """  
    Run the workflow grammar gate CLI.  
  
    Returns:  
      process-like exit code (0 ok, 2 fail).  
    """  
    import sys  
  
    out = out if out is not None else sys.stdout  
    err = err if err is not None else sys.stderr  
  
    ap = _build_parser()  
    ns = ap.parse_args(list(argv) if argv is not None else None)  
  
    baseline_report: Optional[Mapping[str, Any]] = None  
    if ns.baseline_report:  
        try:  
            baseline_report = _read_json_dict(ns.baseline_report)  
        except Exception as e:  # pragma: no cover  
            err.write(f"ERROR: failed to read baseline report {ns.baseline_report!r}: {e}\n")  
            return 2  
  
    meta: Optional[Dict[str, Any]] = None  
    if ns.history_meta_json:  
        try:  
            meta = _read_json_dict(ns.history_meta_json)  
        except Exception as e:  # pragma: no cover  
            err.write(f"ERROR: failed to read history meta JSON {ns.history_meta_json!r}: {e}\n")  
            return 2  
  
    res = run_workflow_grammar_gate(  
        ns.root_dir,  
        mode=str(ns.mode),  
        in_place=bool(ns.in_place),  
        output_dir=ns.output_dir,  
        include_ok_files=bool(ns.include_ok_files),  
        max_files=int(ns.max_files),  
        max_violations_per_file=int(ns.max_violations_per_file),  
        apply_guard=ns.apply_guard,  
        baseline_report=baseline_report,  
        max_total_violations=int(ns.max_total_violations),  
        max_files_with_violations=int(ns.max_files_with_violations),  
        max_delta_total_violations=int(ns.max_delta_total_violations),  
        history_jsonl_path=ns.history_jsonl,  
        history_meta=meta,  
    )  
  
    if res.diagnosis.report is not None:  
        out.write(format_grammar_gate_summary_line(res.diagnosis.report) + "\n")  
  
    if res.guard is not None and not res.guard.ok:  
        for r in res.guard.reasons:  
            err.write(f"GUARD: {r}\n")  
  
    return int(res.exit_code)  