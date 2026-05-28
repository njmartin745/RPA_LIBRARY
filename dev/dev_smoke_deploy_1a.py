import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
from DEPLOY.deploy_1a_service_runner import run_service  
  
  
def main() -> None:  
    calls = {"n": 0}  
  
    def run_fn(workflow_path: str, cfg=None):  
        calls["n"] += 1  
        return {"success": True, "run_id": f"SMOKE-{calls['n']:02d}", "workflow": workflow_path}  
  
    workflows = ["WORKFLOWS/wf_a.json", "WORKFLOWS/wf_b.json"]  
  
    # Stop after 2 cycles via cfg["max_cycles"] (allowed for smoke simulation).  
    run_service(  
        workflows=workflows,  
        interval_seconds=1,  
        cfg={  
            "max_cycles": 2,  
            "run_fn": run_fn,  # ensures AGENT-2A doesn't invoke real Selenium in smoke  
            "workflow_name": "DEPLOY-1A-SMOKE",  
        },  
    )  
  
    assert calls["n"] == 2 * len(workflows)  
    print("dev_smoke_deploy_1a.py: PASS")  
  
  
if __name__ == "__main__":  
    main()  