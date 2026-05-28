from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_3a_deploy_bundle_format import build_deploy_bundle_from_capture_bundle  
from BUILD.build_3b_bundle_fingerprint import stamp_bundle_version_and_fingerprint  
from SNAP.snap_1a_workflow_capture import CapturedEvent  
from SNAP.snap_1c_capture_bundle import build_capture_bundle_from_events  
from VAL.val_2a_deploy_bundle_validator import validate_deploy_bundle_1a  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    events = [  
        CapturedEvent(kind="navigate", seq=1, url="https://example.test/app"),  
        CapturedEvent(kind="click", seq=2, selector="#login"),  
    ]  
    cap = build_capture_bundle_from_events(events, bundle_name="captured")  
    dep = build_deploy_bundle_from_capture_bundle(cap, strict=True)  
    dep = stamp_bundle_version_and_fingerprint(dep)  
  
    rep = validate_deploy_bundle_1a(dep, require_version_fingerprint=True, require_selector_ref=True)  
    assert rep["ok"] is True  
  
    broken = dict(dep)  
    broken["workflow"] = dict(dep["workflow"])  
    broken["workflow"]["steps"] = [dict(dep["workflow"]["steps"][0])]  
    broken["workflow"]["steps"].append({"action": "click_selector", "selector_ref": "missing_ref"})  
    rep2 = validate_deploy_bundle_1a(broken, require_version_fingerprint=True, require_selector_ref=True)  
    assert rep2["ok"] is False  
    assert any(e["path"].endswith("/selector_ref") and "not found" in e["message"] for e in rep2["errors"])  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  