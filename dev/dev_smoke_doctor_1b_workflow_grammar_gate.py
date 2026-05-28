from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))  
from tempfile import TemporaryDirectory  
  
from BUILD.build_2g_workflow_tree_grammar_gate import gate_workflow_tree_assert  
from DOCTOR.doctor_1b_workflow_grammar_gate import doctor_workflow_grammar_gate_diagnosis  
  
  
def main() -> None:  
    with TemporaryDirectory() as td:  
        src = Path(td) / "src"  
        out = Path(td) / "out"  
        (src / "nested").mkdir(parents=True, exist_ok=True)  
  
        wf_ok = {"name": "ok", "steps": [{"action": "log", "message": "hi"}]}  
        wf_bad = {  
            "name": "bad",  
            "steps": [{"action": "log", "message": "keep"}, {"action": "wait_seconds", "seconds": 1}],  
        }  
  
        (src / "a.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
        (src / "nested" / "b.json").write_text(json.dumps(wf_bad), encoding="utf-8")  
  
        d1 = doctor_workflow_grammar_gate_diagnosis(str(src), mode="check", in_place=False)  
        assert d1.ok is False  
        assert d1.exit_code == 2  
        assert "wait_seconds" in d1.report_text  
  
        d2 = doctor_workflow_grammar_gate_diagnosis(str(src), mode="fix", output_dir=str(out), in_place=False)  
        assert d2.ok is True  
        assert d2.exit_code == 0  
  
        gate_workflow_tree_assert(str(out))  
  
    print("dev_smoke_doctor_1b_workflow_grammar_gate: OK")  
  
  
if __name__ == "__main__":  
    main()  