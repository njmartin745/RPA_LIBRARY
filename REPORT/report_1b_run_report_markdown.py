"""  
REPORT-1B — Run report markdown renderer (10.3.2)  
  
Single responsibility:  
- Convert a REPORT-1A run report dict into deterministic Markdown text and write it to:  
  {run_output_dir}/report/run_report.md  
"""  
  
from __future__ import annotations  
  
import json  
import os  
from pathlib import Path  
from typing import Any, Mapping  
  
__all__ = [  
    "build_run_report_markdown",  
    "write_run_report_markdown",  
    "dev_smoke",  
]  
  
  
def _json_compact(obj: Any) -> str:  
    # Deterministic compact JSON for embedding in Markdown  
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))  
  
  
def _nl(s: str) -> str:  
    # Ensure newline normalization  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def build_run_report_markdown(report: Mapping[str, Any]) -> str:  
    """  
    Build deterministic Markdown from a REPORT-1A dict.  
    """  
    schema = report.get("schema")  
    run = report.get("run") if isinstance(report.get("run"), Mapping) else {}  
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}  
    manifest = report.get("manifest") if isinstance(report.get("manifest"), Mapping) else {}  
    outcomes = report.get("step_outcomes")  
    if not isinstance(outcomes, list):  
        outcomes = []  
  
    wf_name = None  
    if isinstance(manifest, Mapping):  
        wf = manifest.get("workflow")  
        if isinstance(wf, Mapping):  
            wf_name = wf.get("name")  
  
    status = run.get("status")  
    ts = run.get("timestamps") if isinstance(run.get("timestamps"), Mapping) else {}  
    started = ts.get("started_at_utc")  
    finished = ts.get("finished_at_utc")  
  
    total_steps = summary.get("total_steps")  
    status_counts = summary.get("status_counts")  
    if not isinstance(status_counts, Mapping):  
        status_counts = {}  
  
    # Deterministic status-count lines: sort keys  
    status_lines = []  
    for k in sorted(status_counts.keys(), key=lambda x: str(x)):  
        status_lines.append(f"- **{k}**: {status_counts[k]}")  
  
    # Deterministic failure listing: keep list order (already sorted in REPORT-1A)  
    failed_blocks: list[str] = []  
    for rec in outcomes:  
        if not isinstance(rec, Mapping):  
            continue  
        if str(rec.get("status")) != "error":  
            continue  
        idx = rec.get("step_index")  
        step = rec.get("step")  
        err = rec.get("error")  
        msg = None  
        if isinstance(err, Mapping):  
            msg = err.get("message")  
        failed_blocks.append(  
            _nl(  
                "\n".join(  
                    [  
                        f"### Failed step {idx}",  
                        "",  
                        f"- **error**: {msg}",  
                        "",  
                        "```json",  
                        _json_compact(step),  
                        "```",  
                    ]  
                )  
            )  
        )  
  
    parts = [  
        f"# Run Report ({schema})",  
        "",  
        f"- **workflow**: {wf_name}",  
        f"- **status**: {status}",  
        f"- **started_at_utc**: {started}",  
        f"- **finished_at_utc**: {finished}",  
        "",  
        "## Summary",  
        "",  
        f"- **total_steps**: {total_steps}",  
        "",  
        "### Status counts",  
        "",  
        *status_lines,  
        "",  
        "## Failures",  
        "",  
    ]  
    if failed_blocks:  
        parts.extend(failed_blocks)  
        parts.append("")  
    else:  
        parts.append("_No failures recorded._\n")  
  
    md = "\n".join(parts)  
    return _nl(md).rstrip("\n") + "\n"  
  
  
def write_run_report_markdown(  
    *,  
    run_output_dir: str | os.PathLike[str],  
    markdown: str,  
    overwrite: bool = True,  
) -> dict[str, Any]:  
    """  
    Write markdown to: {run_output_dir}/report/run_report.md  
    """  
    root = Path(run_output_dir)  
    out_path = root / "report" / "run_report.md"  
    out_path.parent.mkdir(parents=True, exist_ok=True)  
  
    if out_path.exists() and not overwrite:  
        raise FileExistsError(str(out_path))  
  
    out_path.write_text(_nl(markdown), encoding="utf-8", newline="\n")  
  
    return {  
        "schema": "REPORT-1B-WRITE",  
        "path": str(out_path),  
        "path_relative": out_path.resolve().relative_to(root.resolve()).as_posix(),  
        "bytes": out_path.stat().st_size,  
    }  
  
  
def dev_smoke() -> None:  
    repo_root = Path(__file__).resolve().parents[1]  
    out_root = repo_root / "dev" / "_smoke_artifacts" / "10_3_2"  
  
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
  
    # Create history + report JSON using existing modules  
    from HISTORY.history_1a_run_manifest import build_run_manifest, write_run_manifest  
    from HISTORY.history_1b_step_outcomes import build_step_outcome, append_step_outcome  
    from REPORT.report_1a_run_report import build_run_report, write_run_report, load_json_file  
  
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
  
    report = build_run_report(run_output_dir=out_root)  
    write_run_report(run_output_dir=out_root, report=report, overwrite=True)  
  
    # Load from disk to ensure typical usage path works  
    loaded = load_json_file(out_root / "report" / "run_report.json")  
    md = build_run_report_markdown(loaded)  
    info = write_run_report_markdown(run_output_dir=out_root, markdown=md, overwrite=True)  
  
    assert info["schema"] == "REPORT-1B-WRITE"  
    assert info["path_relative"] == "report/run_report.md"  
  
    saved = (out_root / "report" / "run_report.md").read_text(encoding="utf-8")  
    assert saved.endswith("\n")  
    assert "# Run Report (REPORT-1A)" in saved  
    assert "- **workflow**: smoke_workflow" in saved  
    assert "- **status**: error" in saved  
    assert "### Failed step 1" in saved  
    assert '"selector_ref":"app.button.save"' in saved  
    assert "- **error**: boom" in saved  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: REPORT.report_1b_run_report_markdown")  