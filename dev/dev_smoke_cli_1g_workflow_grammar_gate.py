from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
from tempfile import TemporaryDirectory  
  
from CLI.cli_1g_workflow_grammar_gate import main  
  
  
def main_smoke() -> None:  
    with TemporaryDirectory() as td:  
        src = Path(td) / "src"  
        out = Path(td) / "out"  
        rpt = Path(td) / "report.json"  
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
  
        # Assert should fail (exit code 2)  
        code = main(["--assert", str(src)])  
        assert code == 2  
  
        # Sanitize to output dir and emit report  
        code = main(["--sanitize", str(src), "--output-dir", str(out), "--report-json", str(rpt)])  
        assert code == 0  
        assert rpt.exists()  
  
        report = json.loads(rpt.read_text(encoding="utf-8"))  
        assert report["total_files"] == 2  
        assert report["total_violations"] == 2  
  
        # Assert should pass on sanitized output  
        code = main(["--assert", str(out)])  
        assert code == 0  
  
    print("dev_smoke_cli_1g_workflow_grammar_gate: OK")  
  
  
if __name__ == "__main__":  
    main_smoke()  