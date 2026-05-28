from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_3a_deploy_bundle_format import build_deploy_bundle_from_capture_bundle  
from SNAP.snap_1a_workflow_capture import CapturedEvent  
from SNAP.snap_1c_capture_bundle import build_capture_bundle_from_events  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    events = [  
        CapturedEvent(kind="navigate", seq=1, url="https://example.test/app"),  
        CapturedEvent(kind="click", seq=2, selector="#login"),  
    ]  
    cap = build_capture_bundle_from_events(events, bundle_name="captured")  
  
    dep = build_deploy_bundle_from_capture_bundle(cap, strict=True)  
  
    assert dep["schema_id"] == "DEPLOY_BUNDLE_1A"  
    assert dep["name"] == "captured"  
    assert "workflow" in dep and "selector_pack" in dep  
    assert dep["meta"]["source_schema_id"] == "CAPTURE_BUNDLE_1A"  
  
    # Selector pack exists, click step should be selector_ref-first already (or enforced)  
    steps = dep["workflow"]["steps"]  
    assert steps[1]["action"] == "click_selector"  
    assert "selector_ref" in steps[1]  
    assert "selector" not in steps[1]  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  