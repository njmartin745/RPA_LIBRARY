from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from SNAP.snap_1a_workflow_capture import CapturedEvent, captured_events_to_steps  
from SNAP.snap_1b_selector_pack import (  
    build_selector_pack,  
    build_selector_ref_map,  
    selectors_from_captured_events,  
)  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    events = [  
        CapturedEvent(kind="click", seq=1, selector="#login"),  
        CapturedEvent(kind="change", seq=2, selector="input[name=\"username\"]", value="alice"),  
        CapturedEvent(kind="navigate", seq=3, url="https://example.test/app"),  
    ]  
  
    selectors = selectors_from_captured_events(events, include_kinds=("click", "change"))  
    ref_map = build_selector_ref_map(selectors, ref_prefix="cap")  
    pack = build_selector_pack(ref_map, pack_name="captured")  
  
    assert pack["name"] == "captured"  
    assert "#login" in ref_map  
  
    # Integration: step generation should prefer selector_ref when provided  
    steps = captured_events_to_steps(  
        events,  
        selector_ref_map=ref_map,  
        include_clicks=True,  
        include_navigation=False,  
        include_changes=False,  
    )  
    assert steps and steps[0]["action"] == "click_selector"  
    assert "selector_ref" in steps[0]  
    assert "selector" not in steps[0]  
  
    # Determinism  
    selectors2 = selectors_from_captured_events(list(reversed(events)), include_kinds=("click", "change"))  
    ref_map2 = build_selector_ref_map(selectors2, ref_prefix="cap")  
    pack2 = build_selector_pack(ref_map2, pack_name="captured")  
    assert selectors == selectors2  
    assert ref_map == ref_map2  
    assert pack == pack2  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  