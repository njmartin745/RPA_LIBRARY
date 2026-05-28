from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
from tempfile import TemporaryDirectory  
  
from BUILD.build_2g_workflow_tree_grammar_gate import (  
    gate_workflow_tree_assert,  
    gate_workflow_tree_sanitize,  
)  
  
  
def main() -> None:  
    with TemporaryDirectory() as td:  
        src = Path(td) / "src"  
        out = Path(td) / "out"  
        (src / "nested").mkdir(parents=True, exist_ok=True)  
  
        wf_ok = {"name": "ok", "steps": [{"action": "log", "message": "hi"}]}  
        wf_bad = {  
            "name": "bad",  
            "steps": [  
                {"action": "log", "message": "keep"},  
                {"action": "wait_seconds", "seconds": 1},  
                {"action": "look_for_selector", "strategy": "css", "selector": "#x"},  
            ],  
        }  
  
        (src / "a.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
        (src / "nested" / "b.json").write_text(json.dumps(wf_bad), encoding="utf-8")  
  
        # Assert should fail on src due to bad file  
        try:  
            gate_workflow_tree_assert(src)  
            raise AssertionError("Expected ValueError for unsupported actions, but none was raised.")  
        except ValueError:  
            pass  
  
        # Sanitize to output_dir (do not overwrite originals)  
        res = gate_workflow_tree_sanitize(src, output_dir=out)  
        assert res.total_files == 2  
        assert res.total_violations == 2  # wait_seconds + look_for_selector  
  
        # Now assert should pass on out  
        gate_workflow_tree_assert(out)  
  
        # Verify original still contains bad actions  
        original_bad = json.loads((src / "nested" / "b.json").read_text(encoding="utf-8"))  
        assert [s["action"] for s in original_bad["steps"]] == ["log", "wait_seconds", "look_for_selector"]  
  
        # Verify output has them stripped  
        sanitized_bad = json.loads((out / "nested" / "b.json").read_text(encoding="utf-8"))  
        assert sanitized_bad["steps"] == [{"action": "log", "message": "keep"}]  
  
    print("dev_smoke_build_2g: OK")  
  
  
if __name__ == "__main__":  
    main()  