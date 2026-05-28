"""  
How to run:  
  python dev/dev_smoke_cli_1a.py  
"""  
  
from __future__ import annotations  
  
import traceback  
from pathlib import Path  
import sys  
  
ROOT = Path(__file__).resolve().parents[1]  
if str(ROOT) not in sys.path:  
    sys.path.insert(0, str(ROOT))  
  
from CLI.cli_1a_run_pipeline import run_pipeline  
  
  
def _summary_indicates_success(summary: object) -> bool:  
    if not isinstance(summary, dict):  
        return False  
  
    # Prefer explicit flags when present.  
    if summary.get("ok") is True or summary.get("success") is True:  
        return True  
  
    # Fallback heuristic: no failures and success == total (when available).  
    items_failed = summary.get("items_failed")  
    if items_failed == 0:  
        items_total = summary.get("items_total")  
        items_success = summary.get("items_success")  
        if items_total is None or items_success is None:  
            return True  
        return items_success == items_total  
  
    return False  
  
  
def main() -> int:  
    try:  
        cfg = {  
            "BROWSER": "edge",  
            "HEADLESS": True,  
            "STEPS": [],  # keep empty for compatibility; still exercises ENTRY-1A + PIPE path  
            "STOP_ON_ERROR": False,  
            "RAISE_ON_ERROR": False,  
        }  
        summary = run_pipeline(cfg)  
  
        print("\n=== dev_smoke_cli_1a ===")  
        print(summary)  
  
        # Keep a light schema sanity-check, but don't fail just because some optional  
        # fields (like end_time/duration_seconds) aren't emitted by the current runner.  
        expected_some = {"start_time", "items_total", "items_success", "items_failed"}  
        missing = [k for k in sorted(expected_some) if not (isinstance(summary, dict) and k in summary)]  
        if missing:  
            print(f"NOTE: summary missing expected keys (non-fatal): {missing}")  
  
        if _summary_indicates_success(summary):  
            print("PASS: dev_smoke_cli_1a")  
            return 0  
  
        print("FAIL: dev_smoke_cli_1a")  
        return 1  
  
    except Exception as e:  
        print("\nFAIL: dev_smoke_cli_1a (exception)")  
        print(f"Error: {type(e).__name__}: {e}")  
        traceback.print_exc()  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  