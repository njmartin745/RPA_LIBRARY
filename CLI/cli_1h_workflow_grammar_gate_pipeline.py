"""  
CLI-1H: Workflow grammar gate pipeline CLI.  
  
Single responsibility:  
- Provide an argparse-based CLI wrapper around PIPE-1A pipeline runner.  
- Optionally emits:  
  - JSON report via PIPE (report_json_path)  
  - Text report via REPORT-1B (report_text_path and/or stdout)  
  
Does not invent new workflow step types; only gates workflows.  
"""  
  
from __future__ import annotations  
  
import argparse  
from pathlib import Path  
from typing import Optional, Sequence  
  
from PIPE.pipe_1a_workflow_grammar_gate_pipeline import run_workflow_grammar_gate_pipeline  
from REPORT.report_1b_workflow_grammar_gate_report_text import format_grammar_gate_report_text  
  
__all__ = [  
    "build_arg_parser",  
    "cli_main",  
]  
  
  
def build_arg_parser() -> argparse.ArgumentParser:  
    p = argparse.ArgumentParser(  
        prog="workflow-grammar-gate",  
        description="Check or sanitize workflow JSON files for supported action grammar.",  
    )  
    p.add_argument("root_dir", help="Directory (or file) containing workflow JSON(s).")  
  
    p.add_argument(  
        "--mode",  
        choices=["check", "fix"],  
        default="check",  
        help="check: no writes, exit 2 on violations; fix: sanitize (write depending on flags), exit 0.",  
    )  
    p.add_argument(  
        "--output-dir",  
        default=None,  
        help="When mode=fix, write sanitized copies to this directory (preserving relative paths).",  
    )  
    p.add_argument(  
        "--in-place",  
        dest="in_place",  
        action="store_true",  
        default=True,  
        help="When mode=fix and --output-dir not set, overwrite files in place (default).",  
    )  
    p.add_argument(  
        "--no-in-place",  
        dest="in_place",  
        action="store_false",  
        help="When mode=fix and --output-dir not set, do not overwrite files (in-memory only).",  
    )  
  
    p.add_argument(  
        "--report-json",  
        default=None,  
        help="Write deterministic JSON report to this path.",  
    )  
    p.add_argument(  
        "--report-text",  
        default=None,  
        help="Write deterministic text report to this path.",  
    )  
    p.add_argument(  
        "--print-report",  
        action="store_true",  
        default=True,  
        help="Print text report to stdout (default).",  
    )  
    p.add_argument(  
        "--quiet",  
        action="store_true",  
        default=False,  
        help="Do not print report to stdout (overrides --print-report).",  
    )  
  
    p.add_argument(  
        "--include-ok-files",  
        action="store_true",  
        default=False,  
        help="Include files with 0 violations in the text report.",  
    )  
    p.add_argument(  
        "--max-files",  
        type=int,  
        default=200,  
        help="Maximum number of files to show in the text report.",  
    )  
    p.add_argument(  
        "--max-violations-per-file",  
        type=int,  
        default=200,  
        help="Maximum number of violations per file to show in the text report.",  
    )  
    return p  
  
  
def _write_text(path: str, text: str) -> None:  
    p = Path(path)  
    p.parent.mkdir(parents=True, exist_ok=True)  
    p.write_text(text, encoding="utf-8")  
  
  
def cli_main(argv: Optional[Sequence[str]] = None) -> int:  
    args = build_arg_parser().parse_args(list(argv) if argv is not None else None)  
  
    res = run_workflow_grammar_gate_pipeline(  
        args.root_dir,  
        mode=args.mode,  
        in_place=bool(args.in_place),  
        output_dir=args.output_dir,  
        report_json_path=args.report_json,  
    )  
  
    # If we have an outcome, we can also produce the text report (stdout and/or file).  
    if res.outcome is not None:  
        text = format_grammar_gate_report_text(  
            res.outcome.report,  
            include_ok_files=bool(args.include_ok_files),  
            max_files=int(args.max_files),  
            max_violations_per_file=int(args.max_violations_per_file),  
        )  
        if args.report_text is not None:  
            _write_text(args.report_text, text)  
        if (not args.quiet) and bool(args.print_report):  
            print(text)  
  
    return int(res.exit_code)  