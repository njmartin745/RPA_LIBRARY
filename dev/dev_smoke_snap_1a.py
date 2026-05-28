# dev_smoke_snap_1a.py  
from __future__ import annotations  
  
import tempfile  
import traceback  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from SNAP.snap_1a_capture import capture_failure_artifacts  
  
  
def _make_driver_entry(cfg: dict):  
    # Use ENTRY-1A (best-effort tolerant import)  
    entry_mod = __import__("ENTRY.entry_1a_webdriver_bootstrap", fromlist=["*"])  
    fn = getattr(entry_mod, "make_driver", None)  
    if not callable(fn):  
        # fallback candidates  
        for name in ["create_driver", "bootstrap_driver", "build_driver", "get_driver"]:  
            fn2 = getattr(entry_mod, name, None)  
            if callable(fn2):  
                fn = fn2  
                break  
    if not callable(fn):  
        raise ValueError("ENTRY-1A driver factory not found (expected make_driver or compatible).")  
    try:  
        return fn(cfg)  # common convention  
    except TypeError:  
        return fn(cfg=cfg)  # alternate convention  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory() as td:  
        base = Path(td)  
        artifacts_dir = base / "artifacts"  
        run_id = "smoke-snap-1a"  
  
        driver = _make_driver_entry({"headless": True})  
        try:  
            driver.get("https://example.com")  
  
            try:  
                # Intentionally fail (synthetic) while passing driver  
                raise AssertionError("Synthetic failure: selector did not exist")  
            except Exception as e:  
                result = capture_failure_artifacts(  
                    run_id=run_id,  
                    output_dir=artifacts_dir,  
                    driver=driver,  
                    workflow_name="smoke_workflow",  
                    step_index=1,  
                    action="act.click",  
                    error_type=type(e).__name__,  
                    error_message=str(e),  
                    traceback_text=traceback.format_exc(),  
                    extra={"smoke": True},  
                )  
  
            out_dir = Path(result["base_dir"])  
            assert out_dir.exists(), "Artifacts directory was not created"  
            assert (out_dir / "failure.json").exists(), "failure.json missing"  
            assert (out_dir / "screenshot.png").exists(), "screenshot.png missing (driver supplied)"  
            assert (out_dir / "page.html").exists(), "page.html missing (driver supplied)"  
            assert (out_dir / "page.json").exists(), "page.json missing (driver supplied)"  
  
            print("PASS: SNAP-1A")  
            print("Artifact folder:", out_dir.as_posix())  
            return 0  
  
        finally:  
            try:  
                driver.quit()  
            except Exception:  
                pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  