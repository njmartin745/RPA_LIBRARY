from __future__ import annotations  
  
import os  
from typing import Any, Dict  
  
from DOC.doc_1f_doc_index_aggregator import (  
    build_doc_index_artifact_1a,  
    collect_doc_index_entries_1a,  
    iter_doc_module_names_in_dir_1a,  
    write_doc_index_artifact_1a,  
)  
  
__all__ = [  
    "write_doc_index_artifact_to_bundle_out_dir_1a",  
    "dev_smoke",  
]  
  
  
def write_doc_index_artifact_to_bundle_out_dir_1a(  
    *,  
    repo_root: str = ".",  
    doc_dir: str = "DOC",  
    bundle_out_dir: str,  
    out_filename: str = "doc_index_artifact_1a.json",  
    strict_imports: bool = False,  
    overwrite: bool = True,  
) -> Dict[str, Any]:  
    """  
    Build + write DOC index artifact into a bundle output directory.  
  
    Intended for BUILD/build_2c_full_bundle.py consumers, without modifying them:  
    call this helper with the same output directory used for the full bundle.  
  
    Returns:  
      {"out_path": "...", "count": N, "schema_id": "DOC_INDEX_ARTIFACT_1A"}  
    """  
    if not isinstance(bundle_out_dir, str) or not bundle_out_dir.strip():  
        raise ValueError("bundle_out_dir must be a non-empty string")  
  
    os.makedirs(bundle_out_dir, exist_ok=True)  
    out_path = os.path.join(bundle_out_dir, out_filename)  
  
    module_names = iter_doc_module_names_in_dir_1a(repo_root=repo_root, doc_dir=doc_dir)  
    entries = collect_doc_index_entries_1a(module_names, strict=strict_imports)  
    artifact = build_doc_index_artifact_1a(entries)  
    written = write_doc_index_artifact_1a(artifact, out_path, overwrite=overwrite)  
  
    return {  
        "out_path": written,  
        "count": int(artifact.get("count", 0)),  
        "schema_id": artifact.get("schema_id"),  
    }  
  
  
def dev_smoke() -> None:  
    # covered by dev smoke script  
    pass  