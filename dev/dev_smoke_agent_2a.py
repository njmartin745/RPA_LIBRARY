import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))   
  
from AGENT.agent_2a_autonomous_loop import run_autonomous  
  
  
def main() -> None:  
    # Seed a history file with one prior failure so attempt-1 creates a repeated pattern (count>=2).  
    history_path = Path(".dev_tmp/agent_2a_smoke_history.jsonl")  
    history_path.parent.mkdir(parents=True, exist_ok=True)  
    history_path.write_text(  
        json.dumps(  
            {  
                "run_id": "SEED-1",  
                "workflow_name": "WF-SMOKE",  
                "status": "failed",  
                "error_category": "selector",  
                "step_action": "click_selector",  
                "selector_ref": "LOGIN_SUBMIT",  
            }  
        )  
        + "\n",  
        encoding="utf-8",  
    )  
  
    calls = {"n": 0}  
  
    def run_fn(workflow_path: str, cfg=None):  
        calls["n"] += 1  
        if calls["n"] == 1:  
            return {  
                "success": False,  
                "run_id": "R-FAIL-1",  
                "error_category": "selector",  
                "selector_ref": "LOGIN_SUBMIT",  
            }  
        return {"success": True, "run_id": "R-OK-2"}  
  
    def snap_fn(run_result, cfg=None):  
        return {"ok": True, "snap": "noop"}  
  
    def reason_fn(run_result, cfg=None):  
        return {"category": run_result.get("error_category"), "selector_ref": run_result.get("selector_ref")}  
  
    def heal_fn(workflow_path: str, diagnosis=None, cfg=None):  
        # Simulate "no patch" on first failure (must be handled gracefully)  
        return None  
  
    def report_fn(run_result, cfg=None):  
        return ".dev_tmp/final_report_smoke.json"  
  
    out = run_autonomous(  
        "WORKFLOWS/workflow_1a_smoke.json",  
        max_attempts=3,  
        cfg={  
            "workflow_name": "WF-SMOKE",  
            "history_path": str(history_path),  
            "run_fn": run_fn,  
            "snap_fn": snap_fn,  
            "reason_fn": reason_fn,  
            "heal_fn": heal_fn,  
            "report_fn": report_fn,  
        },  
    )  
  
    assert out["attempts"] >= 2  
    assert out["success"] is True  
    assert isinstance(out.get("recommendations"), list) and len(out["recommendations"]) >= 1  
  
    print("dev_smoke_agent_2a.py: PASS")  
    print(json.dumps(out, indent=2))  
  
  
if __name__ == "__main__":  
    main()  