from __future__ import annotations  
  
import json  
import os  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from CLI.cli_1i_build_doc_index_artifact import main  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    out_path = os.path.join("dev", "_smoke_doc_index_artifact_1a.json")  
    try:  
        code = main(["--out", out_path, "--repo-root", ".", "--doc-dir", "DOC"])  
        assert code == 0  
  
        with open(out_path, "r", encoding="utf-8") as f:  
            data = json.load(f)  
  
        assert data["schema_id"] == "DOC_INDEX_ARTIFACT_1A"  
        assert isinstance(data["entries"], list)  
  
        # Ensure the known entry from prior milestones is included.  
        assert any(  
            isinstance(e, dict) and e.get("module") == "CLI.cli_1h_run_deploy_bundle_cli_resolver"  
            for e in data["entries"]  
        )  
  
        print("PASS")  
    finally:  
        try:  
            os.remove(out_path)  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    dev_smoke()  