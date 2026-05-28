"""  
How to run:  
  python dev/dev_smoke_log_1b.py  
"""  
  
from __future__ import annotations  

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from LOG.log_1b_error_taxonomy import (  
    TIMEOUT,  
    CONFIG_ERROR,  
    SELECTOR_NOT_FOUND,  
    classify_exception,  
)  
  
def main() -> int:  
    ok = True  
  
    # 1) TimeoutError -> TIMEOUT  
    try:  
        raise TimeoutError("operation timed out")  
    except Exception as e:  
        d = classify_exception(e)  
        ok = ok and (d["code"] == TIMEOUT)  
  
    # 2) ValueError("bad config") -> CONFIG_ERROR  
    try:  
        raise ValueError("bad config: password=hunter2")  
    except Exception as e:  
        d = classify_exception(e)  
        ok = ok and (d["code"] == CONFIG_ERROR)  
        ok = ok and ("hunter2" not in d["message"])  # redacted  
  
    # 3) Selenium NoSuchElementException if available; otherwise mock by class name  
    try:  
        try:  
            from selenium.common.exceptions import NoSuchElementException  # type: ignore  
            raise NoSuchElementException("no such element: css selector")  
        except Exception:  
            # mock  
            NoSuchElementException = type("NoSuchElementException", (Exception,), {})  
            raise NoSuchElementException("no such element")  
    except Exception as e:  
        d = classify_exception(e)  
        ok = ok and (d["code"] == SELECTOR_NOT_FOUND)  
  
    print("\n=== dev_smoke_log_1b ===")  
    if ok:  
        print("PASS: dev_smoke_log_1b")  
        return 0  
    print("FAIL: dev_smoke_log_1b")  
    return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  