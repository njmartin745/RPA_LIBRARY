# dev_smoke_plan_1a.py  
from __future__ import annotations  
  
import json  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from LINT.lint_1a_steps_validator import validate_steps_file  
from PLAN.plan_1a_step_planner import generate_workflow_skeleton  
  
  
def _read_json(p: Path) -> object:  
    return json.loads(p.read_text(encoding="utf-8"))  
  
  
def main() -> int:  
    # 1) Run planner  
    intent = "Open example.com and wait for page load"  
    res = generate_workflow_skeleton(intent)  
  
    steps_path = Path(res["paths"]["steps_path"])  
    plan_path = Path(res["paths"]["plan_path"])  
  
    # 2) Confirm files created  
    assert steps_path.exists(), f"Missing: {steps_path}"  
    assert plan_path.exists(), f"Missing: {plan_path}"  
  
    # sanity check: steps JSON is parseable and non-empty list  
    steps_obj = _read_json(steps_path)  
    assert isinstance(steps_obj, list), "generated_steps.json must be a list of steps"  
    assert len(steps_obj) >= 1, "expected at least 1 step"  
  
    # 3) Validate using LINT-1A  
    report = validate_steps_file(steps_path)  
    assert report.get("valid") is True, f"Expected valid steps; got: {json.dumps(report, indent=2)}"  
  
    # 4) Print PASS banner  
    print("PASS: PLAN-1A")  
    print(f"  intent: {intent}")  
    print(f"  steps:  {steps_path.as_posix()}")  
    print(f"  plan:   {plan_path.as_posix()}")  
    print(f"  nsteps: {len(steps_obj)}")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  