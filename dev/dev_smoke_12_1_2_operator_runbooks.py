from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from DOC.doc_12b_operator_runbooks import (  
    get_operator_runbooks,  
    render_runbooks_markdown,  
    runbooks_to_json,  
    write_operator_runbooks_markdown,  
)  
  
  
def main() -> int:  
    try:  
        runbooks = get_operator_runbooks()  
        assert isinstance(runbooks, list) and len(runbooks) >= 3, "Expected >= 3 runbooks"  
  
        md = render_runbooks_markdown(runbooks)  
        assert "Operator Runbooks" in md  
        assert "RB-OPS-001" in md  
        assert "Triage a failed run" in md or "RB-OPS-002" in md  
  
        js = runbooks_to_json(runbooks)  
        assert js.strip().startswith("["), "Expected JSON array output"  
        assert '"runbook_id"' in js  
  
        with tempfile.TemporaryDirectory() as td:  
            out_path = os.path.join(td, "operator_runbooks.md")  
            write_operator_runbooks_markdown(out_path)  
            assert os.path.exists(out_path), "Expected markdown file to be created"  
            with open(out_path, "r", encoding="utf-8") as f:  
                written = f.read()  
            assert written == md, "Written markdown must match rendered markdown deterministically"  
  
        print("PASS: dev_smoke_12_1_2_operator_runbooks")  
        return 0  
  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_1_2_operator_runbooks :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  