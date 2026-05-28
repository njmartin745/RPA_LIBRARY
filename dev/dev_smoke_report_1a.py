# dev_smoke_report_1a.py  
from __future__ import annotations  
  
import json  
import tempfile  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
  
from REPORT.report_1a_generate import generate_report  
  
  
def _load_json(p: Path) -> dict:  
    return json.loads(p.read_text(encoding="utf-8"))  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory() as td:  
        base = Path(td)  
        artifacts_dir = base / "artifacts"  
        reports_dir = base / "reports"  
        run_id = "smoke-report-1a"  
  
        run_art = artifacts_dir / run_id  
        run_art.mkdir(parents=True, exist_ok=True)  
  
        (run_art / "failure.json").write_text(  
            json.dumps(  
                {  
                    "run_id": run_id,  
                    "workflow_name": "example_workflow",  
                    "step_index": 2,  
                    "action": "act.click",  
                    "error_type": "NoSuchElementException",  
                    "error_message": "Unable to locate element: #missing",  
                    "timestamp_utc": "2020-01-01T00:00:00Z",  
                    "driver_unavailable": True,  
                    "paths": {"failure_json": "failure.json"},  
                    "capture_errors": [],  
                    "extra": {"cfg": {"headless": True, "timeout": 10}},  
                },  
                indent=2,  
            )  
            + "\n",  
            encoding="utf-8",  
        )  
  
        (run_art / "page.json").write_text(  
            json.dumps({"url": "https://example.com", "title": "Example Domain"}, indent=2) + "\n",  
            encoding="utf-8",  
        )  
  
        (run_art / "traceback.txt").write_text("Traceback (most recent call last):\n  ...\n", encoding="utf-8")  
  
        (run_art / "timeline.json").write_text(  
            json.dumps(  
                {  
                    "run_id": run_id,  
                    "workflow_name": "example_workflow",  
                    "steps": [{"step_index": 0, "action": "nav.goto", "status": "ok"}],  
                },  
                indent=2,  
            )  
            + "\n",  
            encoding="utf-8",  
        )  
  
        # REASON-style diagnosis with fixes (so agent_next_actions can be derived)  
        (run_art / "diagnosis.json").write_text(  
            json.dumps(  
                {  
                    "category": "SELECTOR_NOT_FOUND",  
                    "confidence": 0.9,  
                    "title": "Element not found",  
                    "fixes": [  
                        {"rank": 2, "fix": "Add explicit wait", "why": "Element loads late", "probe": "Log readyState", "headless_note": ""},  
                        {"rank": 1, "fix": "Update selector_ref", "why": "Selector drift", "probe": "Capture selector", "headless_note": ""},  
                    ],  
                },  
                indent=2,  
            )  
            + "\n",  
            encoding="utf-8",  
        )  
  
        res = generate_report(  
            run_id,  
            artifacts_dir=artifacts_dir,  
            reports_dir=reports_dir,  
            include_html=True,  
            include_md=True,  
            include_json=True,  
        )  
  
        out_dir = Path(res["reports_dir"])  
        assert out_dir.exists()  
        assert (out_dir / "report.json").exists() and (out_dir / "report.json").stat().st_size > 10  
        assert (out_dir / "report.md").exists()  
        assert (out_dir / "report.html").exists()  
  
        report_obj = _load_json(out_dir / "report.json")  
        assert isinstance(report_obj.get("agent_next_actions"), list)  
        assert len(report_obj["agent_next_actions"]) >= 1, "Expected agent_next_actions derived from diagnosis/patch presence"  
  
        print("PASS: REPORT-1A")  
        print("Output directory:", out_dir.as_posix())  
        return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  