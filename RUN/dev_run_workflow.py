# dev_run_workflow.py  
from __future__ import annotations  
  
import json  
import sys  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from RUN.run_1a_workflow_runner import run_workflow  
  
  
def main(argv: list[str]) -> int:  
    if len(argv) < 2:  
        print("Usage: python dev_run_workflow.py path/to/workflow.json [cfg_overrides_json]")  
        print('Example: python dev_run_workflow.py workflows/example_workflow.json \'{"headless": true}\'')  
        return 2  
  
    workflow_path = Path(argv[1])  
  
    cfg_overrides = None  
    if len(argv) >= 3:  
        try:  
            cfg_overrides = json.loads(argv[2])  
            if not isinstance(cfg_overrides, dict):  
                raise ValueError("cfg_overrides_json must decode to an object")  
        except Exception as e:  
            print(f"Invalid cfg_overrides_json: {e}")  
            return 2  
  
    summary = run_workflow(workflow_path, cfg_overrides=cfg_overrides)  
    print(json.dumps(summary, indent=2, ensure_ascii=False))  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main(sys.argv))  