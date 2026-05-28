# dev_smoke_guard_1a.py  
from __future__ import annotations  

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from GUARD.guard_1a_runtime import wrap_step_runner  
  
try:  
    from selenium.common.exceptions import StaleElementReferenceException  # type: ignore  
except Exception:  
    class StaleElementReferenceException(Exception):  
        pass  
  
  
def main() -> int:  
    # Case 1: retryable exception once, then success  
    calls = {"n": 0}  
  
    def fake_step_runner(driver, steps, cfg):  
        calls["n"] += 1  
        if calls["n"] == 1:  
            raise StaleElementReferenceException("stale once")  
        return {"ok": True, "calls": calls["n"]}  
  
    wrapped = wrap_step_runner(fake_step_runner, cfg={"GUARD_ENABLED": True, "GUARD_RETRIES": 1})  
    res = wrapped(None, [{"action": "act.click"}], {})  
    assert isinstance(res, dict) and res.get("ok") is True  
    assert calls["n"] == 2, f"Expected 1 retry (2 total attempts); got calls={calls['n']}"  
  
    # Case 2: non-retry exception should not retry  
    calls2 = {"n": 0}  
  
    def fake_step_runner_valueerror(driver, steps, cfg):  
        calls2["n"] += 1  
        raise ValueError("do not retry")  
  
    wrapped2 = wrap_step_runner(fake_step_runner_valueerror, cfg={"GUARD_ENABLED": True, "GUARD_RETRIES": 3})  
    try:  
        wrapped2(None, [{"action": "act.click"}], {})  
        raise AssertionError("Expected ValueError to be raised")  
    except ValueError:  
        pass  
  
    assert calls2["n"] == 1, f"Expected no retry for ValueError; got calls={calls2['n']}"  
  
    print("PASS: GUARD-1A")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  