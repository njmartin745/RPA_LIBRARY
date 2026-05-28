from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_1a_workflow_grammar_gate_entrypoints import (  
    get_workflow_grammar_gate_console_scripts,  
    get_workflow_grammar_gate_entrypoints,  
)  
  
  
def main() -> None:  
    cs = get_workflow_grammar_gate_console_scripts()  
    assert isinstance(cs, dict)  
    assert cs["workflow-grammar-gate"] == "ENTRY.entry_1a_workflow_grammar_gate:main"  
  
    eps = get_workflow_grammar_gate_entrypoints()  
    assert "console_scripts" in eps  
    assert eps["console_scripts"] == cs  
  
    print("dev_smoke_build_1a_workflow_grammar_gate_entrypoints: OK")  
  
  
if __name__ == "__main__":  
    main()  