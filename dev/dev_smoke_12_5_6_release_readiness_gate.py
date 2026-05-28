from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from DOCTOR.doctor_12d_release_readiness_gate import (  
    CheckObservation,  
    get_readiness_policy,  
    validate_readiness_policy,  
    evaluate_readiness,  
    policy_to_json,  
    render_policy_markdown,  
    decision_to_json,  
    render_decision_markdown,  
    write_policy_markdown,  
)  
  
  
def main() -> int:  
    try:  
        policy = get_readiness_policy()  
        errs = validate_readiness_policy(policy)  
        assert errs == [], f"Policy validation errors: {errs}"  
  
        # Deterministic policy rendering  
        pj1 = policy_to_json(policy)  
        pj2 = policy_to_json(policy)  
        assert pj1 == pj2  
        pmd = render_policy_markdown(policy)  
        assert "Release Readiness Gate" in pmd  
  
        # Evaluate with a missing required check and a failing critical check (prod)  
        obs = {  
            "lint.steps_valid": CheckObservation(True, "schema OK"),  
            "workflow.loaded": CheckObservation(False, "bundle load failed"),  
            "replay.index_verified": CheckObservation(True, "verified"),  
            "alerts.signals_passed": CheckObservation(True, "healthy window"),  
            # "audit.log_present" intentionally missing  
            "retention.policy_valid": CheckObservation(True, "validated"),  
            "incident.packet_ready": CheckObservation(True, "template ready"),  
            "extra.non_policy_metric": CheckObservation(False, "ignored as extra"),  
        }  
  
        d1 = evaluate_readiness(policy, env="prod", observations=obs)  
        d2 = evaluate_readiness(policy, env="prod", observations=obs)  
        assert decision_to_json(d1) == decision_to_json(d2)  
  
        assert d1.passed is False  
        assert any((r.check_id == "workflow.loaded" and r.passed is False) for r in d1.results)  
        assert any((r.check_id == "audit.log_present" and r.passed is False and r.message == "Missing observation") for r in d1.results)  
  
        md = render_decision_markdown(d1)  
        assert "Release Readiness Decision" in md  
        assert "Results" in md  
  
        # Write/read markdown artifact  
        with tempfile.TemporaryDirectory() as td:  
            out_md = os.path.join(td, "readiness_policy.md")  
            write_policy_markdown(out_md, policy)  
            with open(out_md, "r", encoding="utf-8") as f:  
                pmd2 = f.read()  
            assert pmd2 == pmd  
  
        print("PASS: dev_smoke_12_5_6_release_readiness_gate")  
        return 0  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_5_6_release_readiness_gate :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  