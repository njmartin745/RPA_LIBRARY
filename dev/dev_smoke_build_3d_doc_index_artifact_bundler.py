from __future__ import annotations  
  
import json  
import os  
import shutil  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_3d_doc_index_artifact_bundler import write_doc_index_artifact_to_bundle_out_dir_1a  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    out_dir = os.path.join("dev", "_smoke_bundle_out")  
    out_path = os.path.join(out_dir, "doc_index_artifact_1a.json")  
  
    try:  
        res = write_doc_index_artifact_to_bundle_out_dir_1a(  
            repo_root=".",  
            doc_dir="DOC",  
            bundle_out_dir=out_dir,  
            overwrite=True,  
            strict_imports=False,  
        )  
        assert res["out_path"] == out_path  
  
        with open(out_path, "r", encoding="utf-8") as f:  
            data = json.load(f)  
  
        assert data["schema_id"] == "DOC_INDEX_ARTIFACT_1A"  
        assert isinstance(data["entries"], list)  
  
        # Ensure the known entry from prior milestones is present.  
        assert any(  
            isinstance(e, dict) and e.get("module") == "CLI.cli_1h_run_deploy_bundle_cli_resolver"  
            for e in data["entries"]  
        )  
  
        print("PASS")  
    finally:  
        try:  
            shutil.rmtree(out_dir)  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    dev_smoke()  