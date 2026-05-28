# dev_smoke_obs_1a.py  
from __future__ import annotations  

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from OBS.obs_1a_run_timeline import create_run_timeline, finalize_timeline, record_step_event  
  
  
def main() -> int:  
    tl = create_run_timeline(run_id="smoke-run-obs-1a", workflow_name="smoke-workflow")  
  
    record_step_event(tl, 0, "nav.goto", "ok", url="https://example.com", duration_ms=120)  
    record_step_event(tl, 1, "act.click", "failed", selector="h1", duration_ms=50, metadata={"reason": "simulated"})  
    record_step_event(tl, 2, "out.save", "ok", duration_ms=30)  
  
    tl2 = finalize_timeline(tl)  
  
    assert isinstance(tl2, dict)  
    assert isinstance(tl2.get("summary"), dict)  
    assert tl2["summary"]["steps_total"] == 3  
    assert tl2["summary"]["steps_ok"] >= 1  
  
    print("OBS-1A summary:")  
    print(tl2["summary"])  
    print("PASS: OBS-1A")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  