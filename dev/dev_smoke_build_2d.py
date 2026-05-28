from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 

from BUILD.build_2d_step_grammar_gate import (  
    ALLOWED_ACTIONS,  
    assert_supported_actions,  
    strip_unsupported_actions,  
)  
  
  
def main() -> None:  
    # Valid (includes nested repeat)  
    steps_ok = [  
        {"action": "open", "url": "https://example.test"},  
        {"action": "log", "message": "hello"},  
        {  
            "action": "repeat",  
            "times": 1,  
            "name": "inner",  
            "steps": [  
                {"action": "exec_js", "script": "return { ok: true }"},  
                {"action": "wait_for_selector", "strategy": "css", "selector": "body"},  
            ],  
        },  
    ]  
    assert_supported_actions(steps_ok, allowed_actions=ALLOWED_ACTIONS)  
  
    # Invalid action should raise  
    steps_bad = [{"action": "wait_seconds", "seconds": 1}]  
    try:  
        assert_supported_actions(steps_bad, allowed_actions=ALLOWED_ACTIONS)  
        raise AssertionError("Expected ValueError for unsupported action, but none was raised.")  
    except ValueError:  
        pass  
  
    # Strip unsupported actions (deterministic)  
    steps_mixed = [  
        {"action": "log", "message": "keep"},  
        {"action": "wait_seconds", "seconds": 2},  
        {  
            "action": "repeat",  
            "times": 1,  
            "steps": [  
                {"action": "look_for_selector", "strategy": "id", "selector": "x"},  
                {"action": "log", "message": "keep2"},  
            ],  
        },  
    ]  
    sanitized = strip_unsupported_actions(steps_mixed, allowed_actions=ALLOWED_ACTIONS)  
    assert sanitized == [  
        {"action": "log", "message": "keep"},  
        {"action": "repeat", "times": 1, "steps": [{"action": "log", "message": "keep2"}]},  
    ]  
  
    print("dev_smoke_build_2d: OK")  
  
  
if __name__ == "__main__":  
    main()  