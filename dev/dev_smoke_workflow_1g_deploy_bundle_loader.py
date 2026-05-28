from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_3c_deploy_bundle_builder import build_stamp_validate_deploy_bundle_1a  
from SNAP.snap_1a_workflow_capture import CapturedEvent  
from SNAP.snap_1c_capture_bundle import build_capture_bundle_from_events  
from WORKFLOWS.workflow_1g_deploy_bundle_loader import (  
    extract_runnable_from_deploy_bundle_1a,  
    load_deploy_bundle_1a,  
)  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    events = [  
        CapturedEvent(kind="navigate", seq=1, url="https://example.test/app"),  
        CapturedEvent(kind="click", seq=2, selector="#login"),  
    ]  
    cap = build_capture_bundle_from_events(events, bundle_name="captured")  
    dep = build_stamp_validate_deploy_bundle_1a(cap, strict=True)  
  
    loaded = load_deploy_bundle_1a(dep, validate=True)  
    wf, sp, meta = extract_runnable_from_deploy_bundle_1a(loaded)  
  
    assert wf["steps"][1]["action"] == "click_selector"  
    assert "selector_ref" in wf["steps"][1]  
    assert "selectors" in sp  
    assert meta["bundle_name"] == "captured"  
    assert meta["bundle_version"].startswith("sha256:")  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  