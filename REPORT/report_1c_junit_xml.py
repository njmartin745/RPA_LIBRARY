"""  
REPORT-1C — JUnit XML renderer (10.3.3)  
  
Single responsibility:  
- Convert a REPORT-1A run report dict into deterministic JUnit XML and write it to:  
  {run_output_dir}/report/junit.xml  
  
Notes:  
- Attribute ordering in XML serializers can vary; we generate XML as a string with a fixed layout.  
- This is intended for CI consumption (tests = steps, failures = error steps).  
"""  
  
from __future__ import annotations  
  
import json  
import os  
from pathlib import Path  
from typing import Any, Mapping  
from xml.sax.saxutils import escape as _xml_escape  
  
__all__ = [  
    "build_junit_xml",  
    "write_junit_xml",  
    "dev_smoke",  
]  
  
  
def _nl(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def _json_compact(obj: Any) -> str:  
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))  
  
  
def _workflow_name_from_report(report: Mapping[str, Any]) -> str:  
    manifest = report.get("manifest")  
    if isinstance(manifest, Mapping):  
        wf = manifest.get("workflow")  
        if isinstance(wf, Mapping):  
            name = wf.get("name")  
            if isinstance(name, str) and name.strip():  
                return name.strip()  
    return "workflow"  
  
  
def build_junit_xml(report: Mapping[str, Any]) -> str:  
    """  
    Build deterministic JUnit XML from a REPORT-1A dict.  
  
    Mapping:  
      - one <testcase> per step outcome  
      - status == 'error' -> <failure>  
    """  
    outcomes = report.get("step_outcomes")  
    if not isinstance(outcomes, list):  
        outcomes = []  
  
    wf_name = _workflow_name_from_report(report)  
  
    total = 0  
    failures = 0  
  
    testcase_lines: list[str] = []  
    for rec in outcomes:  
        if not isinstance(rec, Mapping):  
            continue  
  
        total += 1  
        step_index = rec.get("step_index")  
        step = rec.get("step") if isinstance(rec.get("step"), Mapping) else {}  
        action = step.get("action")  
        action_s = str(action) if action is not None else "action"  
        name = f"step_{step_index}:{action_s}"  
  
        status = str(rec.get("status")) if rec.get("status") is not None else "unknown"  
        err = rec.get("error") if isinstance(rec.get("error"), Mapping) else None  
        err_message = None  
        if isinstance(err, Mapping):  
            err_message = err.get("message")  
        err_message_s = str(err_message) if err_message is not None else "error"  
  
        testcase_lines.append(  
            f'    <testcase classname="{_xml_escape(wf_name)}" name="{_xml_escape(name)}">'  
        )  
  
        if status == "error":  
            failures += 1  
            body = _json_compact(step)  
            testcase_lines.append(  
                f'      <failure message="{_xml_escape(err_message_s)}">{_xml_escape(body)}</failure>'  
            )  
  
        testcase_lines.append("    </testcase>")  
  
    # Deterministic root + suite layout  
    lines = [  
        '<?xml version="1.0" encoding="UTF-8"?>',  
        "<testsuites>",  
        f'  <testsuite name="{_xml_escape(wf_name)}" tests="{total}" failures="{failures}" errors="0" skipped="0">',  
        *testcase_lines,  
        "  </testsuite>",  
        "</testsuites>",  
        "",  
    ]  
    return _nl("\n".join(lines))  
  
  
def write_junit_xml(  
    *,  
    run_output_dir: str | os.PathLike[str],  
    junit_xml: str,  
    overwrite: bool = True,  
) -> dict[str, Any]:  
    """  
    Write XML to: {run_output_dir}/report/junit.xml  
    """  
    root = Path(run_output_dir)  
    out_path = root / "report" / "junit.xml"  
    out_path.parent.mkdir(parents=True, exist_ok=True)  
  
    if out_path.exists() and not overwrite:  
        raise FileExistsError(str(out_path))  
  
    out_path.write_text(_nl(junit_xml), encoding="utf-8", newline="\n")  
  
    return {  
        "schema": "REPORT-1C-WRITE",  
        "path": str(out_path),  
        "path_relative": out_path.resolve().relative_to(root.resolve()).as_posix(),  
        "bytes": out_path.stat().st_size,  
    }  
  
  
def dev_smoke() -> None:  
    repo_root = Path(__file__).resolve().parents[1]  
    out_root = repo_root / "dev" / "_smoke_artifacts" / "10_3_3"  
  
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
  
    loaded = load_json_file(out_root / "report" / "run_report.json")  
    xml = build_junit_xml(loaded)  
    info = write_junit_xml(run_output_dir=out_root, junit_xml=xml, overwrite=True)  
  
    assert info["schema"] == "REPORT-1C-WRITE"  
    assert info["path_relative"] == "report/junit.xml"  
  
    saved = (out_root / "report" / "junit.xml").read_text(encoding="utf-8")  
    assert saved.endswith("\n")  
    assert "<testsuites>" in saved  
    assert 'tests="2"' in saved  
    assert 'failures="1"' in saved  
    assert "step_1:click_selector" in saved  
    assert "<failure" in saved  
    assert "boom" in saved  
    assert "selector_ref" in saved  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: REPORT.report_1c_junit_xml")  