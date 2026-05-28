"""  
CLI-1G: Workflow grammar gate CLI.  
  
Single responsibility:  
- Provide a small CLI entrypoint to assert/sanitize workflow JSON files under a directory  
  using BUILD-2G, and optionally emit a deterministic JSON report using REPORT-1A.  
  
Exit codes (deterministic):  
- 0: success (assert mode with no violations OR sanitize mode completed)  
- 2: assert mode found violations  
- 1: unexpected error / invalid usage  
"""  
  
from __future__ import annotations  
  
import argparse  
from pathlib import Path  
from typing import List, Optional, Sequence  
  
from BUILD.build_2g_workflow_tree_grammar_gate import (  
    WorkflowTreeGateResult,  
    gate_workflow_tree_assert,  
    gate_workflow_tree_sanitize,  
)  
from REPORT.report_1a_workflow_grammar_gate_report import (  
    build_grammar_gate_report,  
    dump_grammar_gate_report_json_text,  
)  
  
__all__ = [  
    "build_arg_parser",  
    "run_cli",  
    "main",  
]  
  
  
def build_arg_parser() -> argparse.ArgumentParser:  
    p = argparse.ArgumentParser(  
        prog="workflow-grammar-gate",  
        description="Assert/sanitize workflow step actions against the supported grammar.",  
    )  
    p.add_argument("root_dir", help="Root directory (or single .json file) to gate.")  
    mode = p.add_mutually_exclusive_group()  
    mode.add_argument(  
        "--assert",  
        dest="mode_assert",  
        action="store_true",  
        help="Fail if unsupported actions are found (default).",  
    )  
    mode.add_argument(  
        "--sanitize",  
        dest="mode_sanitize",  
        action="store_true",  
        help="Strip unsupported actions and optionally write results.",  
    )  
    p.add_argument(  
        "--no-recursive",  
        dest="recursive",  
        action="store_false",  
        help="Do not recurse into subdirectories.",  
    )  
    p.set_defaults(recursive=True)  
  
    p.add_argument(  
        "--output-dir",  
        default=None,  
        help="When sanitizing, write sanitized copies under this directory (preserves relative paths).",  
    )  
    p.add_argument(  
        "--no-in-place",  
        dest="in_place",  
        action="store_false",  
        help="When sanitizing without --output-dir, do not overwrite inputs (in-memory only).",  
    )  
    p.set_defaults(in_place=True)  
  
    p.add_argument(  
        "--report-json",  
        default=None,  
        help="Optional path to write a deterministic JSON report.",  
    )  
    return p  
  
  
def _write_report_if_requested(tree_result: WorkflowTreeGateResult, report_json: Optional[str]) -> None:  
    if not report_json:  
        return  
    report_path = Path(report_json)  
    report_path.parent.mkdir(parents=True, exist_ok=True)  
    report = build_grammar_gate_report(tree_result)  
    report_path.write_text(dump_grammar_gate_report_json_text(report), encoding="utf-8")  
  
  
def run_cli(argv: Sequence[str]) -> int:  
    """  
    Runs the CLI with argv (excluding program name).  
    Returns an exit code (0/1/2).  
    """  
    p = build_arg_parser()  
    args = p.parse_args(list(argv))  
  
    # Default mode is assert if neither flag is provided  
    mode_sanitize = bool(args.mode_sanitize)  
    mode_assert = bool(args.mode_assert) or not mode_sanitize  
  
    root_dir = args.root_dir  
    recursive = bool(args.recursive)  
  
    try:  
        if mode_assert:  
            tree_result = gate_workflow_tree_assert(root_dir, recursive=recursive)  
            _write_report_if_requested(tree_result, args.report_json)  
            return 0  
  
        # sanitize mode  
        output_dir = args.output_dir  
        in_place = bool(args.in_place)  
        tree_result = gate_workflow_tree_sanitize(  
            root_dir,  
            recursive=recursive,  
            in_place=in_place,  
            output_dir=output_dir,  
        )  
        _write_report_if_requested(tree_result, args.report_json)  
        return 0  
  
    except ValueError:  
        # Assertion failure from gate_workflow_tree_assert  
        if mode_assert:  
            # Best-effort: we can still compute a report by sanitizing in-memory (no writes)  
            try:  
                tree_result = gate_workflow_tree_sanitize(  
                    root_dir,  
                    recursive=recursive,  
                    in_place=False,  
                    output_dir=None,  
                )  
                _write_report_if_requested(tree_result, args.report_json)  
            except Exception:  
                pass  
            return 2  
        return 1  
    except SystemExit:  
        # argparse may raise this, but parse_args already happened; keep deterministic.  
        return 1  
    except Exception:  
        return 1  
  
  
def main(argv: Optional[Sequence[str]] = None) -> int:  
    """  
    Programmatic entrypoint. If argv is None, uses sys.argv[1:].  
    """  
    import sys  
  
    return run_cli(sys.argv[1:] if argv is None else argv)  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  