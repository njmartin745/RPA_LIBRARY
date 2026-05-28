from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from DOC.doc_12d_rollback_recovery_procedures import (  
    get_rollback_recovery_playbook,  
    validate_playbook,  
    playbook_to_json,  
    render_playbook_markdown,  
    write_playbook_markdown,  
)  
  
  
def main() -> int:  
    try:  
        pb = get_rollback_recovery_playbook()  
  
        # Validate structure  
        errs = validate_playbook(pb)  
        assert errs == [], f"Validation errors: {errs}"  
  
        # Deterministic rendering  
        js1 = playbook_to_json(pb)  
        js2 = playbook_to_json(pb)  
        assert js1 == js2  
        md = render_playbook_markdown(pb)  
        assert "Rollback and Recovery Procedures" in md  
        assert "Fast rollback" in md or "Fast rollback:" in md  
  
        # Write/read markdown artifact  
        with tempfile.TemporaryDirectory() as td:  
            out_md = os.path.join(td, "rollback_recovery_playbook.md")  
            write_playbook_markdown(out_md, pb)  
            with open(out_md, "r", encoding="utf-8") as f:  
                md_written = f.read()  
            assert md_written == md  
  
        print("PASS: dev_smoke_12_4_3_rollback_recovery_procedures")  
        return 0  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_4_3_rollback_recovery_procedures :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  