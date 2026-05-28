from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from DOC.doc_12a_slos_success_criteria import (  
    get_slos,  
    get_success_criteria,  
    render_operational_standards_markdown,  
    slos_to_json,  
    success_criteria_to_json,  
    write_operational_standards_markdown,  
)  
  
  
def main() -> int:  
    try:  
        slos = get_slos()  
        criteria = get_success_criteria()  
  
        # Basic structural checks  
        assert isinstance(slos, list) and len(slos) >= 3, "Expected at least 3 SLOs"  
        assert isinstance(criteria, list) and len(criteria) >= 3, "Expected at least 3 success criteria"  
  
        # Content checks (ensure milestone intent is present)  
        md = render_operational_standards_markdown(slos, criteria)  
        assert "Operational SLOs" in md  
        assert "Production Success Criteria" in md  
        assert "SLO-VAL-001" in md  
        assert "SC-OPS-001" in md  
  
        # JSON render checks (deterministic + parseable)  
        slos_json = slos_to_json(slos)  
        criteria_json = success_criteria_to_json(criteria)  
        assert slos_json.strip().startswith("[")  
        assert criteria_json.strip().startswith("[")  
  
        # I/O smoke: write and read back  
        with tempfile.TemporaryDirectory() as td:  
            out_path = os.path.join(td, "operational_standards.md")  
            write_operational_standards_markdown(out_path)  
            assert os.path.exists(out_path), "Expected markdown file to be created"  
            with open(out_path, "r", encoding="utf-8") as f:  
                written = f.read()  
            assert written == md, "Written markdown must match rendered markdown deterministically"  
  
        print("PASS: dev_smoke_12_1_1_slos_success_criteria")  
        return 0  
  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_1_1_slos_success_criteria :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  