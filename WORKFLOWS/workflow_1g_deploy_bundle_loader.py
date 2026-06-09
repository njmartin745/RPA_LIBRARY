"""
WORKFLOW-1G — Deploy Bundle Loader

Purpose
-------
Load, normalize, validate, and extract runnable
workflow assets from DEPLOY_BUNDLE_1A artifacts.

Provides a stable bridge between deployment
artifacts and runtime execution.

Public API
----------
load_deploy_bundle_1a(...)
load_deploy_bundle_1a_from_path(...)
extract_runnable_from_deploy_bundle_1a(...)

Dependencies
------------
BUILD-3A
BUILD-3F
VAL-2A

Architecture Position
---------------------
DEPLOY_BUNDLE_1A
        ↓
WORKFLOW-1G
        ↓
VAL-2A
        ↓
RUN-1A
        ↓
PIPE-1A
        ↓
ACT-1A

Status
------
Audited

Notes
-----
Responsibilities:

DEPLOY_BUNDLE_1A
        ↓
Load
        ↓
Normalize
        ↓
Validate
        ↓
Extract
        ↓
Return:
    workflow
    selector_pack
    run_meta

Runtime Responsibilities
------------------------
- Load deploy bundles from disk
- Normalize legacy bundle formats
- Validate deploy bundle structure
- Enforce selector_ref runtime policy
- Extract runtime workflow assets
- Produce stable runtime metadata
- Bridge deployment artifacts to execution

Runtime Contract
----------------
Extracted runtime assets consist of:

- workflow
- selector_pack
- run_meta

The loader intentionally returns only the
minimum runtime payload required for execution.

Compatibility
-------------
Supports legacy bundle compatibility by
automatically normalizing older fingerprint
formats and generating version fingerprints
when required.

Architecture Notes
------------------
This module represents the boundary between
build-time artifacts and runtime execution.

Upstream systems are responsible for capture,
normalization, validation, fingerprinting,
and deployment packaging.

Downstream systems are responsible for
workflow execution, browser orchestration,
action execution, logging, and runtime state.

This separation ensures deploy bundles remain
portable, reproducible, and backward compatible
across runtime versions.
"""

from __future__ import annotations  
  
import json  
from typing import Any, Dict, Mapping, Tuple  
  
from BUILD.build_3a_deploy_bundle_format import DEPLOY_BUNDLE_SCHEMA_ID  
from BUILD.build_3f_deploy_bundle_stamper import ensure_deploy_bundle_version_fingerprint_1a  
from VAL.val_2a_deploy_bundle_validator import assert_deploy_bundle_1a  
  
