from __future__ import annotations  
  
import tempfile  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
  
from SNAP.snap_1a_workflow_capture import CapturedEvent  
from SNAP.snap_1c_capture_bundle import build_capture_bundle_from_events, validate_capture_bundle  
from SNAP.snap_1d_bundle_io import load_capture_bundle_json, save_capture_bundle_json  
  
__all__ = ["dev_smoke"]  
  
  
def _repo_root() -> Path:  
    return Path(__file__).resolve().parent.parent  
  
  
def dev_smoke() -> None:  
    events = [  
        CapturedEvent(kind="click", seq=1, selector="#login"),  
        CapturedEvent(kind="navigate", seq=2, url="https://example.test/app"),  
    ]  
    bundle = build_capture_bundle_from_events(events, bundle_name="captured")  
  
    # Validate before persisting  
    validate_capture_bundle(bundle, repo_root=_repo_root(), require_registry_compat=True)  
  
    with tempfile.TemporaryDirectory() as td:  
        path = Path(td) / "capture_bundle.json"  
        save_capture_bundle_json(path, bundle)  
  
        loaded = load_capture_bundle_json(path)  
        assert loaded == bundle  
  
        # Ensure newline-terminated deterministic output  
        raw = path.read_text(encoding="utf-8")  
        assert raw.endswith("\n")  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  