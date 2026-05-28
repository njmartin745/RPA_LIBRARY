"""  
REPORT-1A — Run report aggregation (10.3.1)  
  
Single responsibility:  
- Read history artifacts (run manifest + step outcomes) and produce a deterministic  
  run report JSON under the run output directory.  
  
Inputs read (if present):  
- {run_output_dir}/history/run_manifest.json  
- {run_output_dir}/history/step_outcomes.jsonl  
  
Output written:  
- {run_output_dir}/report/run_report.json  
"""  
  
from __future__ import annotations  
  
import json  
import os  
from pathlib import Path  
from typing import Any, Iterable, Mapping  
  
__all__ = [  
    "load_json_file",  
    "load_jsonl_file",  
    "build_run_report",  
    "write_run_report",  
    "dev_smoke",  
]  
  
  
def _stable_json_bytes(obj: Any) -> bytes:  
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True).encode("utf-8")  
  
  
def load_json_file(path: str | os.PathLike[str]) -> dict[str, Any]:  
    p = Path(path)  
    return json.loads(p.read_text(encoding="utf-8"))  
  
  
def load_jsonl_file(path: str | os.PathLike[str]) -> list[dict[str, Any]]:  
    p = Path(path)  
    if not p.exists():  
        return []  
    lines = p.read_text(encoding="utf-8").splitlines()  
    out: list[dict[str, Any]] = []  
    for line in lines:  
        s = line.strip()  
        if not s:  
            continue  
        out.append(json.loads(s))  
    return out  
  
  
def _as_int(v: Any, default: int | None = None) -> int | None:  
    try:  
        return int(v)  
    except Exception:  
        return default  
  
  
def _count_status(outcomes: Iterable[Mapping[str, Any]]) -> dict[str, int]:  
    counts: dict[str, int] = {}  
    for rec in outcomes:  
        s = rec.get("status")  
        key = str(s) if s is not None else "unknown"  
        counts[key] = counts.get(key, 0) + 1  
    return counts  
  
  
def build_run_report(  
    *,  
    run_output_dir: str | os.PathLike[str],  
) -> dict[str, Any]:  
    """  
    Build a deterministic report dict by reading history artifacts.  
    """  
    root = Path(run_output_dir)  
    manifest_path = root / "history" / "run_manifest.json"  
    outcomes_path = root / "history" / "step_outcomes.jsonl"  
  
    manifest = load_json_file(manifest_path) if manifest_path.exists() else None  
    outcomes = load_jsonl_file(outcomes_path)  
  
    # Deterministic ordering by step_index then by original order fallback.  
    indexed: list[tuple[int | None, int, dict[str, Any]]] = []  
    for i, rec in enumerate(outcomes):  
        indexed.append((_as_int(rec.get("step_index")), i, rec))  
    indexed.sort(key=lambda t: (t[0] is None, t[0] if t[0] is not None else 10**9, t[1]))  
    outcomes_sorted = [t[2] for t in indexed]  
  
    status_counts = _count_status(outcomes_sorted)  
    total_steps = len(outcomes_sorted)  
    error_steps = [  
        int(rec["step_index"])  
        for rec in outcomes_sorted  
        if str(rec.get("status")) == "error" and _as_int(rec.get("step_index")) is not None  
    ]  
    run_status = "error" if any(str(rec.get("status")) == "error" for rec in outcomes_sorted) else "ok"  
  
    started = None  
    finished = None  
    if isinstance(manifest, Mapping):  
        ts = manifest.get("timestamps")  
        if isinstance(ts, Mapping):  
            started = ts.get("started_at_utc")  
            finished = ts.get("finished_at_utc")  
  
    report: dict[str, Any] = {  
        "schema": "REPORT-1A",  
        "run_output_dir": root.as_posix(),  
        "inputs": {  
            "history_manifest_path": (manifest_path.resolve().relative_to(root.resolve()).as_posix())  
            if manifest_path.exists()  
            else None,  
            "history_outcomes_path": (outcomes_path.resolve().relative_to(root.resolve()).as_posix())  
            if outcomes_path.exists()  
            else None,  
        },  
        "run": {  
            "status": run_status,  
            "timestamps": {  
                "started_at_utc": started,  
                "finished_at_utc": finished,  
            },  
        },  
        "summary": {  
            "total_steps": total_steps,  
            "status_counts": status_counts,  
            "error_steps": error_steps,  
        },  
        "manifest": manifest,  
        "step_outcomes": outcomes_sorted,  
    }  
    return report  
  
  
def write_run_report(  
    *,  
    run_output_dir: str | os.PathLike[str],  
    report: Mapping[str, Any],  
    overwrite: bool = True,  
) -> dict[str, Any]:  
    """  
    Write report to: {run_output_dir}/report/run_report.json  
    """  
    root = Path(run_output_dir)  
    out_path = root / "report" / "run_report.json"  
    out_path.parent.mkdir(parents=True, exist_ok=True)  
  
    if out_path.exists() and not overwrite:  
        raise FileExistsError(str(out_path))  
  
    out_path.write_bytes(_stable_json_bytes(dict(report)))  
  
    return {  
        "schema": "REPORT-1A-WRITE",  
        "path": str(out_path),  
        "path_relative": out_path.resolve().relative_to(root.resolve()).as_posix(),  
        "bytes": out_path.stat().st_size,  
    }  
  
  
def dev_smoke() -> None:  
    repo_root = Path(__file__).resolve().parents[1]  
    out_root = repo_root / "dev" / "_smoke_artifacts" / "10_3_1"  
  
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
  
    # Build history artifacts using 10.2.x modules  
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
  
    rec0 = build_step_outcome(  
        workflow_name="smoke_workflow",  
        step_index=0,  
        step={"action": "open", "url": "https://example.com"},  
        status="ok",  
        started_at_utc="2026-01-01T00:00:00+00:00",  
        finished_at_utc="2026-01-01T00:00:01+00:00",  
    )  
    rec1 = build_step_outcome(  
        workflow_name="smoke_workflow",  
        step_index=1,  
        step={"action": "click_selector", "selector_ref": "app.button.save"},  
        status="error",  
        started_at_utc="2026-01-01T00:00:01+00:00",  
        finished_at_utc="2026-01-01T00:00:02+00:00",  
        error=RuntimeError("boom"),  
    )  
    append_step_outcome(run_output_dir=out_root, outcome=rec0)  
    append_step_outcome(run_output_dir=out_root, outcome=rec1)  
  
    report = build_run_report(run_output_dir=out_root)  
    write_info = write_run_report(run_output_dir=out_root, report=report, overwrite=True)  
  
    assert report["schema"] == "REPORT-1A"  
    assert report["run"]["status"] == "error"  
    assert report["summary"]["total_steps"] == 2  
    assert report["summary"]["error_steps"] == [1]  
    assert report["summary"]["status_counts"]["ok"] == 1  
    assert report["summary"]["status_counts"]["error"] == 1  
  
    assert write_info["schema"] == "REPORT-1A-WRITE"  
    assert write_info["path_relative"] == "report/run_report.json"  
    saved = (out_root / "report" / "run_report.json").read_text(encoding="utf-8")  
    assert '"schema": "REPORT-1A"' in saved  
    # The report stores full relative paths like "history/run_manifest.json"  
    assert "run_manifest.json" in saved  
    assert "step_outcomes.jsonl" in saved  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: REPORT.report_1a_run_report")  