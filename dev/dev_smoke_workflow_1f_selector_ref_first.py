from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from WORKFLOW.workflow_1f_selector_ref_first import enforce_selector_ref_first_in_bundle  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    bundle = {  
        "schema_id": "CAPTURE_BUNDLE_1A",  
        "name": "captured",  
        "workflow": {  
            "steps": [  
                {"action": "click_selector", "selector": " #login "},  
                {"action": "repeat", "times": 2, "steps": [{"action": "wait_for_selector", "selector": "#login"}]},  
                {"action": "open", "url": "https://example.test/app"},  
            ]  
        },  
        "selector_pack": {  
            "schema_id": "SELECTOR_PACK_1A",  
            "name": "captured",  
            "selectors": {  
                "cap_010": {"selector": "#login", "type": "css"},  
            },  
        },  
    }  
  
    out = enforce_selector_ref_first_in_bundle(bundle, strict=False)  
  
    s0 = out["workflow"]["steps"][0]  
    assert s0["action"] == "click_selector"  
    assert s0["selector_ref"] == "cap_010"  
    assert "selector" not in s0  
  
    s1 = out["workflow"]["steps"][1]["steps"][0]  
    assert s1["action"] == "wait_for_selector"  
    assert s1["selector_ref"] == "cap_010"  
    assert "selector" not in s1  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  