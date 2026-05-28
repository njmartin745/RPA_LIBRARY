"""  
How to run:  
  python dev/dev_smoke_out_1a.py  
"""  
  
from __future__ import annotations  
  
import tempfile  
import threading  
import time  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT)) 
  
from OUT.out_1a_download_wait import wait_for_download  
  
  
def _simulate_download(target: Path) -> None:  
    # Create file after a short delay, then append again to test stability logic.  
    time.sleep(0.8)  
    target.write_text("part1\n", encoding="utf-8")  
    time.sleep(0.8)  
    with target.open("a", encoding="utf-8") as f:  
        f.write("part2\n")  
        f.flush()  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory(prefix="dev_smoke_out_1a_") as td:  
        d = Path(td)  
        p = d / "report.csv"  
  
        t = threading.Thread(target=_simulate_download, args=(p,), daemon=True)  
        t.start()  
  
        result = wait_for_download(  
            download_dir=str(d),  
            glob="*.csv",  
            timeout_sec=10,  
            poll_sec=0.2,  
            min_size_bytes=1,  
            stable_sec=0.7,  
            clear_before=True,  
        )  
  
        print("\n=== dev_smoke_out_1a ===")  
        print(result)  
  
        ok = bool(result.get("ok")) and result.get("path") == str(p) and (result.get("size_bytes") or 0) >= 10  
        if ok:  
            print("PASS: dev_smoke_out_1a")  
            return 0  
  
        print("FAIL: dev_smoke_out_1a")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  