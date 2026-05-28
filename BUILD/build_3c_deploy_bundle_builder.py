from __future__ import annotations  
  
from typing import Any, Dict, Mapping, Optional, Tuple  
  
from BUILD.build_3a_deploy_bundle_format import build_deploy_bundle_from_capture_bundle  
from BUILD.build_3f_deploy_bundle_stamper import ensure_deploy_bundle_version_fingerprint_1a  
from VAL.val_2a_deploy_bundle_validator import assert_deploy_bundle_1a, validate_deploy_bundle_1a  
  
__all__ = [  
    "build_stamp_validate_deploy_bundle_1a",  
    "build_stamp_validate_deploy_bundle_1a_with_report",  
    "dev_smoke",  
]  
  
  
def build_stamp_validate_deploy_bundle_1a(  
    capture_bundle: Mapping[str, Any],  
    *,  
    deploy_name: Optional[str] = None,  
    strict: bool = True,  
    # selector_ref-first enforcement behavior (passed through)  
    drop_selector_when_ref_present: bool = True,  
    # stamping behavior (passed through)  
    version: Optional[str] = None,  
    version_prefix: str = "sha256:",  
    version_len: int = 12,  
    # validation behavior  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
) -> Dict[str, Any]:  
    """  
    One-call pipeline:  
      CAPTURE_BUNDLE -> DEPLOY_BUNDLE_1A (normalized, selector_ref-first)  
                   -> stamped (version + fingerprint)  
                   -> validated (raises ValueError on failure)  
  
    Deterministic: no timestamps/randomness.  
    """  
    deploy = build_deploy_bundle_from_capture_bundle(  
        capture_bundle,  
        deploy_name=deploy_name,  
        strict=strict,  
        drop_selector_when_ref_present=drop_selector_when_ref_present,  
    )  
    deploy = ensure_deploy_bundle_version_fingerprint_1a(  
        deploy,  
        version=version,  
        version_prefix=version_prefix,  
        version_len=version_len,  
    )  
    assert_deploy_bundle_1a(  
        deploy,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
    )  
    return deploy  
  
  
def build_stamp_validate_deploy_bundle_1a_with_report(  
    capture_bundle: Mapping[str, Any],  
    *,  
    deploy_name: Optional[str] = None,  
    strict: bool = True,  
    drop_selector_when_ref_present: bool = True,  
    version: Optional[str] = None,  
    version_prefix: str = "sha256:",  
    version_len: int = 12,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
) -> Tuple[Dict[str, Any], Dict[str, Any]]:  
    """  
    Same pipeline as build_stamp_validate_deploy_bundle_1a, but returns (bundle, report)  
    and does NOT raise. Caller can decide what to do with report["ok"].  
    """  
    deploy = build_deploy_bundle_from_capture_bundle(  
        capture_bundle,  
        deploy_name=deploy_name,  
        strict=strict,  
        drop_selector_when_ref_present=drop_selector_when_ref_present,  
    )  
    deploy = ensure_deploy_bundle_version_fingerprint_1a(  
        deploy,  
        version=version,  
        version_prefix=version_prefix,  
        version_len=version_len,  
    )  
    report = validate_deploy_bundle_1a(  
        deploy,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
    )  
    return deploy, report  
  
  
def dev_smoke() -> None:  
    cap = {  
        "schema_id": "CAPTURE_BUNDLE_1A",  
        "name": "captured",  
        "workflow": {"steps": [{"action": "open", "url": "https://example.test/app"}]},  
        "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "captured", "selectors": {}},  
    }  
  
    dep = build_stamp_validate_deploy_bundle_1a(cap, strict=True)  
    assert dep["schema_id"] == "DEPLOY_BUNDLE_1A"  
    assert isinstance(dep.get("version"), str) and dep["version"].startswith("sha256:")  
    assert dep.get("fingerprint", {}).get("algo") == "sha256"  