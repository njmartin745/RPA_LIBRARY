from __future__ import annotations  
  
from typing import Any, Dict, Mapping, Optional  
  
from WORKFLOW.workflow_1e_steps_normalizer import normalize_capture_bundle_workflow  
from WORKFLOW.workflow_1f_selector_ref_first import enforce_selector_ref_first_in_bundle  
  
__all__ = [  
    "DEPLOY_BUNDLE_SCHEMA_ID",  
    "build_deploy_bundle_from_capture_bundle",  
    "dev_smoke",  
]  
  
DEPLOY_BUNDLE_SCHEMA_ID = "DEPLOY_BUNDLE_1A"  
  
  
def build_deploy_bundle_from_capture_bundle(  
    capture_bundle: Mapping[str, Any],  
    *,  
    deploy_name: Optional[str] = None,  
    strict: bool = True,  
    drop_selector_when_ref_present: bool = True,  
) -> Dict[str, Any]:  
    """  
    Build a deployable bundle from a CAPTURE_BUNDLE_1A-like bundle.  
  
    Deploy bundle format (DEPLOY_BUNDLE_1A):  
      {  
        "schema_id": "DEPLOY_BUNDLE_1A",  
        "name": <str>,  
        "workflow": <workflow dict>,  
        "selector_pack": <selector_pack dict>,  
        "meta": {"source_schema_id": <str>, "source_name": <str>}  
      }  
  
    Deterministic: no timestamps/randomness; stable key insertion order.  
    """  
    if not isinstance(capture_bundle, Mapping):  
        raise ValueError("capture_bundle must be a mapping")  
  
    # Normalize workflow fields for review stability + (optional) strict action/required-field checks  
    normalized = normalize_capture_bundle_workflow(capture_bundle, strict=strict)  
  
    # Enforce selector_ref-first (convert selector -> selector_ref when possible/required)  
    ref_first = enforce_selector_ref_first_in_bundle(  
        normalized,  
        drop_selector_when_ref_present=drop_selector_when_ref_present,  
        strict=strict,  
    )  
  
    wf = ref_first.get("workflow")  
    sp = ref_first.get("selector_pack")  
    if not isinstance(wf, Mapping):  
        raise ValueError("capture_bundle.workflow must be a mapping")  
    if not isinstance(sp, Mapping):  
        raise ValueError("capture_bundle.selector_pack must be a mapping")  
  
    source_schema_id = str(capture_bundle.get("schema_id") or "").strip()  
    source_name = str(capture_bundle.get("name") or "").strip()  
  
    name = (deploy_name if deploy_name is not None else source_name).strip()  
    if strict and not name:  
        raise ValueError("deploy bundle name must be non-empty")  
  
    deploy_bundle: Dict[str, Any] = {  
        "schema_id": DEPLOY_BUNDLE_SCHEMA_ID,  
        "name": name,  
        "workflow": dict(wf),  
        "selector_pack": dict(sp),  
        "meta": {  
            "source_schema_id": source_schema_id,  
            "source_name": source_name,  
        },  
    }  
    return deploy_bundle  
  
  
def dev_smoke() -> None:  
    cap = {  
        "schema_id": "CAPTURE_BUNDLE_1A",  
        "name": " captured ",  
        "workflow": {"steps": [{"action": "open", "url": " https://example.test/app "}]},  
        "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "captured", "selectors": {}},  
    }  
  
    out = build_deploy_bundle_from_capture_bundle(cap, strict=True)  
    assert out["schema_id"] == "DEPLOY_BUNDLE_1A"  
    assert out["name"] == "captured"  
    assert out["meta"]["source_schema_id"] == "CAPTURE_BUNDLE_1A"  
    assert out["meta"]["source_name"] == "captured"  
    assert out["workflow"]["steps"][0]["action"] == "open"  
    assert out["workflow"]["steps"][0]["url"] == "https://example.test/app"  