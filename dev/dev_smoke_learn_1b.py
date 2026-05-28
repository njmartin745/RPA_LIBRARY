import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
  
from LEARN.learn_1b_selector_intelligence import (  
    analyze_selector_stability,  
    generate_selector_recommendations,  
)  
  
  
def main() -> None:  
    rows = [  
        # selector used with mixed success/failure (flaky)  
        {"run_id": "R1", "workflow_name": "WF-A", "status": "failed", "error_category": "selector", "selector_ref": "LOGIN_SUBMIT"},  
        {"run_id": "R2", "workflow_name": "WF-A", "status": "success", "selector_ref": "LOGIN_SUBMIT"},  
        {"run_id": "R3", "workflow_name": "WF-B", "status": "failed", "error_category": "timeout", "selector_ref": "LOGIN_SUBMIT"},  
        {"run_id": "R4", "workflow_name": "WF-B", "status": "success", "selector_ref": "LOGIN_SUBMIT"},  
        # stable selector (mostly successes)  
        {"run_id": "R5", "workflow_name": "WF-A", "status": "success", "selector_ref": "POST_LOGIN_LANDMARK"},  
        {"run_id": "R6", "workflow_name": "WF-A", "status": "success", "selector_ref": "POST_LOGIN_LANDMARK"},  
        {"run_id": "R7", "workflow_name": "WF-A", "status": "success", "selector_ref": "POST_LOGIN_LANDMARK"},  
        # another unstable selector in one workflow  
        {"run_id": "R8", "workflow_name": "WF-C", "status": "failed", "error_category": "selector", "strategy": "css", "selector": "#export"},  
        {"run_id": "R9", "workflow_name": "WF-C", "status": "failed", "error_category": "selector", "strategy": "css", "selector": "#export"},  
    ]  
  
    analysis = analyze_selector_stability(rows)  
    assert isinstance(analysis, dict)  
    assert len(analysis.get("selectors", [])) >= 1  
  
    low = analysis.get("low_stability", [])  
    assert isinstance(low, list) and len(low) >= 1  
    assert all("stability_score" in s for s in low)  
  
    recs = generate_selector_recommendations(analysis)  
    assert isinstance(recs, list) and len(recs) >= 1  
  
    print("dev_smoke_learn_1b.py: PASS")  
    print(json.dumps({"analysis": analysis, "recommendations": recs}, indent=2))  
  
  
if __name__ == "__main__":  
    main()  