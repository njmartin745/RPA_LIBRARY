import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))   
  
from LEARN.learn_1a_failure_patterns import (  
    extract_failure_patterns,  
    rank_patterns,  
    generate_recommendations,  
)  
  
  
def main() -> None:  
    # Synthetic history rows with repeated failures  
    rows = [  
        {  
            "run_id": "R1",  
            "workflow_name": "WF-A",  
            "status": "failed",  
            "error_category": "selector",  
            "step_action": "click_selector",  
            "selector_ref": "LOGIN_SUBMIT",  
        },  
        {  
            "run_id": "R2",  
            "workflow_name": "WF-A",  
            "status": "failed",  
            "error_category": "selector",  
            "step_action": "click_selector",  
            "selector_ref": "LOGIN_SUBMIT",  
        },  
        {  
            "run_id": "R3",  
            "workflow_name": "WF-A",  
            "status": "failed",  
            "error_category": "timeout",  
            "step_action": "wait_for_selector",  
            "selector_ref": "EXPORT_READY",  
        },  
        {  
            "run_id": "R4",  
            "workflow_name": "WF-A",  
            "status": "failed",  
            "error_category": "timeout",  
            "step_action": "wait_for_selector",  
            "selector_ref": "EXPORT_READY",  
        },  
        {  
            "run_id": "R5",  
            "workflow_name": "WF-B",  
            "status": "failed",  
            "error_category": "diff",  
            "diff_fingerprint": "FP-123",  
        },  
        {  
            "run_id": "R6",  
            "workflow_name": "WF-B",  
            "status": "failed",  
            "error_category": "diff",  
            "diff_fingerprint": "FP-123",  
        },  
        # success row (should be ignored)  
        {"run_id": "R7", "workflow_name": "WF-A", "status": "success"},  
    ]  
  
    patterns = extract_failure_patterns(rows)  
    assert isinstance(patterns, dict)  
    assert len(patterns.get("patterns", [])) >= 1  
  
    ranked = rank_patterns(patterns)  
    assert isinstance(ranked, list)  
    assert len(ranked) >= 1  
    # ensure sorted by count desc  
    counts = [p["count"] for p in ranked]  
    assert counts == sorted(counts, reverse=True)  
  
    recs = generate_recommendations(ranked)  
    assert isinstance(recs, list)  
    assert len(recs) >= 1  
  
    print("dev_smoke_learn_1a.py: PASS")  
    print(json.dumps({"patterns": patterns["patterns"], "ranked": ranked, "recommendations": recs}, indent=2))  
  
  
if __name__ == "__main__":  
    main()  