from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
from tempfile import TemporaryDirectory  
  
from DOCTOR.doctor_1b_workflow_grammar_gate import doctor_workflow_grammar_gate_diagnosis  
from HISTORY.history_1a_workflow_grammar_gate_history import (  
    append_workflow_grammar_gate_history_jsonl,  
    build_workflow_grammar_gate_history_record,  
    derive_run_id_workflow_grammar_gate,  
    read_workflow_grammar_gate_history_jsonl,  
)  
  
  
def main() -> None:  
    with TemporaryDirectory() as td:  
        root = Path(td) / "wf"  
        root.mkdir(parents=True, exist_ok=True)  
  
        wf_ok = {"name": "ok", "steps": [{"action": "log", "message": "hi"}]}  
        wf_bad = {"name": "bad", "steps": [{"action": "wait_seconds", "seconds": 1}]}  
  
        (root / "ok.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
        (root / "bad.json").write_text(json.dumps(wf_bad), encoding="utf-8")  
  
        d = doctor_workflow_grammar_gate_diagnosis(str(root), mode="check", in_place=False)  
        hist_path = str(Path(td) / "history.jsonl")  
  
        rec = build_workflow_grammar_gate_history_record(  
            root_dir=str(root),  
            mode="check",  
            ok=d.ok,  
            exit_code=d.exit_code,  
            report=d.report,  
            report_text=d.report_text,  
            meta={"ci": False},  
        )  
  
        # run_id deterministic  
        assert rec["run_id"] == derive_run_id_workflow_grammar_gate(  
            root_dir=str(root),  
            mode="check",  
            exit_code=d.exit_code,  
            report_text=d.report_text,  
        )  
  
        append_workflow_grammar_gate_history_jsonl(hist_path, rec)  
        rows = read_workflow_grammar_gate_history_jsonl(hist_path)  
  
        assert len(rows) == 1  
        assert rows[0]["run_id"] == rec["run_id"]  
        assert rows[0]["schema"].startswith("HISTORY-1A.")  
        assert rows[0]["exit_code"] == d.exit_code  
  
    print("dev_smoke_history_1a_workflow_grammar_gate_history: OK")  
  
  
if __name__ == "__main__":  
    main()  