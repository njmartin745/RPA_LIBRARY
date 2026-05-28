"""  
CLI-1F — Generate reports for a run output directory (10.4.3)  
  
Single responsibility:  
- Parse CLI args and invoke RUN-1E post-run reporting hook.  
  
Usage:  
  python -m CLI.cli_1f_generate_reports --run-output-dir <dir>  
"""  
  
from __future__ import annotations  
  
import argparse  
import json  
from pathlib import Path  
from typing import Any, Sequence  
  
__all__ = [  
    "build_arg_parser",  
    "run_cli_generate_reports",  
    "main",  
    "dev_smoke",  
]  
  
  
def build_arg_parser() -> argparse.ArgumentParser:  
    p = argparse.ArgumentParser(prog="rpa-generate-reports", add_help=True)  
    p.add_argument(  
        "--run-output-dir",  
        required=True,  
        help="Path to a run output directory containing history/ artifacts.",  
    )  
    p.add_argument(  
        "--disable",  
        action="store_true",  
        help="Do not generate reports (no-op).",  
    )  
    p.add_argument(  
        "--no-overwrite",  
        action="store_true",  
        help="Do not overwrite existing report files.",  
    )  
    p.add_argument(  
        "--quiet",  
        action="store_true",  
        help="Do not print JSON result to stdout.",  
    )  
    return p  
  
  
def run_cli_generate_reports(argv: Sequence[str]) -> dict[str, Any]:  
    """  
    Pure CLI runner (no printing). Returns the result dict.  
    """  
    ns = build_arg_parser().parse_args(list(argv))  
  
    from RUN.run_1e_post_run_reporting import maybe_generate_post_run_reports  
  
    res = maybe_generate_post_run_reports(  
        run_output_dir=Path(ns.run_output_dir),  
        enabled=(not bool(ns.disable)),  
        overwrite=(not bool(ns.no_overwrite)),  
    )  
    return dict(res)  
  
  
def main(argv: Sequence[str] | None = None) -> int:  
    res = run_cli_generate_reports([] if argv is None else argv)  
  
    # Re-parse quiet flag deterministically from argv if present  
    quiet = False  
    if argv is not None and any(a == "--quiet" for a in argv):  
        quiet = True  
  
    if not quiet:  
        print(json.dumps(res, sort_keys=True, indent=2, ensure_ascii=True))  
    return 0  
  
  
def dev_smoke() -> None:  
    repo_root = Path(__file__).resolve().parents[1]  
    out_root = repo_root / "dev" / "_smoke_artifacts" / "10_4_3"  
  
    # deterministic cleanup  
    if out_root.exists():  
        for p in sorted(out_root.rglob("*"), key=lambda x: str(x), reverse=True):  
            if p.is_file():  
                p.unlink()  
            elif p.is_dir():  
                try:  
                    p.rmdir()  
                except OSError:  
                    pass  
        try:  
            out_root.rmdir()  
        except OSError:  
            pass  
    out_root.mkdir(parents=True, exist_ok=True)  
  
    # Create minimal history artifacts  
    from HISTORY.history_1a_run_manifest import build_run_manifest, write_run_manifest  
    from HISTORY.history_1b_step_outcomes import build_step_outcome, append_step_outcome  
  
    wf_path = out_root / "wf.yml"  
    wf_path.write_text("name: smoke\nsteps: []\n", encoding="utf-8", newline="\n")  
  
    manifest = build_run_manifest(  
        run_output_dir=out_root,  
        workflow_name="smoke_workflow",  
        workflow_path=wf_path,  
        inputs={"env": "DEV"},  
        started_at_utc="2026-01-01T00:00:00+00:00",  
        finished_at_utc="2026-01-01T00:00:02+00:00",  
        bundle_version="bundle-0",  
        workflow_version="wf-0",  
    )  
    write_run_manifest(run_output_dir=out_root, manifest=manifest, overwrite=True)  
  
    append_step_outcome(  
        run_output_dir=out_root,  
        outcome=build_step_outcome(  
            workflow_name="smoke_workflow",  
            step_index=0,  
            step={"action": "open", "url": "https://example.com"},  
            status="ok",  
            started_at_utc="2026-01-01T00:00:00+00:00",  
            finished_at_utc="2026-01-01T00:00:01+00:00",  
        ),  
    )  
    append_step_outcome(  
        run_output_dir=out_root,  
        outcome=build_step_outcome(  
            workflow_name="smoke_workflow",  
            step_index=1,  
            step={"action": "click_selector", "selector_ref": "app.button.save"},  
            status="error",  
            started_at_utc="2026-01-01T00:00:01+00:00",  
            finished_at_utc="2026-01-01T00:00:02+00:00",  
            error=RuntimeError("boom"),  
        ),  
    )  
  
    res = run_cli_generate_reports(  
        ["--run-output-dir", str(out_root), "--quiet"]  
    )  
    assert res["schema"] == "RUN-1E"  
    assert res["generated"] is True  
  
    report_dir = out_root / "report"  
    assert (report_dir / "run_report.json").exists()  
    assert (report_dir / "run_report.md").exists()  
    assert (report_dir / "junit.xml").exists()  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  