from __future__ import annotations  
  
import tempfile  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
  
from SNAP.snap_1a_workflow_capture import CapturedEvent  
from SNAP.snap_1c_capture_bundle import build_capture_bundle_from_events, validate_capture_bundle  
from SNAP.snap_1d_bundle_io import load_capture_bundle_json  
from SNAP.snap_1e_bundle_export import export_capture_bundle_assets  
  
__all__ = ["dev_smoke"]  
  
  
def _repo_root() -> Path:  
    return Path(__file__).resolve().parent.parent  
  
  
def dev_smoke() -> None:  
    events = [  
        CapturedEvent(kind="click", seq=1, selector="#login"),  
        CapturedEvent(kind="navigate", seq=2, url="https://example.test/app"),  
    ]  
    bundle = build_capture_bundle_from_events(events, bundle_name="captured")  
  
    # Ensure registry compatibility before export  
    validate_capture_bundle(bundle, repo_root=_repo_root(), require_registry_compat=True)  
  
    with tempfile.TemporaryDirectory() as td:  
        paths = export_capture_bundle_assets(bundle, td, repo_root=_repo_root(), validate=True)  
  
        loaded_bundle = load_capture_bundle_json(paths["bundle"])  
        loaded_wf = load_capture_bundle_json(paths["workflow"])  
        loaded_sp = load_capture_bundle_json(paths["selector_pack"])  
  
        assert loaded_bundle == bundle  
        assert loaded_wf == bundle["workflow"]  
        assert loaded_sp == bundle["selector_pack"]  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  