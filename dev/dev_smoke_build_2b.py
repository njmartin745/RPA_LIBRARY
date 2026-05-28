import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))  
  
from BUILD.build_2b_plan_optimizer import analyze_spec, optimize_spec  
  
  
def main() -> None:  
    naive_spec = {  
        "spec_version": "BUILD-2A",  
        "workflow_name": "Naive Spec (Inefficient)",  
        "vars": ["${URL}", "${USERNAME}", "${PASSWORD}"],  
        "steps": [  
            {"action": "log", "message": "Starting (log before open)"},  
            {"action": "open", "url": "${URL}"},  
            {"action": "log", "message": "Opened"},  
            {"action": "wait_for_selector", "selector_ref": "LOGIN_USERNAME"},  
            {"action": "wait_for_selector", "selector_ref": "LOGIN_USERNAME"},  # duplicate wait  
            {"action": "type_selector_secret", "selector_ref": "LOGIN_USERNAME", "secret": "${USERNAME}"},  
            {"action": "type_selector_secret", "selector_ref": "LOGIN_PASSWORD", "secret": "${PASSWORD}"},  # missing wait  
            {"action": "click_selector", "selector_ref": "LOGIN_SUBMIT"},  # missing wait  
            {"action": "wait_for_selector", "selector_ref": "POST_LOGIN_LANDMARK"},  
            {"action": "wait_for_selector", "selector_ref": "POST_LOGIN_LANDMARK"},  # duplicate wait  
            # repeated wait+click pair (should consolidate into repeat)  
            {"action": "wait_for_selector", "selector_ref": "CATALOG_VIEW_TAB"},  
            {"action": "click_selector", "selector_ref": "CATALOG_VIEW_TAB"},  
            {"action": "wait_for_selector", "selector_ref": "CATALOG_VIEW_TAB"},  
            {"action": "click_selector", "selector_ref": "CATALOG_VIEW_TAB"},  
            # export readiness (should be wrapped into polling repeat)  
            {"action": "wait_for_selector", "selector_ref": "EXPORT_READY"},  
            {"action": "click_selector", "selector_ref": "EXPORT_DOWNLOAD", "name": "Export Excel"},  
        ],  
        "workflow": {"name": "Naive Spec (Inefficient)", "steps": []},  
    }  
    naive_spec["workflow"]["steps"] = naive_spec["steps"]  
  
    before = len(naive_spec["steps"])  
    analysis = analyze_spec(naive_spec)  
    optimized = optimize_spec(naive_spec)  
    after = len(optimized["steps"])  
  
    assert optimized.get("optimized") is True  
    assert isinstance(optimized.get("optimizations_applied"), list)  
    assert len(optimized["optimizations_applied"]) >= 1  
  
    # "reduced or improved": either fewer steps OR a repeat block was introduced  
    has_repeat = any(s.get("action") == "repeat" for s in optimized["steps"])  
    assert (after <= before) or has_repeat  
  
    # Ensure we didn't lose steps list  
    assert isinstance(optimized["steps"], list) and len(optimized["steps"]) > 0  
  
    print("dev_smoke_build_2b.py: PASS")  
    print("Before steps:", before, "After steps:", after)  
    print("Applied:", optimized["optimizations_applied"])  
    if optimized.get("warnings"):  
        print("Warnings:", optimized["warnings"])  
    print(json.dumps(optimized, indent=2))  
  
  
if __name__ == "__main__":  
    main()  