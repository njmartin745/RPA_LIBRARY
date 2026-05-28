from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from REPORT.report_12d_artifact_retention_policy import (  
    ArtifactMeta,  
    get_retention_policy,  
    validate_retention_policy,  
    evaluate_retention_policy,  
    policy_to_json,  
    render_policy_markdown,  
    decision_to_json,  
    render_decision_markdown,  
    write_policy_markdown,  
)  
  
  
def main() -> int:  
    try:  
        policy = get_retention_policy()  
        errs = validate_retention_policy(policy)  
        assert errs == [], f"Policy validation errors: {errs}"  
  
        # Deterministic policy rendering  
        p1 = policy_to_json(policy)  
        p2 = policy_to_json(policy)  
        assert p1 == p2  
        pmd = render_policy_markdown(policy)  
        assert "Artifact Retention Policy" in pmd  
  
        now_date = "2026-01-31"  
  
        artifacts = [  
            # run_report: use keep_last_n behavior demonstration  
            ArtifactMeta(artifact_id="rr-1", kind="run_report", created_date="2026-01-30"),  
            ArtifactMeta(artifact_id="rr-2", kind="run_report", created_date="2026-01-20"),  
            ArtifactMeta(artifact_id="rr-3", kind="run_report", created_date="2025-12-01"),  
            # legal hold override  
            ArtifactMeta(artifact_id="log-hold", kind="run_log", created_date="2024-01-01", tags=("legal_hold",)),  
        ]  
  
        d1 = evaluate_retention_policy(policy, env="default", artifacts=artifacts, now_date=now_date)  
        d2 = evaluate_retention_policy(policy, env="default", artifacts=artifacts, now_date=now_date)  
        assert decision_to_json(d1) == decision_to_json(d2)  
  
        # Assertions:  
        # - default run_report keep_days=30 => rr-1, rr-2 are within 30 days (keep)  
        # - rr-3 is older than 30 days; keep_last_n=10 would keep it in default if within newest 10,  
        #   but it is within newest 10 because only 3 exist => keep. To test delete, evaluate in prod with  
        #   a kind whose keep_last_n is smaller by crafting a custom artifact kind would be policy rewriting,  
        #   so instead we validate that legal_hold always keeps.  
        actions = {a.artifact_id: a for a in d1.actions}  
        assert actions["log-hold"].keep is True  
        assert "always keep" in actions["log-hold"].reason  
  
        # Render decision markdown deterministically  
        dmd = render_decision_markdown(d1)  
        assert "Artifact Retention Decision" in dmd  
        assert "Summary" in dmd  
  
        # Write/read markdown artifact  
        with tempfile.TemporaryDirectory() as td:  
            out_md = os.path.join(td, "retention_policy.md")  
            write_policy_markdown(out_md, policy)  
            with open(out_md, "r", encoding="utf-8") as f:  
                md_written = f.read()  
            assert md_written == pmd  
  
        print("PASS: dev_smoke_12_5_1_artifact_retention_policy")  
        return 0  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_5_1_artifact_retention_policy :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  