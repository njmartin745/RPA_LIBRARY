"""  
How to run:  
  python dev/dev_smoke_val_1b.py  
"""  
  
from __future__ import annotations  
  
import tempfile  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT)) 
  
from VAL.val_1b_download_validation import validate_download  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory(prefix="dev_smoke_val_1b_") as td:  
        d = Path(td)  
        p = d / "smoke_download.txt"  
        p.write_text("hello\n", encoding="utf-8")  
  
        result = validate_download(  
            download_dir=str(d),  
            glob="smoke_*.txt",  
            min_size_bytes=1,  
        )  
  
        print("\n=== dev_smoke_val_1b ===")  
        print(result)  
  
        ok = bool(result.get("ok")) and result.get("path") == str(p) and (result.get("size_bytes") or 0) > 0  
        if ok:  
            print("PASS: dev_smoke_val_1b")  
            return 0  
        print("FAIL: dev_smoke_val_1b")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  