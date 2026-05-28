from __future__ import annotations  
  
import json  
import os  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from DOC.doc_1f_doc_index_aggregator import (  
    build_doc_index_artifact_1a,  
    collect_doc_index_entries_1a,  
    write_doc_index_artifact_1a,  
)  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    # Keep smoke deterministic: use an explicit known module (added in prior milestone).  
    module_names = ["DOC.doc_1e_cli_run_deploy_bundle_cli_resolver_entry"]  
    entries = collect_doc_index_entries_1a(module_names, strict=True)  
    assert len(entries) == 1  
    assert entries[0]["kind"] == "doc_index_entry"  
  
    artifact = build_doc_index_artifact_1a(entries)  
    assert artifact["schema_id"] == "DOC_INDEX_ARTIFACT_1A"  
    assert artifact["count"] == 1  
  
    out_path = os.path.join("dev", "_smoke_doc_index_artifact_1a.json")  
    try:  
        write_doc_index_artifact_1a(artifact, out_path, overwrite=True)  
        with open(out_path, "r", encoding="utf-8") as f:  
            persisted = json.load(f)  
        assert persisted["count"] == 1  
        assert persisted["entries"][0]["module"] == "CLI.cli_1h_run_deploy_bundle_cli_resolver"  
        print("PASS")  
    finally:  
        try:  
            os.remove(out_path)  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    dev_smoke()  