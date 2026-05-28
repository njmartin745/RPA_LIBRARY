from __future__ import annotations  
  
import json  
import os  
import shutil  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from CLI.cli_1i_bundle_doc_index_and_manifest_cli import run_cli_1a  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    out_dir = os.path.join("dev", "_smoke_cli_bundle_out")  
    doc_index_path = os.path.join(out_dir, "doc_index_artifact_1a.json")  
    manifest_path = os.path.join(out_dir, "build_manifest_artifact_1a.json")  
  
    try:  
        if os.path.isdir(out_dir):  
            shutil.rmtree(out_dir)  
  
        rc = run_cli_1a(  
            [  
                "--bundle-out-dir",  
                out_dir,  
                "--repo-root",  
                ".",  
                "--doc-dir",  
                "DOC",  
            ]  
        )  
        assert rc == 0  
        assert os.path.isfile(doc_index_path)  
        assert os.path.isfile(manifest_path)  
  
        with open(manifest_path, "r", encoding="utf-8") as f:  
            manifest = json.load(f)  
  
        assert manifest["schema_id"] == "BUILD_MANIFEST_ARTIFACT_1A"  
        paths = [a["path"] for a in manifest["artifacts"]]  
        assert "doc_index_artifact_1a.json" in paths  
  
        print("PASS")  
    finally:  
        try:  
            shutil.rmtree(out_dir)  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    dev_smoke()  