from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_2e_workflow_grammar_gate import (  
    assert_workflow_supported_actions,  
    find_workflow_unsupported_actions,  
    sanitize_workflow_steps,  
)  
  
  
def main() -> None:  
    wf_ok = {  
        "name": "ok",  
        "steps": [  
            {"action": "open", "url": "https://example.test"},  
            {"action": "log", "message": "hi"},  
            {  
                "action": "repeat",  
                "times": 1,  
                "steps": [{"action": "wait_for_selector", "strategy": "css", "selector": "body"}],  
            },  
        ],  
    }  
    assert_workflow_supported_actions(wf_ok)  
  
    wf_bad = {  
        "name": "bad",  
        "steps": [  
            {"action": "log", "message": "keep"},  
            {"action": "wait_seconds", "seconds": 1},  
            {"action": "look_for_selector", "strategy": "css", "selector": "#x"},  
            {  
                "action": "repeat",  
                "times": 1,  
                "steps": [  
                    {"action": "log", "message": "keep2"},  
                    {"action": "wait_seconds", "seconds": 2},  
                ],  
            },  
        ],  
    }  
  
    v = find_workflow_unsupported_actions(wf_bad)  
    assert [x.action for x in v] == ["wait_seconds", "look_for_selector", "wait_seconds"]  
  
    try:  
        assert_workflow_supported_actions(wf_bad)  
        raise AssertionError("Expected ValueError for unsupported actions, but none was raised.")  
    except ValueError:  
        pass  
  
    gated = sanitize_workflow_steps(wf_bad)  
    assert [x.action for x in gated.violations] == ["wait_seconds", "look_for_selector", "wait_seconds"]  
    assert gated.sanitized_workflow["steps"] == [  
        {"action": "log", "message": "keep"},  
        {"action": "repeat", "times": 1, "steps": [{"action": "log", "message": "keep2"}]},  
    ]  
    assert_workflow_supported_actions(gated.sanitized_workflow)  
  
    print("dev_smoke_build_2e: OK")  
  
  
if __name__ == "__main__":  
    main()  