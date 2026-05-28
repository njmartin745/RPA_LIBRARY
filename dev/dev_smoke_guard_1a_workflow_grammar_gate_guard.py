from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
from tempfile import TemporaryDirectory  
  
from DOCTOR.doctor_1b_workflow_grammar_gate import doctor_workflow_grammar_gate_diagnosis  
from GUARD.guard_1a_workflow_grammar_gate_guard import guard_workflow_grammar_gate_report  
  
  
def main() -> None:  
    with TemporaryDirectory() as td:  
        root_a = Path(td) / "a"  
        root_b = Path(td) / "b"  
        out_b = Path(td) / "out_b"  
        root_a.mkdir(parents=True, exist_ok=True)  
        root_b.mkdir(parents=True, exist_ok=True)  
  
        wf_ok = {"name": "ok", "steps": [{"action": "log", "message": "hi"}]}  
        wf_bad = {"name": "bad", "steps": [{"action": "wait_seconds", "seconds": 1}]}  
  
        # A: baseline clean  
        (root_a / "ok.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
  
        # B: has a violation  
        (root_b / "ok.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
        (root_b / "bad.json").write_text(json.dumps(wf_bad), encoding="utf-8")  
  
        da = doctor_workflow_grammar_gate_diagnosis(str(root_a), mode="check", in_place=False)  
        db = doctor_workflow_grammar_gate_diagnosis(str(root_b), mode="check", in_place=False)  
        assert da.report is not None  
        assert db.report is not None  
  
        # Strict policy => B must fail  
        dec1 = guard_workflow_grammar_gate_report(  
            db.report,  
            baseline_report=da.report,  
            max_total_violations=0,  
            max_files_with_violations=0,  
            max_delta_total_violations=0,  
        )  
        assert dec1.ok is False  
        assert dec1.exit_code == 2  
        assert any("total_violations" in r or "delta_total_violations" in r for r in dec1.reasons)  
  
        # Fix B into out_b, then re-check and guard should pass  
        dfix = doctor_workflow_grammar_gate_diagnosis(str(root_b), mode="fix", output_dir=str(out_b), in_place=False)  
        assert dfix.exit_code == 0  
  
        db2 = doctor_workflow_grammar_gate_diagnosis(str(out_b), mode="check", in_place=False)  
        assert db2.report is not None  
  
        dec2 = guard_workflow_grammar_gate_report(  
            db2.report,  
            baseline_report=da.report,  
            max_total_violations=0,  
            max_files_with_violations=0,  
            max_delta_total_violations=0,  
        )  
        assert dec2.ok is True  
        assert dec2.exit_code == 0  
        assert dec2.reasons == []  
  
    print("dev_smoke_guard_1a_workflow_grammar_gate_guard: OK")  
  
  
if __name__ == "__main__":  
    main()  