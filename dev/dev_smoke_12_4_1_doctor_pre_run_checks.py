from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))   
    
from DOCTOR.doctor_12a_pre_run_checks import (  
    get_doctor_policy,  
    evaluate_doctor_policy,  
    policy_to_json,  
    render_policy_markdown,  
    decision_to_json,  
    render_decision_markdown,  
    write_policy_markdown,  
)  
  
  
def main() -> int:  
    try:  
        policy = get_doctor_policy()  
  
        # Deterministic policy render  
        js1 = policy_to_json(policy)  
        js2 = policy_to_json(policy)  
        assert js1 == js2  
        md = render_policy_markdown(policy)  
        assert "Pre-run DOCTOR Checks" in md  
        assert "Environment: prod" in md  
  
        # Failing decision (missing evidence)  
        fail_dec = evaluate_doctor_policy(policy, env="prod", evidence={})  
        assert fail_dec.passed is False  
        assert "webdriver_ready" in fail_dec.missing_evidence  
  
        # Passing decision  
        evidence = {  
            "webdriver_ready": True,  
            "workflow_loaded": True,  
            "selectors_loaded": True,  
            "secrets_resolved": True,  
            "output_dir_writable": True,  
            "target_reachable": True,  
        }  
        pass_dec = evaluate_doctor_policy(policy, env="prod", evidence=evidence)  
        assert pass_dec.passed is True  
        assert pass_dec.failed_checks == []  
        assert pass_dec.missing_evidence == []  
  
        # Deterministic decision render  
        djs = decision_to_json(pass_dec)  
        dmd = render_decision_markdown(pass_dec)  
        assert '"passed": true' in djs  
        assert "Passed:" in dmd  
  
        # Write/read markdown artifact  
        with tempfile.TemporaryDirectory() as td:  
            out_md = os.path.join(td, "doctor_policy.md")  
            write_policy_markdown(out_md, policy)  
            with open(out_md, "r", encoding="utf-8") as f:  
                md_written = f.read()  
            assert md_written == md  
  
        print("PASS: dev_smoke_12_4_1_doctor_pre_run_checks")  
        return 0  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_4_1_doctor_pre_run_checks :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  