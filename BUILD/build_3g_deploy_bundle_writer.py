from __future__ import annotations  
  
import json  
import os  
from typing import Any, Dict, Mapping, Optional  
  
from BUILD.build_3a_deploy_bundle_format import DEPLOY_BUNDLE_SCHEMA_ID  
from BUILD.build_3f_deploy_bundle_stamper import ensure_deploy_bundle_version_fingerprint_1a  
from VAL.val_2a_deploy_bundle_validator import assert_deploy_bundle_1a  
  
__all__ = [  
    "dumps_deploy_bundle_1a_json",  
    "write_deploy_bundle_1a_to_path",  
    "dev_smoke",  
]  
  
  
def dumps_deploy_bundle_1a_json(  
    bundle: Mapping[str, Any],  
    *,  
    pretty: bool = False,  
    ensure_trailing_newline: bool = True,  
) -> str:  
    """  
    Deterministically JSON-serialize a DEPLOY_BUNDLE_1A mapping.  
  
    - sort_keys=True for stable diffs  
    - pretty=False uses compact separators for stability and minimal size  
    """  
    if not isinstance(bundle, Mapping):  
        raise TypeError(f"bundle must be a mapping, got: {type(bundle)!r}")  
    if bundle.get("schema_id") != DEPLOY_BUNDLE_SCHEMA_ID:  
        raise ValueError(f"bundle.schema_id must be {DEPLOY_BUNDLE_SCHEMA_ID}")  
  
    if pretty:  
        s = json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=2)  
    else:  
        s = json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))  
  
    if ensure_trailing_newline and not s.endswith("\n"):  
        s += "\n"  
    return s  
  
  
def write_deploy_bundle_1a_to_path(  
    bundle: Mapping[str, Any],  
    path: str,  
    *,  
    validate: bool = True,  
    normalize_stamp: bool = True,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
    pretty: bool = False,  
    atomic: bool = True,  
    encoding: str = "utf-8",  
) -> Dict[str, Any]:  
    """  
    Write a DEPLOY_BUNDLE_1A JSON file to `path`.  
  
    - normalize_stamp=True: ensures version+fingerprint exist (legacy compatibility)  
    - validate=True: validates (and raises) before writing  
    - atomic=True: writes to path + ".tmp" then os.replace()  
    """  
    if not isinstance(path, str) or not path.strip():  
        raise ValueError("path must be a non-empty string")  
  
    out: Dict[str, Any] = dict(bundle)  
  
    if normalize_stamp and require_version_fingerprint:  
        out = ensure_deploy_bundle_version_fingerprint_1a(out)  
  
    if validate:  
        assert_deploy_bundle_1a(  
            out,  
            require_version_fingerprint=require_version_fingerprint,  
            require_selector_ref=require_selector_ref,  
        )  
  
    text = dumps_deploy_bundle_1a_json(out, pretty=pretty, ensure_trailing_newline=True)  
  
    parent = os.path.dirname(os.path.abspath(path))  
    if parent:  
        os.makedirs(parent, exist_ok=True)  
  
    if atomic:  
        tmp_path = path + ".tmp"  
        with open(tmp_path, "w", encoding=encoding, newline="\n") as f:  
            f.write(text)  
        os.replace(tmp_path, path)  
    else:  
        with open(path, "w", encoding=encoding, newline="\n") as f:  
            f.write(text)  
  
    return out  
  
  
def dev_smoke() -> None:  
    bundle = {  
        "schema_id": "DEPLOY_BUNDLE_1A",  
        "name": "x",  
        "workflow": {"steps": [{"action": "open", "url": "https://example.test"}]},  
        "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "x", "selectors": {}},  
        "meta": {"source_schema_id": "CAPTURE_BUNDLE_1A", "source_name": "x"},  
        # intentionally omit version/fingerprint to test normalize_stamp  
    }  
  
    path = "dev_smoke_tmp_deploy_bundle_1a.json"  
    try:  
        written = write_deploy_bundle_1a_to_path(  
            bundle,  
            path,  
            validate=True,  
            normalize_stamp=True,  
            require_version_fingerprint=True,  
            require_selector_ref=True,  
            pretty=False,  
            atomic=True,  
        )  
        assert written.get("schema_id") == "DEPLOY_BUNDLE_1A"  
        assert isinstance(written.get("version"), str) and written["version"].startswith("sha256:")  
        assert written.get("fingerprint", {}).get("algo") == "sha256"  
  
        with open(path, "r", encoding="utf-8") as f:  
            loaded = json.load(f)  
        assert loaded.get("schema_id") == "DEPLOY_BUNDLE_1A"  
        assert loaded.get("fingerprint", {}).get("sha256") == written["fingerprint"]["sha256"]  
    finally:  
        try:  
            if os.path.exists(path):  
                os.remove(path)  
            if os.path.exists(path + ".tmp"):  
                os.remove(path + ".tmp")  
        except Exception:  
            # smoke cleanup should not mask failures above  
            pass  