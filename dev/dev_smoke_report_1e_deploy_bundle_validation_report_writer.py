from __future__ import annotations  
  
import json  
import os  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_3c_deploy_bundle_builder import build_stamp_validate_deploy_bundle_1a  
from REPORT.report_1e_deploy_bundle_validation_report_writer import (  
    derive_deploy_bundle_validation_report_path_1a,  
    write_deploy_bundle_validation_report_alongside_1a,  
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
  
    bundle_path = os.path.join("dev", "_smoke_deploy_bundle_1a.json")  
    report_path = derive_deploy_bundle_validation_report_path_1a(bundle_path)  
  
    with open(bundle_path, "w", encoding="utf-8") as f:  
        json.dump(dep, f, ensure_ascii=False, sort_keys=True, indent=2)  
  
    try:  
        out_path, report = write_deploy_bundle_validation_report_alongside_1a(bundle_path, overwrite=True)  
        assert out_path == report_path  
        assert report["schema_id"] == "DEPLOY_BUNDLE_VALIDATION_REPORT_1A"  
        assert report["bundle"]["expected_schema_id"] == "DEPLOY_BUNDLE_1A"  
        assert report["validation"]["ok"] is True  
  
        with open(out_path, "r", encoding="utf-8") as f:  
            persisted = json.load(f)  
        assert persisted["validation"]["ok"] is True  
  
        print("PASS")  
    finally:  
        for p in (bundle_path, report_path):  
            try:  
                os.remove(p)  
            except Exception:  
                pass  
  
  
if __name__ == "__main__":  
    dev_smoke()  