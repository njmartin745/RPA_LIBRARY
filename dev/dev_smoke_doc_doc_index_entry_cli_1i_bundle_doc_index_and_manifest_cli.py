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
from DOC.doc_1f_doc_index_aggregator import collect_doc_index_entries_1a, iter_doc_module_names_in_dir_1a  
from DOC.doc_index_entry_cli_1i_bundle_doc_index_and_manifest_cli import DOC_INDEX_ENTRY_1A  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    # 1) Validate the entry shape (matches known-good collector output).  
    assert DOC_INDEX_ENTRY_1A["kind"] == "doc_index_entry"  
    assert DOC_INDEX_ENTRY_1A["layer"] == "CLI"  
    assert DOC_INDEX_ENTRY_1A["module"] == "CLI.cli_1i_bundle_doc_index_and_manifest_cli"  
    assert isinstance(DOC_INDEX_ENTRY_1A.get("usage"), dict)  
  
    # 2) Ensure the aggregator discovers + collects our entry.  
    module_names = list(iter_doc_module_names_in_dir_1a(repo_root=".", doc_dir="DOC"))  
    assert "DOC.doc_index_entry_cli_1i_bundle_doc_index_and_manifest_cli" in module_names  
  
    entries = collect_doc_index_entries_1a(module_names, strict=False)  
    assert len(entries) >= 2, f"expected >=2 doc index entries, got {len(entries)}"  
  
    assert any(  
        isinstance(e, dict) and e.get("module") == "CLI.cli_1i_bundle_doc_index_and_manifest_cli" for e in entries  
    )  
  
    # 3) Ensure a real artifact can be written and contains our module string.  
    out_dir = os.path.join("dev", "_smoke_doc_index_entry_cli_1i_out")  
    out_path = os.path.join(out_dir, "doc_index_artifact_1a.json")  
  
    try:  
        if os.path.isdir(out_dir):  
            shutil.rmtree(out_dir)  
  
        meta = write_doc_index_artifact_to_bundle_out_dir_1a(  
            repo_root=".",  
            doc_dir="DOC",  
            bundle_out_dir=out_dir,  
            out_filename="doc_index_artifact_1a.json",  
            overwrite=True,  
            strict_imports=False,  
        )  
        assert int(meta["count"]) >= 2  
        assert os.path.isfile(out_path)  
  
        with open(out_path, "r", encoding="utf-8") as f:  
            obj = json.load(f)  
        s = json.dumps(obj, ensure_ascii=False, sort_keys=True)  
        assert "CLI.cli_1i_bundle_doc_index_and_manifest_cli" in s  
  
        print("PASS")  
    finally:  
        try:  
            shutil.rmtree(out_dir)  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    dev_smoke()  