"""  
REPORT-1D — Generate standard report artifacts (10.4.1)  
  
Single responsibility:  
- Given a run_output_dir, generate the standard set of report artifacts by composing:  
  - REPORT-1A (JSON aggregation)  
  - REPORT-1B (Markdown)  
  - REPORT-1C (JUnit XML)  
  
Outputs:  
- {run_output_dir}/report/run_report.json  
- {run_output_dir}/report/run_report.md  
- {run_output_dir}/report/junit.xml  
"""  
  
from __future__ import annotations  
  
from pathlib import Path  
from typing import Any, Mapping  
  
__all__ = [  
    "generate_standard_reports",  
    "dev_smoke",  
]  
  
  
def generate_standard_reports(  
    *,  
    run_output_dir: str | Path,  
    overwrite: bool = True,  
) -> dict[str, Any]:  
    """  
    Generate standard report artifacts for a given run_output_dir.  
  
    Returns a dict describing what was written.  
    """  
    from REPORT.report_1a_run_report import build_run_report, write_run_report  
    from REPORT.report_1b_run_report_markdown import build_run_report_markdown, write_run_report_markdown  
    from REPORT.report_1c_junit_xml import build_junit_xml, write_junit_xml  
  
    root = Path(run_output_dir)  
  
    report = build_run_report(run_output_dir=root)  
    write_json = write_run_report(run_output_dir=root, report=report, overwrite=overwrite)  
  
    md = build_run_report_markdown(report)  
    write_md = write_run_report_markdown(run_output_dir=root, markdown=md, overwrite=overwrite)  
  
    xml = build_junit_xml(report)  
    write_xml = write_junit_xml(run_output_dir=root, junit_xml=xml, overwrite=overwrite)  
  
    return {  
        "schema": "REPORT-1D",  
        "run_output_dir": root.as_posix(),  
        "written": {  
            "run_report_json": dict(write_json),  
            "run_report_md": dict(write_md),  
            "junit_xml": dict(write_xml),  
        },  
    }  
  
  
def dev_smoke() -> None:  
    repo_root = Path(__file__).resolve().parents[1]  
    out_root = repo_root / "dev" / "_smoke_artifacts" / "10_4_1"  
  
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
  
    info = generate_standard_reports(run_output_dir=out_root, overwrite=True)  
    assert info["schema"] == "REPORT-1D"  
  
    report_dir = out_root / "report"  
    assert (report_dir / "run_report.json").exists()  
    assert (report_dir / "run_report.md").exists()  
    assert (report_dir / "junit.xml").exists()  
  
    md = (report_dir / "run_report.md").read_text(encoding="utf-8")  
    assert "- **status**: error" in md  
    assert "### Failed step 1" in md  
  
    xml = (report_dir / "junit.xml").read_text(encoding="utf-8")  
    assert 'tests="2"' in xml  
    assert 'failures="1"' in xml  
    assert "step_1:click_selector" in xml  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: REPORT.report_1d_generate_reports")  