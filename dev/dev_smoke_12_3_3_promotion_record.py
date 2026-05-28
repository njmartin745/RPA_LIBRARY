from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from REGISTRY.reg_12b_promotion_gates import get_promotion_policy, evaluate_promotion  
from REPORT.report_12a_release_manifest import build_release_manifest  
from REPORT.report_12b_bundle_fingerprint import compute_bundle_fingerprint  
from REPORT.report_12c_promotion_record import (  
    build_promotion_record,  
    promotion_record_to_json,  
    render_promotion_record_markdown,  
    write_promotion_record_json,  
    write_promotion_record_markdown,  
)  
  
  
def main() -> int:  
    try:  
        policy = get_promotion_policy()  
  
        with tempfile.TemporaryDirectory() as td:  
            wf_path = os.path.join(td, "workflow.json")  
            sel_path = os.path.join(td, "selectors.json")  
  
            with open(wf_path, "wb") as f:  
                f.write(b'{"name":"demo","steps":[{"type":"log","message":"hello"}]}\n')  
            with open(sel_path, "wb") as f:  
                f.write(b'{"selectors":{"login_button":"#login"}}\n')  
  
            manifest = build_release_manifest(  
                workflow_version="1.0.0",  
                selectors_version="1.2.3",  
                framework_version="2.0.0",  
                workflow_path=wf_path,  
                selectors_path=sel_path,  
            )  
            fingerprint = compute_bundle_fingerprint(manifest)  
  
            evidence = {  
                "lint_steps_validator_passed": True,  
                "reviewable_diffs_attached": "PASS",  
                "smoke_suite_passed": True,  
                "bundle_fingerprint_recorded": True,  
                "bundle_version_recorded": True,  
                "doctor_checks_passed": True,  
                "change_control_approved": "YES",  
                # prove normalization supports nested JSON:  
                "ci": {"job": "build", "checks": ["lint", "smoke"]},  
            }  
  
            decision = evaluate_promotion(  
                policy,  
                from_env="stage",  
                to_env="prod",  
                evidence=evidence,  
            )  
            assert decision.allowed is True  
  
            record = build_promotion_record(  
                policy_id=policy.policy_id,  
                decision=decision,  
                manifest=manifest,  
                fingerprint=fingerprint,  
                evidence=evidence,  
                redacted_keys=["nonexistent_key"],  # should be harmless  
            )  
  
            js = promotion_record_to_json(record)  
            md = render_promotion_record_markdown(record)  
  
            assert js.strip().startswith("{")  
            assert '"fingerprint"' in js and '"manifest"' in js and '"decision"' in js  
            assert "Promotion Record" in md  
            assert fingerprint.fingerprint in md  
  
            out_json = os.path.join(td, "promotion_record.json")  
            out_md = os.path.join(td, "promotion_record.md")  
            write_promotion_record_json(out_json, record)  
            write_promotion_record_markdown(out_md, record)  
  
            with open(out_json, "r", encoding="utf-8") as f:  
                js_written = f.read()  
            with open(out_md, "r", encoding="utf-8") as f:  
                md_written = f.read()  
  
            assert js_written == js  
            assert md_written == md  
  
        print("PASS: dev_smoke_12_3_3_promotion_record")  
        return 0  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_3_3_promotion_record :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  