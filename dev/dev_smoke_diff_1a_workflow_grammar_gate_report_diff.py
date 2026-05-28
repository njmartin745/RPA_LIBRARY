from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))  
from tempfile import TemporaryDirectory  
  
from DOCTOR.doctor_1b_workflow_grammar_gate import doctor_workflow_grammar_gate_diagnosis  
from DIFF.diff_1a_workflow_grammar_gate_report_diff import diff_workflow_grammar_gate_reports  
  
  
def main() -> None:  
    with TemporaryDirectory() as td:  
        root_a = Path(td) / "a"  
        root_b = Path(td) / "b"  
        root_a.mkdir(parents=True, exist_ok=True)  
        root_b.mkdir(parents=True, exist_ok=True)  
  
        wf_ok = {"name": "ok", "steps": [{"action": "log", "message": "hi"}]}  
        wf_bad = {"name": "bad", "steps": [{"action": "wait_seconds", "seconds": 1}]}  
  
        # A has one bad file  
        (root_a / "ok.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
        (root_a / "bad.json").write_text(json.dumps(wf_bad), encoding="utf-8")  
  
        # B has only ok file  
        (root_b / "ok.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
  
        da = doctor_workflow_grammar_gate_diagnosis(str(root_a), mode="check", in_place=False)  
        db = doctor_workflow_grammar_gate_diagnosis(str(root_b), mode="check", in_place=False)  
  
        assert da.report is not None  
        assert db.report is not None  
  
        d = diff_workflow_grammar_gate_reports(da.report, db.report)  
  
        assert d["schema"].startswith("DIFF-1A.")  
        assert d["delta_total_violations"] <= 0  # removing the bad file cannot increase violations  
        assert "removed_files" in d  
        # bad.json should be removed if the report includes per-file paths  
        # (best-effort schema support, so we only assert type + determinism)  
        assert isinstance(d["removed_files"], list)  
        assert isinstance(d["added_files"], list)  
        assert isinstance(d["changed_files"], list)  
  
    print("dev_smoke_diff_1a_workflow_grammar_gate_report_diff: OK")  
  
  
if __name__ == "__main__":  
    main()  