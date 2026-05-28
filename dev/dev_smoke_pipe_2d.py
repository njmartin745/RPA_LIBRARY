"""  
How to run:  
  python dev/dev_smoke_pipe_2d.py  
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
      
from typing import Any, Dict  
  
from PIPE.pipe_2d_artifact_integration import handle_download_artifact  
  
  
def _resolve_open_manifest():  
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
    writer: Any = None  
    try:  
        open_manifest = _resolve_open_manifest()  
  
        with tempfile.TemporaryDirectory(prefix="dev_smoke_pipe_2d_") as td:  
            base = Path(td)  
            downloads = base / "downloads"  
            out_dir = base / "out"  
            manifest_path = base / "manifest.jsonl"  
  
            downloads.mkdir(parents=True, exist_ok=True)  
            out_dir.mkdir(parents=True, exist_ok=True)  
  
            dl_file = downloads / "report.xlsx"  
            dl_file.write_bytes(b"hello")  
  
            cfg: Dict[str, Any] = {  
                "MANIFEST_PATH": str(manifest_path),  
                "OUT_DIR": str(out_dir),  
                "ARTIFACT_BASE_NAME": "report",  
                "ARTIFACT_OVERWRITE": False,  
            }  
  
            writer = open_manifest(cfg)  
  
            res = handle_download_artifact(  
                download_path=dl_file,  
                cfg=cfg,  
                run_id="R1",  
                item_id="I1",  
                writer=writer,  
            )  
  
            # Close/flush writer if supported  
            for meth in ("flush", "close"):  
                fn = getattr(writer, meth, None)  
                if callable(fn):  
                    try:  
                        fn()  
                    except Exception:  
                        pass  
  
            ok = True  
            ok = ok and bool(res.get("ok")) is True  
            artifact_path = Path(res["artifact_path"])  
            ok = ok and artifact_path.exists()  
            ok = ok and (not dl_file.exists())  
  
            rows = _read_jsonl(manifest_path)  
            ok = ok and (len(rows) == 1)  
            ok = ok and (rows[0].get("status") == "success")  
            ok = ok and (rows[0].get("details", {}).get("artifact_path") == str(artifact_path))  
  
            print("\n=== dev_smoke_pipe_2d ===")  
            print(f"manifest_path: {manifest_path}")  
            print(f"artifact_path: {artifact_path}")  
            print(f"row: {rows[0] if rows else None}")  
  
            if ok:  
                print("PASS: dev_smoke_pipe_2d")  
                return 0  
            print("FAIL: dev_smoke_pipe_2d")  
            return 1  
  
    except Exception as e:  
        print("\nFAIL: dev_smoke_pipe_2d (exception)")  
        print(f"Error: {type(e).__name__}: {e}")  
        traceback.print_exc()  
        return 1  
    finally:  
        try:  
            if writer is not None:  
                fn = getattr(writer, "close", None)  
                if callable(fn):  
                    fn()  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  