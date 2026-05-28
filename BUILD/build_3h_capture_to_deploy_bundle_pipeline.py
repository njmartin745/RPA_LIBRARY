from __future__ import annotations  
  
import json  
import os  
from typing import Any, Dict, Mapping, Optional  
  
from BUILD.build_3c_deploy_bundle_builder import build_stamp_validate_deploy_bundle_1a  
from BUILD.build_3g_deploy_bundle_writer import write_deploy_bundle_1a_to_path  
from WORKFLOWS.workflow_1g_deploy_bundle_loader import load_deploy_bundle_1a_from_path  
  
__all__ = [  
    "load_json_mapping_from_path",  
    "build_write_deploy_bundle_1a_from_capture_bundle",  
    "build_write_deploy_bundle_1a_from_capture_bundle_path",  
    "dev_smoke",  
]  
  
  
def load_json_mapping_from_path(path: str) -> Dict[str, Any]:  
    """  
    Load a JSON file and require it to be a JSON object (mapping).  
    """  
    if not isinstance(path, str) or not path.strip():  
        raise ValueError("path must be a non-empty string")  
    with open(path, "r", encoding="utf-8") as f:  
        obj = json.load(f)  
    if not isinstance(obj, Mapping):  
        raise ValueError("JSON root must be an object")  
    return dict(obj)  
  
  
def build_write_deploy_bundle_1a_from_capture_bundle(  
    capture_bundle: Mapping[str, Any],  
    deploy_path: str,  
    *,  
    deploy_name: Optional[str] = None,  
    strict: bool = True,  
    drop_selector_when_ref_present: bool = True,  
    # stamping behavior  
    version: Optional[str] = None,  
    version_prefix: str = "sha256:",  
    version_len: int = 12,  
    # validation behavior  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
    # write behavior  
    pretty: bool = False,  
    atomic: bool = True,  
) -> Dict[str, Any]:  
    """  
    End-to-end pipeline:  
      CAPTURE_BUNDLE (mapping) -> build DEPLOY_BUNDLE_1A -> write JSON -> return deploy dict  
  
    Deterministic: no timestamps/randomness (fingerprint-based versioning).  
    """  
    deploy = build_stamp_validate_deploy_bundle_1a(  
        capture_bundle,  
        deploy_name=deploy_name,  
        strict=strict,  
        drop_selector_when_ref_present=drop_selector_when_ref_present,  
        version=version,  
        version_prefix=version_prefix,  
        version_len=version_len,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
    )  
  
    # Writer re-validates by default; keep it on for safety.  
    deploy = write_deploy_bundle_1a_to_path(  
        deploy,  
        deploy_path,  
        validate=True,  
        normalize_stamp=require_version_fingerprint,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
        pretty=pretty,  
        atomic=atomic,  
    )  
    return deploy  
  
  
def build_write_deploy_bundle_1a_from_capture_bundle_path(  
    capture_path: str,  
    deploy_path: str,  
    *,  
    deploy_name: Optional[str] = None,  
    strict: bool = True,  
    drop_selector_when_ref_present: bool = True,  
    version: Optional[str] = None,  
    version_prefix: str = "sha256:",  
    version_len: int = 12,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
    pretty: bool = False,  
    atomic: bool = True,  
) -> Dict[str, Any]:  
    """  
    CAPTURE_BUNDLE JSON path -> DEPLOY_BUNDLE JSON path.  
    """  
    cap = load_json_mapping_from_path(capture_path)  
    return build_write_deploy_bundle_1a_from_capture_bundle(  
        cap,  
        deploy_path,  
        deploy_name=deploy_name,  
        strict=strict,  
        drop_selector_when_ref_present=drop_selector_when_ref_present,  
        version=version,  
        version_prefix=version_prefix,  
        version_len=version_len,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
        pretty=pretty,  
        atomic=atomic,  
    )  
  
  
def dev_smoke() -> None:  
    cap_path = "dev_smoke_tmp_capture_bundle_1a.json"  
    dep_path = "dev_smoke_tmp_deploy_bundle_1a.json"  
    try:  
        cap = {  
            "schema_id": "CAPTURE_BUNDLE_1A",  
            "name": "captured",  
            "workflow": {"steps": [{"action": "open", "url": "https://example.test/app"}]},  
            "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "captured", "selectors": {}},  
        }  
        with open(cap_path, "w", encoding="utf-8", newline="\n") as f:  
            f.write(json.dumps(cap, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")  
  
        dep = build_write_deploy_bundle_1a_from_capture_bundle_path(  
            cap_path,  
            dep_path,  
            strict=True,  
            require_version_fingerprint=True,  
            require_selector_ref=True,  
            pretty=False,  
            atomic=True,  
        )  
        assert dep.get("schema_id") == "DEPLOY_BUNDLE_1A"  
        assert isinstance(dep.get("version"), str) and dep["version"].startswith("sha256:")  
        assert dep.get("fingerprint", {}).get("algo") == "sha256"  
  
        loaded = load_deploy_bundle_1a_from_path(dep_path, validate=True)  
        assert loaded.get("schema_id") == "DEPLOY_BUNDLE_1A"  
        assert loaded.get("version") == dep.get("version")  
    finally:  
        for p in (cap_path, dep_path, dep_path + ".tmp"):  
            try:  
                if os.path.exists(p):  
                    os.remove(p)  
            except Exception:  
                pass  