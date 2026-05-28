# dev_smoke_history_1a.py  
from __future__ import annotations  
  
import tempfile  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from HISTORY.history_1a_store import append_run_history, read_run_history, sanitize_run_record, summarize_history  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory() as td:  
        base = Path(td)  
        hp = base / "history" / "run_history.jsonl"  
  
        # 1) success  
        append_run_history(  
            {  
                "ts_utc": "2020-01-01T00:00:00Z",  
                "run_id": "r1",  
                "workflow": "example_workflow",  
                "success": True,  
                "duration_ms": 1234,  
                "token": "SHOULD_NOT_APPEAR",  
                "notes": ["ok"],  
            },  
            history_path=hp,  
        )  
  
        # 2) failure + category + suspicious keys  
        append_run_history(  
            {  
                "ts_utc": "2020-01-02T00:00:00Z",  
                "run_id": "r2",  
                "workflow_name": "example_workflow",  
                "success": False,  
                "failure_category": "SELECTOR_NOT_FOUND",  
                "password": "SHOULD_NOT_APPEAR",  
                "authorization": "SHOULD_NOT_APPEAR",  
                "traceback": "Traceback ... SHOULD_NOT_APPEAR",  
                "error_message": "Element not found",  
            },  
            history_path=hp,  
        )  
  
        # 3) success  
        append_run_history(  
            {  
                "ts_utc": "2020-01-03T00:00:00Z",  
                "run_id": "r3",  
                "workflow": "other_workflow",  
                "status": "ok",  
                "duration_seconds": 0.5,  
            },  
            history_path=hp,  
        )  
  
        rows = read_run_history(history_path=hp, limit=200)  
        assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}"  
  
        s = summarize_history(rows)  
        assert "success_rate" in s  
        assert "top_failure_categories" in s  
        assert s["total_runs"] == 3  
        assert s["last_run_ts"] == "2020-01-03T00:00:00Z"  
  
        # Verify sanitization behavior explicitly  
        sanitized = sanitize_run_record({"run_id": "rx", "token": "x", "password": "y", "notes": ["n"]})  
        # Canonical record should not carry token/password keys at all  
        assert "token" not in sanitized and "password" not in sanitized  
  
        # Ensure the written row doesn't contain forbidden key names  
        raw_text = hp.read_text(encoding="utf-8", errors="replace")  
        lowered = raw_text.lower()  
        assert "token" not in lowered  
        assert "password" not in lowered  
        assert "authorization" not in lowered  
        assert "traceback" not in lowered  
  
        print("PASS: HISTORY-1A")  
        print("History path:", hp.as_posix())  
        return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  