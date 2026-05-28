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
from CLI.cli_1g_run_deploy_bundle_with_report_fail_fast import main  
from REPORT.report_1e_deploy_bundle_validation_report_writer import derive_deploy_bundle_validation_report_path_1a  
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
  
    # Make bundle "report-invalid" but still runnable if we pass --no-validate:  
    dep = dict(dep)  
    if "version" in dep:  
        del dep["version"]  
  
    bundle_path = os.path.join("dev", "_smoke_deploy_bundle_1a_missing_version.json")  
    report_path = derive_deploy_bundle_validation_report_path_1a(bundle_path)  
  
    with open(bundle_path, "w", encoding="utf-8") as f:  
        json.dump(dep, f, ensure_ascii=False, sort_keys=True, indent=2)  
  
    def stub_runner(*, workflow: Dict[str, Any], selector_pack: Dict[str, Any], run_meta: Dict[str, Any]) -> Dict[str, Any]:  
        assert workflow["steps"][0]["action"] == "open"  
        assert isinstance(selector_pack.get("selectors"), Mapping)  
        return {"status": "ok"}  
  
    try:  
        # Expect exit code 1 because report ok=false (missing version) and fail-fast enabled.  
        code1 = main(  
            [  
                bundle_path,  
                "--no-validate",  
                "--write-validation-report",  
                "--fail-if-report-not-ok",  
            ],  
            runner=stub_runner,  
        )  
        assert code1 == 1  
        assert os.path.exists(report_path)  
  
        # Expect exit code 0 when missing version is allowed (report ok=true).  
        code2 = main(  
            [  
                bundle_path,  
                "--no-validate",  
                "--write-validation-report",  
                "--fail-if-report-not-ok",  
                "--allow-missing-version-fingerprint",  
            ],  
            runner=stub_runner,  
        )  
        assert code2 == 0  
  
        print("PASS")  
    finally:  
        for p in (bundle_path, report_path):  
            try:  
                os.remove(p)  
            except Exception:  
                pass  
  
  
if __name__ == "__main__":  
    dev_smoke()  