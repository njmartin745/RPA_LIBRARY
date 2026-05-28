"""  
How to run:  
  python dev/dev_smoke_pipe_2e.py  
"""  
  
from __future__ import annotations  
  
import traceback  

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from PIPE.pipe_2e_run_summary import (  
    finish_run_summary,  
    record_artifact,  
    record_item_failure,  
    record_item_success,  
    start_run_summary,  
)  
  
  
def main() -> int:  
    try:  
        s = start_run_summary("R1")  
        record_item_success(s, "I1")  
        record_item_success(s, "I2")  
        record_item_failure(s, "I3", error={"code": "CONFIG_ERROR", "type": "ValueError", "message": "boom"})  
        record_artifact(s, "/tmp/out/report.xlsx")  
        s2 = finish_run_summary(s)  
  
        ok = True  
        ok = ok and (s2.get("items_total") == 3)  
        ok = ok and (s2.get("items_success") == 2)  
        ok = ok and (s2.get("items_failed") == 1)  
        ok = ok and ("duration_seconds" in s2) and (s2["duration_seconds"] is None or s2["duration_seconds"] >= 0)  
        ok = ok and (s2.get("end_time") is not None)  
  
        print("\n=== dev_smoke_pipe_2e ===")  
        print(s2)  
  
        if ok:  
            print("PASS: dev_smoke_pipe_2e")  
            return 0  
        print("FAIL: dev_smoke_pipe_2e")  
        return 1  
  
    except Exception as e:  
        print("\nFAIL: dev_smoke_pipe_2e (exception)")  
        print(f"Error: {type(e).__name__}: {e}")  
        traceback.print_exc()  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  