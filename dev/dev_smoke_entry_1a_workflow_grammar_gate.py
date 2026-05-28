from __future__ import annotations  
  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
from tempfile import TemporaryDirectory  
  
from ENTRY.entry_1a_workflow_grammar_gate import main  
  
  
def main_smoke() -> None:  
    with TemporaryDirectory() as td:  
        root = Path(td) / "workflows"  
        root.mkdir(parents=True, exist_ok=True)  
  
        wf_ok = {"name": "ok", "steps": [{"action": "log", "message": "hi"}]}  
        wf_bad = {"name": "bad", "steps": [{"action": "wait_seconds", "seconds": 1}]}  
  
        (root / "ok.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
        (root / "bad.json").write_text(json.dumps(wf_bad), encoding="utf-8")  
  
        code_ok = main([str(root / "ok.json"), "--mode", "check", "--quiet"])  
        assert code_ok == 0  
  
        code_bad = main([str(root), "--mode", "check", "--quiet"])  
        assert code_bad == 2  
  
    print("dev_smoke_entry_1a_workflow_grammar_gate: OK")  
  
  
if __name__ == "__main__":  
    main_smoke()  