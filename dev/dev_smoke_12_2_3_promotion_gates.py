from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from REGISTRY.reg_12b_promotion_gates import (  
    get_promotion_policy,  
    evaluate_promotion,  
    render_promotion_policy_markdown,  
    promotion_policy_to_json,  
    write_promotion_policy_markdown,  
)  
  
  
def main() -> int:  
    try:  
        policy = get_promotion_policy()  
  
        md = render_promotion_policy_markdown(policy)  
        assert "Environment Promotion Gates Policy" in md  
        assert "dev → stage" in md  
        assert "stage → prod" in md  
        assert "GATE-VAL-001" in md  
  
        js = promotion_policy_to_json(policy)  
        assert js.strip().startswith("{")  
        assert '"paths"' in js and '"gates"' in js  
  
        # Should fail with missing evidence  
        dec_missing = evaluate_promotion(  
            policy,  
            from_env="stage",  
            to_env="prod",  
            evidence={"lint_steps_validator_passed": True},  
        )  
        assert dec_missing.allowed is False  
        assert "GATE-CC-001" in dec_missing.failed_gates or "GATE-OPS-001" in dec_missing.failed_gates  
        assert len(dec_missing.missing_evidence) >= 1  
  
        # Should pass with complete evidence  
        dec_ok = evaluate_promotion(  
            policy,  
            from_env="stage",  
            to_env="prod",  
            evidence={  
                "lint_steps_validator_passed": True,  
                "reviewable_diffs_attached": "PASS",  
                "smoke_suite_passed": True,  
                "bundle_fingerprint_recorded": True,  
                "bundle_version_recorded": True,  
                "doctor_checks_passed": True,  
                "change_control_approved": "YES",  
            },  
        )  
        assert dec_ok.allowed is True  
        assert dec_ok.failed_gates == []  
  
        # I/O determinism  
        with tempfile.TemporaryDirectory() as td:  
            out_path = os.path.join(td, "promotion_gates_policy.md")  
            write_promotion_policy_markdown(out_path)  
            assert os.path.exists(out_path)  
            with open(out_path, "r", encoding="utf-8") as f:  
                written = f.read()  
            assert written == md  
  
        print("PASS: dev_smoke_12_2_3_promotion_gates")  
        return 0  
  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_2_3_promotion_gates :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  