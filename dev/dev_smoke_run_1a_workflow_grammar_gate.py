from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
from tempfile import TemporaryDirectory  
  
from RUN.run_1a_workflow_grammar_gate import (  
    gate_workflow_dict_for_run,  
    gate_workflow_path_for_run,  
)  
  
  
def main() -> None:  
    wf_bad = {  
        "name": "bad",  
        "steps": [  
            {"action": "log", "message": "keep"},  
            {"action": "wait_seconds", "seconds": 1},  
            {"action": "look_for_selector", "strategy": "css", "selector": "#x"},  
            {  
                "action": "repeat",  
                "times": 1,  
                "steps": [{"action": "wait_seconds", "seconds": 2}, {"action": "log", "message": "ok"}],  
            },  
        ],  
    }  
  
    # Dict gating: raise mode should fail  
    try:  
        gate_workflow_dict_for_run(wf_bad, on_violation="raise")  
        raise AssertionError("Expected ValueError for unsupported actions, but none was raised.")  
    except ValueError:  
        pass  
  
    # Dict gating: sanitize mode should strip unsupported actions  
    out = gate_workflow_dict_for_run(wf_bad, on_violation="sanitize")  
    assert [v.action for v in out.violations] == ["wait_seconds", "look_for_selector", "wait_seconds"]  
    assert out.workflow["steps"] == [  
        {"action": "log", "message": "keep"},  
        {"action": "repeat", "times": 1, "steps": [{"action": "log", "message": "ok"}]},  
    ]  
  
    # Path gating  
    with TemporaryDirectory() as td:  
        p = Path(td) / "wf.json"  
        p.write_text(json.dumps(wf_bad), encoding="utf-8")  
  
        try:  
            gate_workflow_path_for_run(p, on_violation="raise")  
            raise AssertionError("Expected ValueError for unsupported actions, but none was raised.")  
        except ValueError:  
            pass  
  
        out2 = gate_workflow_path_for_run(p, on_violation="sanitize", in_place_sanitize=False)  
        assert len(out2.violations) == 3  
        assert out2.workflow["steps"][0]["action"] == "log"  
  
        # Ensure file not overwritten when in_place_sanitize=False and no output_path  
        original = json.loads(p.read_text(encoding="utf-8"))  
        assert any(s["action"] == "wait_seconds" for s in original["steps"])  
  
    print("dev_smoke_run_1a_workflow_grammar_gate: OK")  
  
  
if __name__ == "__main__":  
    main()  