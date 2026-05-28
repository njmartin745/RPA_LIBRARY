from __future__ import annotations  
  
from typing import Any, Dict, Mapping, Optional  
  
from BUILD.build_3b_bundle_fingerprint import stamp_bundle_version_and_fingerprint  
from VAL.val_2a_deploy_bundle_validator import validate_deploy_bundle_1a  
  
__all__ = [  
    "ensure_deploy_bundle_version_fingerprint_1a",  
    "dev_smoke",  
]  
  
  
def _is_nonempty_str(x: Any) -> bool:  
    return isinstance(x, str) and x.strip() != ""  
  
  
def _hex64(x: Any) -> bool:  
    if not isinstance(x, str) or len(x) != 64:  
        return False  
    try:  
        int(x, 16)  
        return True  
    except Exception:  
        return False  
  
  
def ensure_deploy_bundle_version_fingerprint_1a(  
    bundle: Mapping[str, Any],  
    *,  
    version: Optional[str] = None,  
    version_prefix: str = "sha256:",  
    version_len: int = 12,  
    fingerprint_key: str = "fingerprint",  
    add_hexdigest_alias: bool = True,  
) -> Dict[str, Any]:  
    """  
    Ensure DEPLOY_BUNDLE_1A has a schema-compliant version+fingerprint.  
  
    Behavior:  
    - If fingerprint.sha256 is missing but fingerprint.hexdigest is a 64-hex string, copy it to sha256.  
    - Otherwise, deterministically (re)stamp using BUILD.build_3b_bundle_fingerprint.stamp_bundle_version_and_fingerprint.  
    - Ensure fingerprint.algo == 'sha256' and fingerprint.canonicalization is non-empty (validator warns if empty).  
    - Ensure bundle.version is non-empty (derived from sha256 if needed).  
    - Optionally add fingerprint.hexdigest as an alias of fingerprint.sha256 (compat).  
    """  
    if not isinstance(bundle, Mapping):  
        raise TypeError(f"bundle must be a mapping, got: {type(bundle)!r}")  
  
    if version is not None and not _is_nonempty_str(version):  
        raise ValueError("version must be a non-empty string when provided")  
  
    if not isinstance(version_len, int) or version_len <= 0:  
        raise ValueError("version_len must be a positive int")  
  
    out: Dict[str, Any] = dict(bundle)  
  
    fp_any = out.get(fingerprint_key)  
    fp: Dict[str, Any] = dict(fp_any) if isinstance(fp_any, Mapping) else {}  
  
    # Legacy compatibility: accept hexdigest as sha256 if it looks correct.  
    if not _hex64(fp.get("sha256")) and _hex64(fp.get("hexdigest")):  
        fp["sha256"] = fp["hexdigest"]  
  
    # If still not valid, recompute deterministically using the framework stamper.  
    if not _hex64(fp.get("sha256")):  
        stamped = stamp_bundle_version_and_fingerprint(  
            out,  
            version=version,  
            version_prefix=version_prefix,  
            version_len=version_len,  
            fingerprint_key=fingerprint_key,  
        )  
        fp2_any = stamped.get(fingerprint_key)  
        fp2 = dict(fp2_any) if isinstance(fp2_any, Mapping) else {}  
        if add_hexdigest_alias and _hex64(fp2.get("sha256")):  
            fp2["hexdigest"] = fp2["sha256"]  
        if not _is_nonempty_str(fp2.get("canonicalization")):  
            fp2["canonicalization"] = "json_sort_keys_separators_v1"  
        stamped[fingerprint_key] = fp2  
        return stamped  
  
    # Otherwise: keep existing sha256, just normalize required fields.  
    fp["algo"] = "sha256"  
    if add_hexdigest_alias and _hex64(fp.get("sha256")):  
        fp["hexdigest"] = fp["sha256"]  
    if not _is_nonempty_str(fp.get("canonicalization")):  
        fp["canonicalization"] = "legacy_or_external"  
  
    out[fingerprint_key] = fp  
  
    if version is not None:  
        out["version"] = version.strip()  
    else:  
        if not _is_nonempty_str(out.get("version")):  
            out["version"] = f"{version_prefix}{fp['sha256'][:version_len]}"  
  
    return out  
  
  
def dev_smoke() -> None:  
    legacy = {  
        "schema_id": "DEPLOY_BUNDLE_1A",  
        "name": "x",  
        "workflow": {"steps": [{"action": "open", "url": "https://example.test"}]},  
        "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "x", "selectors": {}},  
        "fingerprint": {"algo": "sha256", "hexdigest": "0" * 64, "canonicalization": ""},  
        # version intentionally missing to test derivation  
    }  
  
    fixed = ensure_deploy_bundle_version_fingerprint_1a(legacy)  
    assert fixed["fingerprint"]["algo"] == "sha256"  
    assert fixed["fingerprint"]["sha256"] == "0" * 64  
    assert isinstance(fixed["version"], str) and fixed["version"].startswith("sha256:")  
  
    rep = validate_deploy_bundle_1a(fixed, require_version_fingerprint=True, require_selector_ref=True)  
    if not rep["ok"]:  
        raise AssertionError(f"expected ok=true, got: {rep!r}")  