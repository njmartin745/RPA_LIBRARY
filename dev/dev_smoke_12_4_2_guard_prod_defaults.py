from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
     
from GUARD.guard_12a_prod_defaults import (  
    get_guard_policy,  
    evaluate_guard_policy,  
    policy_to_json,  
    render_policy_markdown,  
    decision_to_json,  
    render_decision_markdown,  
    write_policy_markdown,  
)  
  
  
def main() -> int:  
    try:  
        policy = get_guard_policy()  
  
        # Deterministic render  
        js1 = policy_to_json(policy)  
        js2 = policy_to_json(policy)  
        assert js1 == js2  
        md = render_policy_markdown(policy)  
        assert "Production Defaults" in md  
        assert "prod" in md  
  
        selectors = {"selectors": {"login_button": "#login"}}  
  
        passing_workflow = {  
            "name": "pass",  
            "steps": [  
                {"type": "open", "url": "https://example.com/login"},  
                {"type": "wait_for_selector", "selector_ref": "login_button"},  
                {"type": "click_selector", "selector_ref": "login_button"},  
                {"type": "log", "message": "ok"},  
            ],  
        }  
  
        pass_dec = evaluate_guard_policy(policy, env="prod", workflow=passing_workflow, selectors=selectors)  
        assert pass_dec.passed is True  
        assert pass_dec.violations == []  
  
        failing_workflow = {  
            "name": "fail",  
            "steps": [  
                {"type": "open", "url": "http://example.com/login"},  # not https  
                {"type": "exec_js", "script": "return 1;"},          # disallowed in prod  
                {"type": "click_selector", "selector": "#raw"},      # raw selector disallowed in prod  
                {"type": "wait_for_selector", "selector_ref": "missing_ref"},  # unresolved selector_ref  
            ],  
        }  
  
        fail_dec = evaluate_guard_policy(policy, env="prod", workflow=failing_workflow, selectors=selectors)  
        assert fail_dec.passed is False  
        assert len(fail_dec.violations) >= 3  
  
        djs = decision_to_json(fail_dec)  
        dmd = render_decision_markdown(fail_dec)  
        assert '"passed": false' in djs  
        assert "Violations" in dmd  
  
        # Write/read markdown artifact  
        with tempfile.TemporaryDirectory() as td:  
            out_md = os.path.join(td, "guard_policy.md")  
            write_policy_markdown(out_md, policy)  
            with open(out_md, "r", encoding="utf-8") as f:  
                md_written = f.read()  
            assert md_written == md  
  
        print("PASS: dev_smoke_12_4_2_guard_prod_defaults")  
        return 0  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_4_2_guard_prod_defaults :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  