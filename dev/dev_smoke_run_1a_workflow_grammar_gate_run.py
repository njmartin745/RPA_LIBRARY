from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))  
from tempfile import TemporaryDirectory  
  
from DOCTOR.doctor_1b_workflow_grammar_gate import doctor_workflow_grammar_gate_diagnosis  
from HISTORY.history_1a_workflow_grammar_gate_history import read_workflow_grammar_gate_history_jsonl  
from RUN.run_1a_workflow_grammar_gate_run import run_workflow_grammar_gate  
  
  
def main() -> None:  
    with TemporaryDirectory() as td:  
        td = Path(td)  
        base = td / "base"  
        new = td / "new"  
        out = td / "out"  
        base.mkdir(parents=True, exist_ok=True)  
        new.mkdir(parents=True, exist_ok=True)  
  
        wf_ok = {"name": "ok", "steps": [{"action": "log", "message": "hi"}]}  
        wf_bad = {"name": "bad", "steps": [{"action": "wait_seconds", "seconds": 1}]}  
  
        (base / "ok.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
  
        (new / "ok.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
        (new / "bad.json").write_text(json.dumps(wf_bad), encoding="utf-8")  
  
        baseline = doctor_workflow_grammar_gate_diagnosis(str(base), mode="check", in_place=False)  
        assert baseline.report is not None  
  
        hist_path = str(td / "history.jsonl")  
  
        r1 = run_workflow_grammar_gate(  
            str(new),  
            mode="check",  
            in_place=False,  
            baseline_report=baseline.report,  
            max_total_violations=0,  
            max_files_with_violations=0,  
            max_delta_total_violations=0,  
            history_jsonl_path=hist_path,  
            history_meta={"case": "check_fail"},  
        )  
        assert r1.ok is False  
        assert r1.exit_code == 2  
        assert r1.guard is not None  
        assert r1.history_record is not None  
  
        # Fix to out, then check out should pass strict policy  
        rfix = run_workflow_grammar_gate(  
            str(new),  
            mode="fix",  
            in_place=False,  
            output_dir=str(out),  
            history_jsonl_path=hist_path,  
            history_meta={"case": "fix"},  
        )  
        assert rfix.exit_code == 0  
  
        r2 = run_workflow_grammar_gate(  
            str(out),  
            mode="check",  
            in_place=False,  
            baseline_report=baseline.report,  
            max_total_violations=0,  
            max_files_with_violations=0,  
            max_delta_total_violations=0,  
            history_jsonl_path=hist_path,  
            history_meta={"case": "check_pass"},  
        )  
        assert r2.ok is True  
        assert r2.exit_code == 0  
  
        rows = read_workflow_grammar_gate_history_jsonl(hist_path)  
        assert len(rows) == 3  
        assert rows[0]["schema"].startswith("HISTORY-1A.")  
        assert rows[0]["meta"]["case"] == "check_fail"  
        assert rows[2]["meta"]["case"] == "check_pass"  
  
    print("dev_smoke_run_1a_workflow_grammar_gate_run: OK")  
  
  
if __name__ == "__main__":  
    main()  