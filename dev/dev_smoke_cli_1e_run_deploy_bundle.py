from __future__ import annotations  
  
import json  
import os  
from typing import Any, Dict, Mapping  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_3c_deploy_bundle_builder import build_stamp_validate_deploy_bundle_1a  
from CLI.cli_1e_run_deploy_bundle import run_deploy_bundle_path_1a  
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
  
    out_path = os.path.join("dev", "_smoke_deploy_bundle_1a.json")  
    with open(out_path, "w", encoding="utf-8") as f:  
        json.dump(dep, f, ensure_ascii=False, sort_keys=True, indent=2)  
  
    called = {"ok": False}  
  
    def stub_runner(*, workflow: Dict[str, Any], selector_pack: Dict[str, Any], run_meta: Dict[str, Any]) -> Dict[str, Any]:  
        assert workflow["steps"][0]["action"] == "open"  
        assert workflow["steps"][1]["action"] == "click_selector"  
        assert isinstance(selector_pack.get("selectors"), Mapping)  
        assert run_meta["bundle_name"] == "captured"  
        called["ok"] = True  
        return {"status": "ok"}  
  
    try:  
        result = run_deploy_bundle_path_1a(out_path, runner=stub_runner, validate=True)  
        assert result == {"status": "ok"}  
        assert called["ok"] is True  
        print("PASS")  
    finally:  
        try:  
            os.remove(out_path)  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    dev_smoke()  