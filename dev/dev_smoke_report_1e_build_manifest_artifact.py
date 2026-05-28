from __future__ import annotations  
  
import json  
import os  
import shutil  
import hashlib  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_3d_doc_index_artifact_bundler import write_doc_index_artifact_to_bundle_out_dir_1a  
from REPORT.report_1e_build_manifest_artifact import build_and_write_build_manifest_for_bundle_out_dir_1a  
  
__all__ = ["dev_smoke"]  
  
  
def _sha256_bytes(path: str) -> str:  
    h = hashlib.sha256()  
    with open(path, "rb") as f:  
        for chunk in iter(lambda: f.read(1024 * 1024), b""):  
            h.update(chunk)  
    return h.hexdigest()  
  
  
def dev_smoke() -> None:  
    out_dir = os.path.join("dev", "_smoke_bundle_manifest_out")  
    doc_index_name = "doc_index_artifact_1a.json"  
    doc_index_path = os.path.join(out_dir, doc_index_name)  
    manifest_path = os.path.join(out_dir, "build_manifest_artifact_1a.json")  
  
    try:  
        write_doc_index_artifact_to_bundle_out_dir_1a(  
            repo_root=".",  
            doc_dir="DOC",  
            bundle_out_dir=out_dir,  
            out_filename=doc_index_name,  
            overwrite=True,  
            strict_imports=False,  
        )  
        assert os.path.isfile(doc_index_path)  
  
        res = build_and_write_build_manifest_for_bundle_out_dir_1a(  
            bundle_out_dir=out_dir,  
            artifact_rel_paths=[doc_index_name],  
            overwrite=True,  
        )  
        assert res["out_path"] == manifest_path  
  
        with open(manifest_path, "r", encoding="utf-8") as f:  
            manifest = json.load(f)  
  
        assert manifest["schema_id"] == "BUILD_MANIFEST_ARTIFACT_1A"  
        assert manifest["count"] == 1  
        assert isinstance(manifest["artifacts"], list) and len(manifest["artifacts"]) == 1  
  
        entry = manifest["artifacts"][0]  
        assert entry["path"] == doc_index_name  
        assert entry["sha256"] == _sha256_bytes(doc_index_path)  
        assert entry["bytes"] == os.path.getsize(doc_index_path)  
  
        print("PASS")  
    finally:  
        try:  
            shutil.rmtree(out_dir)  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    dev_smoke()  