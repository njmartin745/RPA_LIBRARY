"""  
How to run:  
  python dev/dev_smoke_state_1c.py  
"""  
  
from __future__ import annotations  
  
import json  
import tempfile  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT)) 
  
from STATE.state_1c_retry_helpers import extract_failed_ids, read_manifest_rows, write_retry_manifest  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory(prefix="dev_smoke_state_1c_") as td:  
        base = Path(td)  
        manifest_path = base / "manifest.jsonl"  
        retry_path = base / "manifest_retry.jsonl"  
  
        # Mixed rows: at least 2 fails, plus a duplicate fail ID to test de-dupe + stable order.  
        rows = [  
            {"ACCOUNT_ID": "A100", "status": "success"},  
            {"ACCOUNT_ID": "A200", "status": "fail", "error": "redacted"},  
            {"ACCOUNT_ID": "A300", "status": "failed"},  
            {"ACCOUNT_ID": "A200", "status": "fail"},  # duplicate failed id  
            {"ACCOUNT_ID": "A400", "status": "queued"},  
        ]  
  
        # Write manifest JSONL with a blank line included.  
        with manifest_path.open("w", encoding="utf-8", newline="\n") as f:  
            for r in rows:  
                f.write(json.dumps(r, ensure_ascii=False) + "\n")  
            f.write("\n")  
  
        loaded = read_manifest_rows(manifest_path)  
        failed_ids = extract_failed_ids(loaded)  
  
        outp = write_retry_manifest(retry_path, failed_ids, id_field="ACCOUNT_ID")  
        reloaded_retry = read_manifest_rows(outp)  
  
        ok = True  
        ok = ok and (failed_ids == ["A200", "A300"])  
        ok = ok and (len(reloaded_retry) == 2)  
        ok = ok and all(isinstance(r, dict) and r.get("status") == "queued" for r in reloaded_retry)  
        ok = ok and all(r.get("ACCOUNT_ID") in {"A200", "A300"} for r in reloaded_retry)  
  
        print("\n=== dev_smoke_state_1c ===")  
        print(f"manifest_path: {manifest_path}")  
        print(f"retry_path:    {outp}")  
        print(f"failed_count:  {len(failed_ids)}")  
        print(f"retry_count:   {len(reloaded_retry)}")  
  
        if ok:  
            print("PASS: dev_smoke_state_1c")  
            return 0  
  
        print("FAIL: dev_smoke_state_1c")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  