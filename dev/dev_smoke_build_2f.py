from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))  
from tempfile import TemporaryDirectory  
  
from BUILD.build_2f_workflow_file_grammar_gate import (  
    gate_workflow_file_assert,  
    gate_workflow_file_sanitize,  
    load_workflow_json_file,  
)  
  
  
def main() -> None:  
    with TemporaryDirectory() as td:  
        p = Path(td) / "wf.json"  
  
        wf_bad = {  
            "name": "bad",  
            "steps": [  
                {"action": "log", "message": "keep"},  
                {"action": "wait_seconds", "seconds": 1},  
                {  
                    "action": "repeat",  
                    "times": 1,  
                    "steps": [  
                        {"action": "look_for_selector", "strategy": "css", "selector": "#x"},  
                        {"action": "log", "message": "keep2"},  
                    ],  
                },  
            ],  
        }  
        p.write_text(json.dumps(wf_bad), encoding="utf-8")  
  
        # Assert should fail on unsupported actions  
        try:  
            gate_workflow_file_assert(p)  
            raise AssertionError("Expected ValueError for unsupported actions, but none was raised.")  
        except ValueError:  
            pass  
  
        # Sanitize in place should remove unsupported actions and keep supported ones  
        res = gate_workflow_file_sanitize(p, in_place=True)  
        assert res.wrote_file is True  
        assert [v.action for v in res.violations] == ["wait_seconds", "look_for_selector"]  
  
        wf_after = load_workflow_json_file(p)  
        assert wf_after["steps"] == [  
            {"action": "log", "message": "keep"},  
            {"action": "repeat", "times": 1, "steps": [{"action": "log", "message": "keep2"}]},  
        ]  
  
        # Now assert should pass  
        gate_workflow_file_assert(p)  
  
    print("dev_smoke_build_2f: OK")  
  
  
if __name__ == "__main__":  
    main()  