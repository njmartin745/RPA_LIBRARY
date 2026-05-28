import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
  
from AGENT.agent_2b_scheduler import run_continuous  
  
  
def main() -> None:  
    # Use a dedicated history file to keep test deterministic and isolated.  
    history_path = Path(".dev_tmp/agent_2b_smoke_history.jsonl")  
    history_path.parent.mkdir(parents=True, exist_ok=True)  
    history_path.write_text("", encoding="utf-8")  
  
    calls = {"n": 0}  
  
    def run_fn(workflow_path: str, cfg=None):  
        calls["n"] += 1  
        return {"success": True, "run_id": f"R-{calls['n']:02d}"}  
  
    out = run_continuous(  
        "WORKFLOWS/workflow_1a_smoke.json",  
        interval_seconds=1,  
        max_cycles=2,  
        cfg={  
            "history_path": str(history_path),  
            "workflow_name": "WF-AGENT-2B-SMOKE",  
            "run_fn": run_fn,  # ensures no real Selenium  
        },  
    )  
  
    assert out["cycles"] == 2  
    assert isinstance(out["runs"], list) and len(out["runs"]) == 2  
    assert out["success_count"] + out["failure_count"] == 2  
  
    print("dev_smoke_agent_2b.py: PASS")  
    print(json.dumps(out, indent=2))  
  
  
if __name__ == "__main__":  
    main()  