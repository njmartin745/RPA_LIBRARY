# dev_smoke_replay_1a.py  
from __future__ import annotations  
  
import json  
import os  
import tempfile  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
  
from REPLAY.replay_1a_run_replay import replay_run  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory() as td:  
        base = Path(td)  
  
        # Arrange: minimal workflows/ + artifacts/ structure inside temp  
        workflows_dir = base / "workflows"  
        artifacts_dir = base / "artifacts"  
        workflows_dir.mkdir(parents=True, exist_ok=True)  
        artifacts_dir.mkdir(parents=True, exist_ok=True)  
  
        wf_name = "example_workflow"  
        wf_path = workflows_dir / f"{wf_name}.json"  
        wf_path.write_text(  
            json.dumps(  
                {  
                    "name": wf_name,  
                    "steps": [  
                        {"action": "nav.goto", "url": "https://example.com"},  
                        {"action": "act.click", "selector_ref": "example.h1"},  
                        {"action": "out.save", "path": "out.json"},  
                    ],  
                },  
                indent=2,  
            )  
            + "\n",  
            encoding="utf-8",  
        )  
  
        run_id = "smoke-replay-1a"  
        run_dir = artifacts_dir / run_id  
        run_dir.mkdir(parents=True, exist_ok=True)  
        (run_dir / "failure.json").write_text(  
            json.dumps(  
                {  
                    "run_id": run_id,  
                    "workflow_name": wf_name,  
                    "step_index": 1,  
                    "action": "act.click",  
                    "error_type": "NoSuchElementException",  
                    "error_message": "Unable to locate element",  
                    "timestamp_utc": "2020-01-01T00:00:00Z",  
                    "driver_unavailable": True,  
                    "paths": {"failure_json": str((run_dir / "failure.json").as_posix())},  
                    "capture_errors": [],  
                },  
                indent=2,  
            )  
            + "\n",  
            encoding="utf-8",  
        )  
  
        # Ensure fallback resolver can find workflows/<name>.json by running in temp base  
        old_cwd = os.getcwd()  
        os.chdir(base.as_posix())  
        try:  
            summary = replay_run(run_id, artifacts_dir="artifacts", dry_run=True)  
        finally:  
            os.chdir(old_cwd)  
  
        assert isinstance(summary, dict)  
        assert summary["replay_of"] == run_id  
        assert isinstance(summary.get("workflow"), str) and summary["workflow"].endswith(f"{wf_name}.json")  
        assert "success" in summary and isinstance(summary["success"], bool)  
        assert "steps_executed" in summary and isinstance(summary["steps_executed"], int)  
        assert isinstance(summary.get("notes"), list)  
  
        print("PASS: REPLAY-1A")  
        return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  