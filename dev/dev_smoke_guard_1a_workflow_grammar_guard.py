from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
from tempfile import TemporaryDirectory  
  
from GUARD.guard_1a_workflow_grammar_guard import (  
    WorkflowGrammarGuardConfig,  
    guard_workflow_dict_for_execution,  
    guard_workflow_path_for_execution,  
)  
  
  
def main() -> None:  
    wf_bad = {  
        "name": "bad",  
        "steps": [  
            {"action": "log", "message": "keep"},  
            {"action": "wait_seconds", "seconds": 1},  
            {"action": "look_for_selector", "strategy": "css", "selector": "#x"},  
        ],  
    }  
  
    # Dict guard: raise mode should give friendly message  
    try:  
        guard_workflow_dict_for_execution(wf_bad)  
        raise AssertionError("Expected ValueError, but none was raised.")  
    except ValueError as e:  
        msg = str(e)  
        assert "wait_seconds" in msg  
        assert "look_for_selector" in msg  
        assert "violation" in msg.lower()  
  
    # Dict guard: sanitize mode should strip  
    cfg = WorkflowGrammarGuardConfig(on_violation="sanitize")  
    wf_ok = guard_workflow_dict_for_execution(wf_bad, config=cfg)  
    assert wf_ok["steps"] == [{"action": "log", "message": "keep"}]  
  
    # Path guard  
    with TemporaryDirectory() as td:  
        p = Path(td) / "wf.json"  
        p.write_text(json.dumps(wf_bad), encoding="utf-8")  
  
        try:  
            guard_workflow_path_for_execution(p)  
            raise AssertionError("Expected ValueError, but none was raised.")  
        except ValueError as e:  
            msg = str(e)  
            assert "wf.json" in msg  
            assert "wait_seconds" in msg  
  
        wf_ok2 = guard_workflow_path_for_execution(p, config=cfg)  
        assert wf_ok2["steps"] == [{"action": "log", "message": "keep"}]  
  
    print("dev_smoke_guard_1a_workflow_grammar_guard: OK")  
  
  
if __name__ == "__main__":  
    main()  