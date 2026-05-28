from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from DOC.doc_1e_cli_run_deploy_bundle_cli_resolver_entry import DOC_INDEX_ENTRY_1A, get_doc_index_entry_1a  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    entry = get_doc_index_entry_1a()  
    assert entry is DOC_INDEX_ENTRY_1A  
    assert entry["layer"] == "CLI"  
    assert entry["module"] == "CLI.cli_1h_run_deploy_bundle_cli_resolver"  
    assert isinstance(entry["usage"]["examples"], list)  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  