"""
BUILD-3E — Bundle Manifest Integrator

Purpose
-------
Generate and integrate documentation indexes
and build manifests for deployment bundle
output directories.

Provides a deterministic orchestration layer
that combines documentation discovery,
artifact indexing, and manifest generation.

Public API
----------
discover_bundle_artifact_rel_paths_1a(...)
build_bundle_out_dir_doc_index_and_manifest_1a(...)

Dependencies
------------
BUILD-3D
REPORT-1E

Architecture Position
---------------------
Bundle Output Directory
        ↓
BUILD-3E
        ↓
BUILD-3D
        ↓
REPORT-1E
        ↓
Bundle Metadata

Status
------
Audited

Notes
-----
Integration Pipeline:

Bundle Output Directory
        ↓
Artifact Discovery
        ↓
Documentation Index
        ↓
Artifact Manifest
        ↓
Bundle Metadata

Responsibilities
----------------
- Discover bundle artifacts
- Build documentation indexes
- Build artifact manifests
- Maintain deterministic ordering
- Coordinate bundle metadata generation
- Produce deployment-ready metadata assets

Artifact Discovery Rules
------------------------
- Recursive discovery supported
- Deterministic sorting
- POSIX path normalization
- Manifest self-exclusion
- Duplicate elimination

Deterministic Guarantees
------------------------
Artifact discovery, index generation,
and manifest generation are deterministic.

Identical bundle contents produce
identical metadata outputs.

Architecture Notes
------------------
This module serves as the orchestration layer
between documentation indexing and manifest
generation.

Index creation is delegated to BUILD-3D.

Manifest creation is delegated to REPORT-1E.
"""

from __future__ import annotations  
  
import os  
from typing import Any, Dict, List, Optional, Sequence, Set  
  
from BUILD.build_3d_doc_index_artifact_bundler import write_doc_index_artifact_to_bundle_out_dir_1a  
from REPORT.report_1e_build_manifest_artifact import build_and_write_build_manifest_for_bundle_out_dir_1a  
  
__all__ = [  
    "discover_bundle_artifact_rel_paths_1a",  
    "build_bundle_out_dir_doc_index_and_manifest_1a",  
    "dev_smoke",  
]  
  
  
def discover_bundle_artifact_rel_paths_1a(  
    *,  
    bundle_out_dir: str,  
    recursive: bool = True,  
    exclude_filenames: Optional[Set[str]] = None,  
) -> List[str]:  
    """  
    Deterministically discover artifact files within bundle_out_dir.  
    Returns relative paths with POSIX separators.  
  
    Notes:  
      - Sorted for deterministic output.  
      - Excludes any filenames in exclude_filenames (by basename match).  
    """  
    if not isinstance(bundle_out_dir, str) or not bundle_out_dir.strip():  
        raise ValueError("bundle_out_dir must be a non-empty string")  
  
    if not os.path.isdir(bundle_out_dir):  
        raise FileNotFoundError(bundle_out_dir)  
  
    exclude = set(exclude_filenames or set())  
  
    rel_paths: List[str] = []  
    if recursive:  
        for root, dirnames, filenames in os.walk(bundle_out_dir):  
            dirnames.sort()  
            filenames.sort()  
            for fn in filenames:  
                if fn in exclude:  
                    continue  
                abs_path = os.path.join(root, fn)  
                if not os.path.isfile(abs_path):  
                    continue  
                rel = os.path.relpath(abs_path, bundle_out_dir).replace("\\", "/")  
                rel_paths.append(rel)  
    else:  
        for fn in sorted(os.listdir(bundle_out_dir)):  
            if fn in exclude:  
                continue  
            abs_path = os.path.join(bundle_out_dir, fn)  
            if os.path.isfile(abs_path):  
                rel_paths.append(fn.replace("\\", "/"))  
  
    rel_paths.sort()  
    return rel_paths  
  
  
def build_bundle_out_dir_doc_index_and_manifest_1a(  
    *,  
    repo_root: str = ".",  
    doc_dir: str = "DOC",  
    bundle_out_dir: str,  
    doc_index_filename: str = "doc_index_artifact_1a.json",  
    manifest_filename: str = "build_manifest_artifact_1a.json",  
    strict_imports: bool = False,  
    overwrite: bool = True,  
    artifact_rel_paths: Optional[Sequence[str]] = None,  
) -> Dict[str, Any]:  
    """  
    Writes doc_index_artifact_1a.json into bundle_out_dir, then writes a build manifest  
    listing artifacts in bundle_out_dir (including the doc index).  
  
    If artifact_rel_paths is None, artifacts are discovered from bundle_out_dir.  
    The manifest file itself is excluded from discovery by default.  
    """  
    if not isinstance(bundle_out_dir, str) or not bundle_out_dir.strip():  
        raise ValueError("bundle_out_dir must be a non-empty string")  
  
    os.makedirs(bundle_out_dir, exist_ok=True)  
  
    doc_res = write_doc_index_artifact_to_bundle_out_dir_1a(  
        repo_root=repo_root,  
        doc_dir=doc_dir,  
        bundle_out_dir=bundle_out_dir,  
        out_filename=doc_index_filename,  
        strict_imports=strict_imports,  
        overwrite=overwrite,  
    )  
  
    if artifact_rel_paths is None:  
        artifact_rel_paths = discover_bundle_artifact_rel_paths_1a(  
            bundle_out_dir=bundle_out_dir,  
            recursive=True,  
            exclude_filenames={manifest_filename},  
        )  
  
    # Ensure doc index is included (deterministically).  
    art_list = list(artifact_rel_paths)  
    if doc_index_filename not in art_list:  
        art_list.append(doc_index_filename)  
    art_list = sorted(set(art_list))  
  
    man_res = build_and_write_build_manifest_for_bundle_out_dir_1a(  
        bundle_out_dir=bundle_out_dir,  
        artifact_rel_paths=art_list,  
        out_filename=manifest_filename,  
        overwrite=overwrite,  
    )  
  
    return {  
        "doc_index": doc_res,  
        "manifest": man_res,  
        "bundle_out_dir": bundle_out_dir,  
        "artifact_count": man_res["count"],  
    }  
  
  
def dev_smoke() -> None:  
    # covered by dev smoke script  
    pass  