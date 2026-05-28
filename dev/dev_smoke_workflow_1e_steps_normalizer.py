from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from WORKFLOW.workflow_1e_steps_normalizer import normalize_capture_bundle_workflow  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    bundle = {  
        "schema_id": "CAPTURE_BUNDLE_1A",  
        "name": " captured ",  
        "workflow": {  
            "steps": [  
                {"action": " open ", "url": " https://example.test/app "},  
                {"action": "click_selector", "selector_ref": " cap_001 ", "x": None},  
                {"action": "repeat", "times": " 2 ", "steps": [{"action": "wait_for_selector", "selector": " #a "}]},  
            ]  
        },  
        "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "captured", "selectors": {}},  
    }  
  
    out = normalize_capture_bundle_workflow(bundle, strict=True)  
  
    assert out is not bundle  
    assert out["workflow"]["steps"][0]["action"] == "open"  
    assert out["workflow"]["steps"][0]["url"] == "https://example.test/app"  
    assert out["workflow"]["steps"][1]["selector_ref"] == "cap_001"  
    assert "x" not in out["workflow"]["steps"][1]  
    assert out["workflow"]["steps"][2]["times"] == 2  
    assert out["workflow"]["steps"][2]["steps"][0]["selector"] == "#a"  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  