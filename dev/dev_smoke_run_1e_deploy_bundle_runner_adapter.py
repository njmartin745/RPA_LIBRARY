from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_3c_deploy_bundle_builder import build_stamp_validate_deploy_bundle_1a  
from RUN.run_1e_deploy_bundle_runner_adapter import run_deploy_bundle_1a, run_deploy_bundle_1a_with_meta  
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
  
    def stub_runner(workflow, selector_pack, run_meta):  
        assert workflow["steps"][0]["action"] == "open"  
        assert "selectors" in selector_pack  
        assert run_meta["bundle_name"] == "captured"  
        return {"ran": True}  
  
    r1 = run_deploy_bundle_1a(dep, runner=stub_runner, validate=True)  
    assert r1 == {"ran": True}  
  
    r2, meta = run_deploy_bundle_1a_with_meta(dep, runner=stub_runner, validate=True)  
    assert r2 == {"ran": True}  
    assert meta["bundle_name"] == "captured"  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  