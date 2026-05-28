from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))  
from tempfile import TemporaryDirectory  
  
from BUILD.build_2g_workflow_tree_grammar_gate import gate_workflow_tree_assert  
from CLI.cli_1h_workflow_grammar_gate_pipeline import cli_main  
  
  
def main() -> None:  
    with TemporaryDirectory() as td:  
        src = Path(td) / "src"  
        out = Path(td) / "out"  
        rpt_json = Path(td) / "report.json"  
        rpt_txt = Path(td) / "report.txt"  
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
  
        # check => exit 2, writes reports, does not sanitize  
        code = cli_main(  
            [  
                str(src),  
                "--mode",  
                "check",  
                "--report-json",  
                str(rpt_json),  
                "--report-text",  
                str(rpt_txt),  
                "--quiet",  
            ]  
        )  
        assert code == 2  
        assert rpt_json.exists()  
        assert rpt_txt.exists()  
        txt = rpt_txt.read_text(encoding="utf-8")  
        assert "workflow_grammar_gate:" in txt  
        assert "wait_seconds" in txt  
        assert "look_for_selector" in txt  
  
        # fix => exit 0, sanitizes to out, then out should assert clean  
        code2 = cli_main(  
            [  
                str(src),  
                "--mode",  
                "fix",  
                "--output-dir",  
                str(out),  
                "--quiet",  
            ]  
        )  
        assert code2 == 0  
        gate_workflow_tree_assert(out)  
  
    print("dev_smoke_cli_1h_workflow_grammar_gate_pipeline: OK")  
  
  
if __name__ == "__main__":  
    main()  