__all__ = [  
    "load_json_mapping_from_path",  
    "load_deploy_bundle_1a",  
    "load_deploy_bundle_1a_from_path",  
    "extract_runnable_from_deploy_bundle_1a",  
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
  
  
def load_deploy_bundle_1a(  
    bundle_obj: Mapping[str, Any],  
    *,  
    validate: bool = True,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
) -> Dict[str, Any]:  
    """  
    Load a DEPLOY_BUNDLE_1A bundle from an in-memory mapping.  
  
    Returns a shallow-copied dict suitable for downstream extraction.  
  
    Loader behavior:  
    - Normalizes/stamps version+fingerprint when require_version_fingerprint=True  
      (supports legacy bundles that used fingerprint.hexdigest or omitted version).  
    - Optionally validates after normalization.  
    """  
    if not isinstance(bundle_obj, Mapping):  
        raise ValueError("bundle_obj must be a mapping")  
  
    schema_id = bundle_obj.get("schema_id")  
    if schema_id != DEPLOY_BUNDLE_SCHEMA_ID:  
        raise ValueError(f"bundle_obj.schema_id must be {DEPLOY_BUNDLE_SCHEMA_ID}")  
  
    bundle: Dict[str, Any] = dict(bundle_obj)  
  
    if require_version_fingerprint:  
        bundle = ensure_deploy_bundle_version_fingerprint_1a(bundle)  
  
    if validate:  
        assert_deploy_bundle_1a(  
            bundle,  
            require_version_fingerprint=require_version_fingerprint,  
            require_selector_ref=require_selector_ref,  
        )  
  
    return bundle  
  
  
def load_deploy_bundle_1a_from_path(  
    path: str,  
    *,  
    validate: bool = True,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
) -> Dict[str, Any]:  
    """  
    Load a DEPLOY_BUNDLE_1A bundle from a JSON file path.  
    """  
    obj = load_json_mapping_from_path(path)  
    return load_deploy_bundle_1a(  
        obj,  
        validate=validate,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
    )  
  
  
def extract_runnable_from_deploy_bundle_1a(  
    deploy_bundle: Mapping[str, Any],  
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:  
    """  
    Extract runnable components from a DEPLOY_BUNDLE_1A bundle.  
  
    Returns:  
      (workflow_dict, selector_pack_dict, run_meta_dict)  
  
    run_meta_dict is intentionally small/stable; callers can extend separately.  
    """  
    if not isinstance(deploy_bundle, Mapping):  
        raise ValueError("deploy_bundle must be a mapping")  
    if deploy_bundle.get("schema_id") != DEPLOY_BUNDLE_SCHEMA_ID:  
        raise ValueError(f"deploy_bundle.schema_id must be {DEPLOY_BUNDLE_SCHEMA_ID}")  
  
    wf = deploy_bundle.get("workflow")  
    sp = deploy_bundle.get("selector_pack")  
    if not isinstance(wf, Mapping):  
        raise ValueError("deploy_bundle.workflow must be a mapping")  
    if not isinstance(sp, Mapping):  
        raise ValueError("deploy_bundle.selector_pack must be a mapping")  
  
    run_meta = {  
        "bundle_schema_id": DEPLOY_BUNDLE_SCHEMA_ID,  
        "bundle_name": str(deploy_bundle.get("name") or ""),  
        "bundle_version": str(deploy_bundle.get("version") or ""),  
    }  
    return dict(wf), dict(sp), run_meta  
  
  
def dev_smoke() -> None:  
    # Smoke: build a valid deploy bundle via existing builder, then load+extract.  
    from BUILD.build_3c_deploy_bundle_builder import build_stamp_validate_deploy_bundle_1a  
    from SNAP.snap_1a_workflow_capture import CapturedEvent  
    from SNAP.snap_1c_capture_bundle import build_capture_bundle_from_events  
  
    events = [  
        CapturedEvent(kind="navigate", seq=1, url="https://example.test/app"),  
        CapturedEvent(kind="click", seq=2, selector="#login"),  
    ]  
    cap = build_capture_bundle_from_events(events, bundle_name="captured")  
    dep = build_stamp_validate_deploy_bundle_1a(cap, strict=True)  
  
    loaded = load_deploy_bundle_1a(dep, validate=True)  
    wf, sp, meta = extract_runnable_from_deploy_bundle_1a(loaded)  
  
    assert wf["steps"][0]["action"] == "open"  
    assert isinstance(sp.get("selectors"), Mapping)  
    assert meta["bundle_schema_id"] == "DEPLOY_BUNDLE_1A"  
    assert meta["bundle_name"] == "captured"  
    assert meta["bundle_version"].startswith("sha256:")  
  
    # Legacy compatibility: simulate older bundles that had fingerprint.hexdigest, no sha256/version.  
    legacy = dict(dep)  
    legacy_fp = dict(legacy.get("fingerprint") or {})  
    legacy_fp["hexdigest"] = legacy_fp.get("sha256")  
    legacy_fp.pop("sha256", None)  
    legacy_fp["canonicalization"] = ""  
    legacy["fingerprint"] = legacy_fp  
    legacy.pop("version", None)  
  
    loaded_legacy = load_deploy_bundle_1a(legacy, validate=True, require_version_fingerprint=True)  
    assert loaded_legacy["fingerprint"]["sha256"] == dep["fingerprint"]["sha256"]  
    assert isinstance(loaded_legacy["version"], str) and loaded_legacy["version"].startswith("sha256:")  