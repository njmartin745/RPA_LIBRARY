"""
BUILD-3B — Bundle Fingerprint Engine

Purpose
-------
Generate deterministic fingerprints and version
identifiers for deployment artifacts.

Provides canonical serialization, hashing,
fingerprint generation, and version derivation
for reproducible bundle identity.

Public API
----------
DEFAULT_FINGERPRINT_DROP_TOP_LEVEL_KEYS
canonical_bytes_for_fingerprint(...)
compute_sha256_hex(...)
compute_bundle_fingerprint(...)
stamp_bundle_version_and_fingerprint(...)

Dependencies
------------
Standard Library Only

Architecture Position
---------------------
DEPLOY_BUNDLE
        ↓
BUILD-3B
        ↓
Fingerprint
        ↓
Version
        ↓
BUILD-3F

Status
------
Audited

Notes
-----
Fingerprint Pipeline:

Bundle
    ↓
Canonical JSON
    ↓
SHA256
    ↓
Fingerprint
    ↓
Version

Responsibilities
----------------
- Canonicalize bundle content
- Generate deterministic hashes
- Generate bundle fingerprints
- Generate bundle versions
- Prevent self-referential hashing
- Support reproducible builds

Canonicalization Rules
----------------------
- UTF-8 encoding
- JSON serialization
- sort_keys=True
- Compact separators
- No whitespace significance

Fingerprint Rules
-----------------
The following top-level keys are excluded
from fingerprint generation:

- fingerprint
- bundle_fingerprint
- version
- bundle_version

This prevents recursive fingerprint generation.

Deterministic Guarantees
------------------------
Identical bundle content produces identical
fingerprints and version identifiers.

No timestamps, randomness, machine identifiers,
or environment-specific values influence output.

Architecture Notes
------------------
This module is the canonical source of truth
for bundle identity generation throughout
the deployment pipeline.
"""

from __future__ import annotations  
  
import hashlib  
import json  
from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence, Tuple  
  
__all__ = [  
    "DEFAULT_FINGERPRINT_DROP_TOP_LEVEL_KEYS",  
    "canonical_bytes_for_fingerprint",  
    "compute_sha256_hex",  
    "compute_bundle_fingerprint",  
    "stamp_bundle_version_and_fingerprint",  
    "dev_smoke",  
]  
  
DEFAULT_FINGERPRINT_DROP_TOP_LEVEL_KEYS: Tuple[str, ...] = (  
    "fingerprint",  
    "bundle_fingerprint",  
    "version",  
    "bundle_version",  
)  
  
  
def canonical_bytes_for_fingerprint(obj: Any) -> bytes:  
    """  
    Deterministic canonicalization for hashing:  
      - JSON  
      - ensure_ascii=False  
      - sort_keys=True (recursive for dict keys)  
      - separators without whitespace  
    """  
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))  
    return s.encode("utf-8")  
  
  
def compute_sha256_hex(data: bytes) -> str:  
    return hashlib.sha256(data).hexdigest()  
  
  
def _drop_top_level_keys(d: Mapping[str, Any], drop_keys: Sequence[str]) -> Dict[str, Any]:  
    out: Dict[str, Any] = {}  
    drop = set(drop_keys)  
    for k, v in d.items():  
        if k in drop:  
            continue  
        out[k] = v  
    return out  
  
  
def compute_bundle_fingerprint(  
    bundle: Mapping[str, Any],  
    *,  
    drop_top_level_keys: Sequence[str] = DEFAULT_FINGERPRINT_DROP_TOP_LEVEL_KEYS,  
) -> Dict[str, Any]:  
    """  
    Compute deterministic bundle fingerprint (sha256 over canonical JSON bytes),  
    excluding specified top-level keys to avoid self-referential hashing.  
    """  
    if not isinstance(bundle, Mapping):  
        raise ValueError("bundle must be a mapping")  
  
    material = _drop_top_level_keys(bundle, drop_top_level_keys)  
    b = canonical_bytes_for_fingerprint(material)  
    sha = compute_sha256_hex(b)  
  
    return {  
        "algo": "sha256",  
        "canonicalization": "json_sort_keys_separators_v1",  
        "sha256": sha,  
        "bytes": len(b),  
        "dropped_top_level_keys": list(drop_top_level_keys),  
    }  
  
  
def stamp_bundle_version_and_fingerprint(  
    bundle: Mapping[str, Any],  
    *,  
    version: Optional[str] = None,  
    version_prefix: str = "sha256:",  
    version_len: int = 12,  
    drop_top_level_keys: Sequence[str] = DEFAULT_FINGERPRINT_DROP_TOP_LEVEL_KEYS,  
    fingerprint_key: str = "fingerprint",  
    version_key: str = "version",  
) -> Dict[str, Any]:  
    """  
    Return a new bundle dict stamped with:  
      - bundle[version_key] (deterministic from content unless explicitly provided)  
      - bundle[fingerprint_key] (deterministic)  
    """  
    if not isinstance(bundle, Mapping):  
        raise ValueError("bundle must be a mapping")  
  
    fp = compute_bundle_fingerprint(bundle, drop_top_level_keys=drop_top_level_keys)  
  
    if version is None:  
        if not isinstance(version_prefix, str):  
            raise ValueError("version_prefix must be a string")  
        if not isinstance(version_len, int) or version_len <= 0:  
            raise ValueError("version_len must be a positive int")  
        version = f"{version_prefix}{fp['sha256'][:version_len]}"  
  
    out: Dict[str, Any] = dict(bundle)  
    out[version_key] = version  
    out[fingerprint_key] = fp  
    return out  
  
  
def dev_smoke() -> None:  
    b1 = {"schema_id": "DEPLOY_BUNDLE_1A", "name": "x", "workflow": {"steps": []}, "selector_pack": {"selectors": {}}}  
    b2 = {"name": "x", "selector_pack": {"selectors": {}}, "workflow": {"steps": []}, "schema_id": "DEPLOY_BUNDLE_1A"}  
  
    s1 = stamp_bundle_version_and_fingerprint(b1)  
    s2 = stamp_bundle_version_and_fingerprint(b2)  
  
    assert s1["fingerprint"]["sha256"] == s2["fingerprint"]["sha256"]  # key order should not matter  
    assert s1["version"] == s2["version"]  
  
    b3 = dict(b1)  
    b3["name"] = "y"  
    s3 = stamp_bundle_version_and_fingerprint(b3)  
    assert s3["fingerprint"]["sha256"] != s1["fingerprint"]["sha256"]  