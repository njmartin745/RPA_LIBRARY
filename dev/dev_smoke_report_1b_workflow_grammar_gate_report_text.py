from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
from tempfile import TemporaryDirectory  
  
from BUILD.build_2g_workflow_tree_grammar_gate import gate_workflow_tree_sanitize  
from REPORT.report_1a_workflow_grammar_gate_report import build_grammar_gate_report  
from REPORT.report_1b_workflow_grammar_gate_report_text import format_grammar_gate_report_text  
  
  
def main() -> None:  
    with TemporaryDirectory() as td:  
        src = Path(td) / "src"  
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
  
        tree_res = gate_workflow_tree_sanitize(str(src), in_place=False, output_dir=None)  
        report = build_grammar_gate_report(tree_res)  
  
        text = format_grammar_gate_report_text(report)  
        assert "workflow_grammar_gate: files=2" in text  
        assert "wait_seconds" in text  
        assert "look_for_selector" in text  
        assert "nested" in text  
  
    print("dev_smoke_report_1b_workflow_grammar_gate_report_text: OK")  
  
  
if __name__ == "__main__":  
    main()  