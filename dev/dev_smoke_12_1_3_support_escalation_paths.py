from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from DOC.doc_12c_support_escalation_paths import (  
    get_support_roles,  
    get_severity_levels,  
    get_response_targets,  
    get_escalation_matrix,  
    get_incident_ticket_requirements,  
    render_support_escalation_markdown,  
    support_escalation_to_json,  
    write_support_escalation_markdown,  
)  
  
  
def main() -> int:  
    try:  
        roles = get_support_roles()  
        sevs = get_severity_levels()  
        targets = get_response_targets()  
        matrix = get_escalation_matrix()  
        ticket = get_incident_ticket_requirements()  
  
        assert len(roles) >= 3, "Expected >= 3 support roles"  
        assert any(r.role_id == "ROLE-L1" for r in roles), "Expected ROLE-L1"  
        assert any(s.sev == "SEV-1" for s in sevs), "Expected SEV-1"  
        assert any(t.sev == "SEV-1" for t in targets), "Expected SEV-1 response target"  
        assert len(matrix) >= 2, "Expected >= 2 escalation rules"  
        assert len(ticket.required_fields) >= 5, "Expected required incident fields"  
  
        md = render_support_escalation_markdown(roles, sevs, targets, matrix, ticket)  
        assert "Support and Escalation Paths" in md  
        assert "Escalation Matrix" in md  
        assert "SEV-1" in md  
        assert "run_id" in md  
  
        js = support_escalation_to_json()  
        assert js.strip().startswith("{"), "Expected JSON object output"  
        assert '"roles"' in js and '"severity_levels"' in js, "Expected key sections"  
  
        with tempfile.TemporaryDirectory() as td:  
            out_path = os.path.join(td, "support_escalation.md")  
            write_support_escalation_markdown(out_path)  
            assert os.path.exists(out_path), "Expected markdown file to be created"  
            with open(out_path, "r", encoding="utf-8") as f:  
                written = f.read()  
            assert written == md, "Written markdown must match rendered markdown deterministically"  
  
        print("PASS: dev_smoke_12_1_3_support_escalation_paths")  
        return 0  
  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_1_3_support_escalation_paths :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  