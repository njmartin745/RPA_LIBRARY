"""  
RUN-1E — Post-run reporting hook (10.4.2)  
  
Single responsibility:  
- Provide an additive, runner-friendly hook that can be called at the end of a run  
  to generate standard report artifacts.  
  
This module does NOT modify existing runners; it is intended to be composed by RUN  
modules (or CLI) in later milestones.  
  
Outputs (when enabled=True):  
- {run_output_dir}/report/run_report.json  
- {run_output_dir}/report/run_report.md  
- {run_output_dir}/report/junit.xml  
"""  
  
from __future__ import annotations  
  
from pathlib import Path  
from typing import Any  
  
__all__ = [  
    "maybe_generate_post_run_reports",  
    "dev_smoke",  
]  
  
  
def maybe_generate_post_run_reports(  
    *,  
    run_output_dir: str | Path,  
    enabled: bool = True,  
    overwrite: bool = True,  
) -> dict[str, Any]:  
    """  
    If enabled, generate standard reports for run_output_dir.  
  
    Returns a deterministic dict describing behavior.  
    """  
    root = Path(run_output_dir)  
  
    if not enabled:  
        return {  
            "schema": "RUN-1E",  
            "run_output_dir": root.as_posix(),  
            "enabled": False,  
            "generated": False,  
            "details": None,  
        }  
  
    from REPORT.report_1d_generate_reports import generate_standard_reports  
  
    details = generate_standard_reports(run_output_dir=root, overwrite=overwrite)  
  
    return {  
        "schema": "RUN-1E",  
        "run_output_dir": root.as_posix(),  
        "enabled": True,  
        "generated": True,  
        "details": details,  
    }  
  
  
def dev_smoke() -> None:  
    repo_root = Path(__file__).resolve().parents[1]  
    out_root = repo_root / "dev" / "_smoke_artifacts" / "10_4_2"  
  
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
  
    # disabled path  
    disabled = maybe_generate_post_run_reports(run_output_dir=out_root, enabled=False, overwrite=True)  
    assert disabled["schema"] == "RUN-1E"  
    assert disabled["enabled"] is False  
    assert disabled["generated"] is False  
  
    # enabled path  
    enabled = maybe_generate_post_run_reports(run_output_dir=out_root, enabled=True, overwrite=True)  
    assert enabled["schema"] == "RUN-1E"  
    assert enabled["enabled"] is True  
    assert enabled["generated"] is True  
  
    report_dir = out_root / "report"  
    assert (report_dir / "run_report.json").exists()  
    assert (report_dir / "run_report.md").exists()  
    assert (report_dir / "junit.xml").exists()  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: RUN.run_1e_post_run_reporting")  