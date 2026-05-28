from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from DOC.doc_1a_workflow_grammar_gate import build_workflow_grammar_gate_markdown  
  
  
def main() -> None:  
    md = build_workflow_grammar_gate_markdown()  
    assert "# Workflow Grammar Gate" in md  
    assert "## Supported actions" in md  
    # spot-check required actions appear  
    assert "`open`" in md  
    assert "`click_selector`" in md  
    assert "`type_selector_secret`" in md  
    assert "`wait_for_selector`" in md  
    assert "`repeat`" in md  
    assert "CLI (CLI-1H)" in md  
    assert "PIPE-1A" in md  
  
    print("dev_smoke_doc_1a_workflow_grammar_gate: OK")  
  
  
if __name__ == "__main__":  
    main()  