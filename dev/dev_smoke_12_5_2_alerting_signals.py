from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from REPORT.report_12e_alerting_signals import (  
    get_alert_policy,  
    validate_alert_policy,  
    evaluate_alert_policy,  
    policy_to_json,  
    render_policy_markdown,  
    decision_to_json,  
    render_decision_markdown,  
    write_policy_markdown,  
)  
  
  
def main() -> int:  
    try:  
        policy = get_alert_policy()  
        errs = validate_alert_policy(policy)  
        assert errs == [], f"Policy validation errors: {errs}"  
  
        # Deterministic policy rendering  
        p1 = policy_to_json(policy)  
        p2 = policy_to_json(policy)  
        assert p1 == p2  
        pmd = render_policy_markdown(policy)  
        assert "Alerting Signals From Run Outcomes" in pmd  
  
        # Trigger critical alerts in prod deterministically  
        metrics_bad = {  
            "total_runs": 10,  
            "success_runs": 97 // 10,  # intentionally 9 (not 9.7) for int contract  
            "failed_runs": 1,  
            "consecutive_failures": 3,        # prod max is 2 => critical  
            "doctor_blocked_runs": 1,         # 10% => warning in prod  
            "guard_blocked_runs": 0,  
            "p95_duration_seconds": 240,      # > 180 => warning  
        }  
  
        # Fix the integer contract: success_runs must be int and success+failed <= total.  
        metrics_bad["success_runs"] = 9  
        metrics_bad["failed_runs"] = 1  
  
        d1 = evaluate_alert_policy(policy, env="prod", metrics=metrics_bad)  
        d2 = evaluate_alert_policy(policy, env="prod", metrics=metrics_bad)  
        assert decision_to_json(d1) == decision_to_json(d2)  
  
        assert d1.passed is False  
        assert any(a.severity == "critical" for a in d1.alerts)  
        assert any(a.signal_id == "signal.consecutive_failures_high" for a in d1.alerts)  
  
        # A clean-ish window should pass  
        metrics_ok = {  
            "total_runs": 10,  
            "success_runs": 10,  
            "failed_runs": 0,  
            "consecutive_failures": 0,  
            "doctor_blocked_runs": 0,  
            "guard_blocked_runs": 0,  
            "p95_duration_seconds": 120,  
        }  
        ok = evaluate_alert_policy(policy, env="prod", metrics=metrics_ok)  
        assert ok.passed is True  
  
        # Render decision markdown  
        dmd = render_decision_markdown(d1)  
        assert "Alerting Signals Decision" in dmd  
        assert "Alerts" in dmd  
  
        # Write/read markdown artifact  
        with tempfile.TemporaryDirectory() as td:  
            out_md = os.path.join(td, "alert_policy.md")  
            write_policy_markdown(out_md, policy)  
            with open(out_md, "r", encoding="utf-8") as f:  
                md_written = f.read()  
            assert md_written == pmd  
  
        print("PASS: dev_smoke_12_5_2_alerting_signals")  
        return 0  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_5_2_alerting_signals :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  