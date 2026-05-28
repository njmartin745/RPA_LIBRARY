"""  
How to run:  
  python dev/dev_smoke_state_1d.py  
"""  
  
from __future__ import annotations  
  
import json  
import tempfile  
import traceback  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from typing import Any, Dict, Optional  
  
from LOG.log_1b_error_taxonomy import classify_exception  
from STATE.state_1d_manifest_row_helpers import row_failure, row_queued, row_success, write_row  
  
  
def _resolve_open_manifest():  
    """  
    Resolve STATE-1B open_manifest(cfg) without assuming exact module name.  
    """  
    candidates = [  
        ("STATE.state_1b_manifest_writer", "open_manifest"),  
        ("STATE.state_1b", "open_manifest"),  
    ]  
    for mod_name, fn in candidates:  
        try:  
            m = __import__(mod_name, fromlist=[fn])  
            f = getattr(m, fn, None)  
            if callable(f):  
                return f  
        except Exception:  
            continue  
  
    # Scan STATE.* for open_manifest  
    try:  
        import pkgutil, importlib  
  
        pkg = importlib.import_module("STATE")  
        for mi in pkgutil.iter_modules(pkg.__path__, prefix=pkg.__name__ + "."):  
            try:  
                m = importlib.import_module(mi.name)  
            except Exception:  
                continue  
            f = getattr(m, "open_manifest", None)  
            if callable(f):  
                return f  
    except Exception:  
        pass  
  
    raise RuntimeError("Could not resolve STATE-1B open_manifest(cfg).")  
  
  
def _read_jsonl(path: Path):  
    rows = []  
    for line in path.read_text(encoding="utf-8").splitlines():  
        if line.strip():  
            rows.append(json.loads(line))  
    return rows  
  
  
def main() -> int:  
    writer: Optional[Any] = None  
    try:  
        open_manifest = _resolve_open_manifest()  
  
        with tempfile.TemporaryDirectory(prefix="dev_smoke_state_1d_") as td:  
            manifest_path = Path(td) / "manifest.jsonl"  
            cfg: Dict[str, Any] = {"MANIFEST_PATH": str(manifest_path)}  
  
            writer = open_manifest(cfg)  
  
            write_row(writer, row_queued(run_id="R1", item_id="I1", step="start", reason="queued for processing"))  
            write_row(writer, row_success(run_id="R1", item_id="I1", step="done", details={"count": 1}))  
            err = classify_exception(ValueError("boom"))  
            write_row(writer, row_failure(run_id="R1", item_id="I1", step="fail_step", error=err))  
  
            # close if writer supports it  
            for meth in ("close", "flush"):  
                fn = getattr(writer, meth, None)  
                if callable(fn):  
                    try:  
                        fn()  
                    except Exception:  
                        pass  
  
            rows = _read_jsonl(manifest_path)  
            ok = True  
            ok = ok and (len(rows) == 3)  
            ok = ok and (rows[0].get("status") == "queued")  
            ok = ok and (rows[1].get("status") == "success")  
            ok = ok and (rows[2].get("status") == "fail")  
  
            print("\n=== dev_smoke_state_1d ===")  
            print(f"manifest_path: {manifest_path}")  
            print(f"rows: {rows}")  
  
            if ok:  
                print("PASS: dev_smoke_state_1d")  
                return 0  
            print("FAIL: dev_smoke_state_1d")  
            return 1  
  
    except Exception as e:  
        print("\nFAIL: dev_smoke_state_1d (exception)")  
        print(f"Error: {type(e).__name__}: {e}")  
        traceback.print_exc()  
        return 1  
  
    finally:  
        # attempt close  
        try:  
            if writer is not None:  
                fn = getattr(writer, "close", None)  
                if callable(fn):  
                    fn()  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  