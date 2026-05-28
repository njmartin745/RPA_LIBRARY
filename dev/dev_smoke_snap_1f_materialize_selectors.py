from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from SNAP.snap_1a_workflow_capture import CapturedEvent  
from SNAP.snap_1c_capture_bundle import build_capture_bundle_from_events  
from SNAP.snap_1f_materialize_selectors import materialize_selector_refs_in_bundle  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    events = [  
        CapturedEvent(kind="click", seq=1, selector="#login"),  
        CapturedEvent(kind="navigate", seq=2, url="https://example.test/app"),  
    ]  
    bundle = build_capture_bundle_from_events(events, bundle_name="captured")  
  
    steps = bundle["workflow"]["steps"]  
    assert steps[0]["action"] == "click_selector"  
    assert "selector_ref" in steps[0]  # capture bundle is selector_ref-first  
  
    mat = materialize_selector_refs_in_bundle(bundle, drop_selector_ref=True)  
    msteps = mat["workflow"]["steps"]  
    assert msteps[0]["action"] == "click_selector"  
    assert "selector" in msteps[0]  
    assert msteps[0]["selector"] == "#login"  
    assert "selector_ref" not in msteps[0]  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  