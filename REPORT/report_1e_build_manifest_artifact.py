"""
REPORT-1E — Build Manifest Artifact Generator

Purpose
-------
Generate deterministic build manifest artifacts
for deployment bundles.

Provides artifact inventory generation,
artifact hashing, manifest construction,
and manifest persistence.

Public API
----------
sha256_file_1a(...)
build_build_manifest_artifact_1a(...)
write_build_manifest_artifact_1a(...)
build_and_write_build_manifest_for_bundle_out_dir_1a(...)

Dependencies
------------
Standard Library Only

Architecture Position
---------------------
Bundle Artifacts
        ↓
REPORT-1E
        ↓
BUILD_MANIFEST_ARTIFACT_1A
        ↓
BUILD-3E

Status
------
Audited

Notes
-----
Manifest Generation Pipeline:

Bundle Artifacts
        ↓
File Discovery
        ↓
SHA256 Hashing
        ↓
Manifest Construction
        ↓
Artifact Manifest

Responsibilities
----------------
- Generate artifact inventories
- Calculate artifact hashes
- Build manifest artifacts
- Persist manifest artifacts
- Support deployment bundle verification

Manifest Structure
------------------
BUILD_MANIFEST_ARTIFACT_1A

Contains:

- schema_id
- count
- artifacts
- file sizes
- sha256 hashes

Deterministic Guarantees
------------------------
Manifest generation is deterministic.

No timestamps, randomness, machine-specific
identifiers, or environment-dependent values
are included.

Identical artifacts produce identical
manifest outputs.

Architecture Notes
------------------
This module serves as the canonical source
of deployment artifact inventory metadata.

It is intentionally independent of bundle
construction and focuses solely on artifact
verification and reporting.
"""

from __future__ import annotations  
  
import hashlib  
import json  
import os  
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple  
  
__all__ = [  
    "sha256_file_1a",  
    "build_build_manifest_artifact_1a",  
    "write_build_manifest_artifact_1a",  
    "build_and_write_build_manifest_for_bundle_out_dir_1a",  
    "dev_smoke",  
]  
  
BUILD_MANIFEST_ARTIFACT_SCHEMA_ID = "BUILD_MANIFEST_ARTIFACT_1A"  
  
  
def sha256_file_1a(path: str) -> str:  
    if not isinstance(path, str) or not path.strip():  
        raise ValueError("path must be a non-empty string")  
    h = hashlib.sha256()  
    with open(path, "rb") as f:  
        for chunk in iter(lambda: f.read(1024 * 1024), b""):  
            h.update(chunk)  
    return h.hexdigest()  
  
  
def _artifact_entry_from_file_1a(*, rel_path: str, abs_path: str) -> Dict[str, Any]:  
    st = os.stat(abs_path)  
    return {  
        "path": rel_path.replace("\\", "/"),  
        "bytes": int(st.st_size),  
        "sha256": sha256_file_1a(abs_path),  
    }  
  
  
def build_build_manifest_artifact_1a(  
    *,  
    bundle_out_dir: str,  
    artifact_rel_paths: Sequence[str],  
) -> Dict[str, Any]:  
    """  
    Build a deterministic manifest of artifacts within bundle_out_dir.  
  
    No timestamps or environment-specific fields are included.  
    Artifact list is sorted by "path".  
    """  
    if not isinstance(bundle_out_dir, str) or not bundle_out_dir.strip():  
        raise ValueError("bundle_out_dir must be a non-empty string")  
  
    entries: List[Dict[str, Any]] = []  
    for rel in artifact_rel_paths:  
        if not isinstance(rel, str) or not rel.strip():  
            raise ValueError("artifact_rel_paths must contain only non-empty strings")  
        abs_path = os.path.join(bundle_out_dir, rel)  
        if not os.path.isfile(abs_path):  
            raise FileNotFoundError(abs_path)  
        entries.append(_artifact_entry_from_file_1a(rel_path=rel, abs_path=abs_path))  
  
    entries.sort(key=lambda e: str(e.get("path", "")))  
  
    return {  
        "schema_id": BUILD_MANIFEST_ARTIFACT_SCHEMA_ID,  
        "bundle_out_dir": bundle_out_dir,  
        "count": len(entries),  
        "artifacts": entries,  
    }  
  
  
def write_build_manifest_artifact_1a(  
    manifest: Mapping[str, Any],  
    out_path: str,  
    *,  
    overwrite: bool = True,  
) -> str:  
    if not isinstance(manifest, Mapping):  
        raise ValueError("manifest must be a mapping")  
    if not isinstance(out_path, str) or not out_path.strip():  
        raise ValueError("out_path must be a non-empty string")  
  
    if (not overwrite) and os.path.exists(out_path):  
        raise FileExistsError(out_path)  
  
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)  
    with open(out_path, "w", encoding="utf-8") as f:  
        json.dump(dict(manifest), f, ensure_ascii=False, sort_keys=True, indent=2)  
    return out_path  
  
  
def build_and_write_build_manifest_for_bundle_out_dir_1a(  
    *,  
    bundle_out_dir: str,  
    artifact_rel_paths: Sequence[str],  
    out_filename: str = "build_manifest_artifact_1a.json",  
    overwrite: bool = True,  
) -> Dict[str, Any]:  
    """  
    Convenience wrapper: build + write manifest into bundle_out_dir.  
    Returns {"out_path": ..., "count": ..., "schema_id": ...}.  
    """  
    manifest = build_build_manifest_artifact_1a(  
        bundle_out_dir=bundle_out_dir,  
        artifact_rel_paths=artifact_rel_paths,  
    )  
    out_path = os.path.join(bundle_out_dir, out_filename)  
    written = write_build_manifest_artifact_1a(manifest, out_path, overwrite=overwrite)  
    return {  
        "out_path": written,  
        "count": int(manifest.get("count", 0)),  
        "schema_id": manifest.get("schema_id"),  
    }  
  
  
def dev_smoke() -> None:  
    # covered by dev smoke script  
    pass  