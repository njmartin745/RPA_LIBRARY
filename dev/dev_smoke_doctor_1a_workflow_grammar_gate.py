from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
from tempfile import TemporaryDirectory  
  
from BUILD.build_2g_workflow_tree_grammar_gate import gate_workflow_tree_assert  
from DOCTOR.doctor_1a_workflow_grammar_gate import (  
    doctor_check_workflow_grammar,  
    doctor_fix_workflow_grammar,  
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
  
        # Check mode: should not write, but should detect violations  
        chk = doctor_check_workflow_grammar(str(src))  
        assert chk.total_files == 2  
        assert chk.total_violations == 2  
        assert all(f["wrote_file"] is False for f in chk.report["files"])  
  
        # Fix mode: write sanitized copies to output dir, keep originals intact  
        fx = doctor_fix_workflow_grammar(str(src), output_dir=str(out))  
        assert fx.total_files == 2  
        assert fx.total_violations == 2  
        assert all(f["wrote_file"] is True for f in fx.report["files"])  
  
        # Originals still bad -> assert should fail on src  
        try:  
            gate_workflow_tree_assert(src)  
            raise AssertionError("Expected ValueError on original src, but assert passed.")  
        except ValueError:  
            pass  
  
        # Output should be clean -> assert should pass on out  
        gate_workflow_tree_assert(out)  
  
    print("dev_smoke_doctor_1a_workflow_grammar_gate: OK")  
  
  
if __name__ == "__main__":  
    main()  