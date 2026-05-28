from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))   
from tempfile import TemporaryDirectory  
  
from BUILD.build_2g_workflow_tree_grammar_gate import gate_workflow_tree_sanitize  
from REPORT.report_1a_workflow_grammar_gate_report import (  
    build_grammar_gate_report,  
    dump_grammar_gate_report_json_text,  
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
  
        res = gate_workflow_tree_sanitize(src, output_dir=out)  
        report = build_grammar_gate_report(res)  
  
        assert report["total_files"] == 2  
        assert report["total_violations"] == 2  
  
        # Deterministic JSON output  
        text = dump_grammar_gate_report_json_text(report)  
        loaded = json.loads(text)  
        assert loaded["total_files"] == 2  
        assert loaded["total_violations"] == 2  
        assert [f["path"] for f in loaded["files"]] == sorted(  
            [f["path"] for f in loaded["files"]], key=lambda s: s.lower()  
        )  
  
    print("dev_smoke_report_1a_workflow_grammar_gate_report: OK")  
  
  
if __name__ == "__main__":  
    main()  