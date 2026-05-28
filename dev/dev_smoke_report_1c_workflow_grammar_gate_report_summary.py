from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
from tempfile import TemporaryDirectory  
  
from DOCTOR.doctor_1b_workflow_grammar_gate import doctor_workflow_grammar_gate_diagnosis  
from REPORT.report_1c_workflow_grammar_gate_report_summary import (  
    build_grammar_gate_report_summary,  
    format_grammar_gate_summary_line,  
)  
  
  
def main() -> None:  
    with TemporaryDirectory() as td:  
        root = Path(td) / "wf"  
        out = Path(td) / "out"  
        root.mkdir(parents=True, exist_ok=True)  
  
        wf_ok = {"name": "ok", "steps": [{"action": "log", "message": "hi"}]}  
        wf_bad = {"name": "bad", "steps": [{"action": "wait_seconds", "seconds": 1}]}  
  
        (root / "ok.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
        (root / "bad.json").write_text(json.dumps(wf_bad), encoding="utf-8")  
  
        d1 = doctor_workflow_grammar_gate_diagnosis(str(root), mode="check", in_place=False)  
        assert d1.report is not None  
        s1 = build_grammar_gate_report_summary(d1.report)  
        line1 = format_grammar_gate_summary_line(d1.report)  
        assert s1["ok"] is False  
        assert s1["total_violations"] > 0  
        assert "FAIL" in line1  
  
        # Fix into output dir, then re-check output dir  
        dfix = doctor_workflow_grammar_gate_diagnosis(str(root), mode="fix", output_dir=str(out), in_place=False)  
        assert dfix.exit_code == 0  
  
        d2 = doctor_workflow_grammar_gate_diagnosis(str(out), mode="check", in_place=False)  
        assert d2.report is not None  
        s2 = build_grammar_gate_report_summary(d2.report)  
        line2 = format_grammar_gate_summary_line(d2.report)  
        assert s2["ok"] is True  
        assert s2["total_violations"] == 0  
        assert "OK" in line2  
  
    print("dev_smoke_report_1c_workflow_grammar_gate_report_summary: OK")  
  
  
if __name__ == "__main__":  
    main()  