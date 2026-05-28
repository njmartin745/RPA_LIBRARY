from __future__ import annotations  
  
import json  
import os  
from typing import Any, Dict, Mapping, Optional, Tuple  
  
from BUILD.build_3a_deploy_bundle_format import DEPLOY_BUNDLE_SCHEMA_ID  
from VAL.val_2a_deploy_bundle_validator import validate_deploy_bundle_1a  
from WORKFLOWS.workflow_1g_deploy_bundle_loader import load_json_mapping_from_path  
  
__all__ = [  
    "derive_deploy_bundle_validation_report_path_1a",  
    "build_deploy_bundle_validation_report_1a",  
    "write_deploy_bundle_validation_report_1a",  
    "write_deploy_bundle_validation_report_alongside_1a",  
    "dev_smoke",  
]  
  
  
REPORT_SCHEMA_ID = "DEPLOY_BUNDLE_VALIDATION_REPORT_1A"  
  
  
def derive_deploy_bundle_validation_report_path_1a(bundle_path: str) -> str:  
    """  
    Deterministically derive a report path alongside a bundle path.  
  
    Example:  
      C:\\x\\bundle.json -> C:\\x\\bundle.validation.json  
    """  
    if not isinstance(bundle_path, str) or not bundle_path.strip():  
        raise ValueError("bundle_path must be a non-empty string")  
    root, ext = os.path.splitext(bundle_path)  
    if ext.lower() != ".json":  
        # Still write alongside; keep original extension and append suffix.  
        return bundle_path + ".validation.json"  
    return root + ".validation.json"  
  
  
def build_deploy_bundle_validation_report_1a(  
    deploy_bundle_obj: Mapping[str, Any],  
    *,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
) -> Dict[str, Any]:  
    """  
    Build a report dict for a (possibly invalid) deploy bundle object.  
    Never raises for validation failures; returns validate_deploy_bundle_1a() report plus metadata.  
    """  
    if not isinstance(deploy_bundle_obj, Mapping):  
        raise ValueError("deploy_bundle_obj must be a mapping")  
  
    validation = validate_deploy_bundle_1a(  
        deploy_bundle_obj,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
    )  
  
    # Best-effort metadata extraction (even when invalid)  
    name = deploy_bundle_obj.get("name")  
    version = deploy_bundle_obj.get("version")  
    schema_id = deploy_bundle_obj.get("schema_id")  
  
    return {  
        "schema_id": REPORT_SCHEMA_ID,  
        "bundle": {  
            "schema_id": schema_id,  
            "name": name,  
            "version": version,  
            "expected_schema_id": DEPLOY_BUNDLE_SCHEMA_ID,  
        },  
        "validation": validation,  
    }  
  
  
def write_deploy_bundle_validation_report_1a(  
    report: Mapping[str, Any],  
    out_path: str,  
    *,  
    overwrite: bool = True,  
) -> str:  
    """  
    Write a report mapping to JSON deterministically.  
    Returns out_path.  
    """  
    if not isinstance(report, Mapping):  
        raise ValueError("report must be a mapping")  
    if not isinstance(out_path, str) or not out_path.strip():  
        raise ValueError("out_path must be a non-empty string")  
  
    if (not overwrite) and os.path.exists(out_path):  
        raise FileExistsError(out_path)  
  
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)  
    with open(out_path, "w", encoding="utf-8") as f:  
        json.dump(dict(report), f, ensure_ascii=False, sort_keys=True, indent=2)  
    return out_path  
  
  
def write_deploy_bundle_validation_report_alongside_1a(  
    bundle_path: str,  
    *,  
    report_path: Optional[str] = None,  
    overwrite: bool = True,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
) -> Tuple[str, Dict[str, Any]]:  
    """  
    Load a JSON file (intended DEPLOY_BUNDLE_1A), validate it, and write a report alongside it.  
  
    Returns: (report_path, report_dict)  
    """  
    obj = load_json_mapping_from_path(bundle_path)  
    report = build_deploy_bundle_validation_report_1a(  
        obj,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
    )  
  
    out = report_path or derive_deploy_bundle_validation_report_path_1a(bundle_path)  
    write_deploy_bundle_validation_report_1a(report, out_path=out, overwrite=overwrite)  
    return out, report  
  
  
def dev_smoke() -> None:  
    # covered by dev smoke script  
    pass  