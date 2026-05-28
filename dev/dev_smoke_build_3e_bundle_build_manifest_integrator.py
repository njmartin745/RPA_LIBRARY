from __future__ import annotations  
  
import hashlib  
import json  
import os  
import shutil  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_3e_bundle_build_manifest_integrator import build_bundle_out_dir_doc_index_and_manifest_1a  
  
__all__ = ["dev_smoke"]  
  
  
def _sha256_bytes(path: str) -> str:  
    h = hashlib.sha256()  
    with open(path, "rb") as f:  
        for chunk in iter(lambda: f.read(1024 * 1024), b""):  
            h.update(chunk)  
    return h.hexdigest()  
  
  
def dev_smoke() -> None:  
    out_dir = os.path.join("dev", "_smoke_bundle_integrator_out")  
    doc_index_path = os.path.join(out_dir, "doc_index_artifact_1a.json")  
    dummy_rel = "bundle_dummy.txt"  
    dummy_path = os.path.join(out_dir, dummy_rel)  
    manifest_path = os.path.join(out_dir, "build_manifest_artifact_1a.json")  
  
    try:  
        os.makedirs(out_dir, exist_ok=True)  
        with open(dummy_path, "w", encoding="utf-8") as f:  
            f.write("dummy\n")  
  
        res = build_bundle_out_dir_doc_index_and_manifest_1a(  
            repo_root=".",  
            doc_dir="DOC",  
            bundle_out_dir=out_dir,  
            overwrite=True,  
            strict_imports=False,  
        )  
  
        assert os.path.isfile(doc_index_path)  
        assert os.path.isfile(manifest_path)  
        assert res["manifest"]["out_path"] == manifest_path  
        assert res["manifest"]["schema_id"] == "BUILD_MANIFEST_ARTIFACT_1A"  
  
        with open(manifest_path, "r", encoding="utf-8") as f:  
            manifest = json.load(f)  
  
        paths = [a["path"] for a in manifest["artifacts"]]  
        assert "doc_index_artifact_1a.json" in paths  
        assert dummy_rel in paths  
        assert "build_manifest_artifact_1a.json" not in paths  # excluded from discovery  
  
        # Verify checksums match the actual files.  
        by_path = {a["path"]: a for a in manifest["artifacts"]}  
        assert by_path[dummy_rel]["sha256"] == _sha256_bytes(dummy_path)  
        assert by_path["doc_index_artifact_1a.json"]["sha256"] == _sha256_bytes(doc_index_path)  
  
        print("PASS")  
    finally:  
        try:  
            shutil.rmtree(out_dir)  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    dev_smoke()  