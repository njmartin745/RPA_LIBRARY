from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))  
from tempfile import TemporaryDirectory  
  
from BUILD.build_2g_workflow_tree_grammar_gate import gate_workflow_tree_assert  
from PIPE.pipe_1a_workflow_grammar_gate_pipeline import run_workflow_grammar_gate_pipeline  
  
  
def main() -> None:  
    with TemporaryDirectory() as td:  
        src = Path(td) / "src"  
        out = Path(td) / "out"  
        rpt1 = Path(td) / "check_report.json"  
        rpt2 = Path(td) / "fix_report.json"  
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
  
        # Pipeline check => exit 2, report written  
        res1 = run_workflow_grammar_gate_pipeline(  
            str(src),  
            mode="check",  
            report_json_path=str(rpt1),  
        )  
        assert res1.exit_code == 2  
        assert res1.wrote_report is True  
        assert rpt1.exists()  
  
        # Pipeline fix => exit 0, write sanitized copies to out, report written  
        res2 = run_workflow_grammar_gate_pipeline(  
            str(src),  
            mode="fix",  
            output_dir=str(out),  
            report_json_path=str(rpt2),  
        )  
        assert res2.exit_code == 0  
        assert res2.wrote_report is True  
        assert rpt2.exists()  
  
        # Originals still fail assert  
        try:  
            gate_workflow_tree_assert(src)  
            raise AssertionError("Expected ValueError on original src, but assert passed.")  
        except ValueError:  
            pass  
  
        # Output should pass assert  
        gate_workflow_tree_assert(out)  
  
    print("dev_smoke_pipe_1a_workflow_grammar_gate_pipeline: OK")  
  
  
if __name__ == "__main__":  
    main()  