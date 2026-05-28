from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_3c_deploy_bundle_builder import (  
    build_stamp_validate_deploy_bundle_1a,  
    build_stamp_validate_deploy_bundle_1a_with_report,  
)  
from SNAP.snap_1a_workflow_capture import CapturedEvent  
from SNAP.snap_1c_capture_bundle import build_capture_bundle_from_events  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    events = [  
        CapturedEvent(kind="navigate", seq=1, url="https://example.test/app"),  
        CapturedEvent(kind="click", seq=2, selector="#login"),  
    ]  
    cap = build_capture_bundle_from_events(events, bundle_name="captured")  
  
    dep = build_stamp_validate_deploy_bundle_1a(cap, strict=True)  
    assert dep["schema_id"] == "DEPLOY_BUNDLE_1A"  
    assert dep["name"] == "captured"  
    assert dep["version"].startswith("sha256:")  
    assert dep["fingerprint"]["algo"] == "sha256"  
    assert len(dep["fingerprint"]["sha256"]) == 64  
  
    dep2, rep2 = build_stamp_validate_deploy_bundle_1a_with_report(cap, strict=True)  
    assert dep2["fingerprint"]["sha256"] == dep["fingerprint"]["sha256"]  
    assert rep2["ok"] is True  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  