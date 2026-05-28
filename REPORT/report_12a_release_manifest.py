"""  
REPORT-12A: Release Manifest (Milestone 12.3.1)  
  
Single responsibility:  
- Build a deterministic release manifest describing a workflow release bundle:  
  - component versions  
  - artifact file hashes (sha256) and sizes  
- Provide deterministic renderers (Markdown/JSON) for auditability.  
  
Design constraints:  
- No timestamps are generated in this module (determinism). If a timestamp is  
  required, the caller should add it externally.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Dict, List, Mapping, Optional, Sequence  
import hashlib  
import json  
import os  
  
  
__all__ = [  
    "ArtifactRef",  
    "ManifestComponent",  
    "ReleaseManifest",  
    "read_bytes_file",  
    "sha256_bytes_hex",  
    "artifact_ref_from_path",  
    "build_release_manifest",  
    "manifest_to_json",  
    "render_manifest_markdown",  
    "write_text_file",  
    "write_manifest_json",  
    "write_manifest_markdown",  
]  
  
  
@dataclass(frozen=True, slots=True)  
class ArtifactRef:  
    """  
    Immutable-ish identifier for an artifact on disk (as observed at manifest generation time).  
    """  
    path: str  
    sha256: str  
    size_bytes: int  
  
  
@dataclass(frozen=True, slots=True)  
class ManifestComponent:  
    component_id: str  # e.g. "workflow", "selectors", "framework"  
    version: str  
    artifact: Optional[ArtifactRef]  # framework may be version-only  
  
  
@dataclass(frozen=True, slots=True)  
class ReleaseManifest:  
    manifest_id: str  
    title: str  
    components: List[ManifestComponent]  
    notes: List[str]  
  
  
def read_bytes_file(path: str) -> bytes:  
    with open(path, "rb") as f:  
        return f.read()  
  
  
def sha256_bytes_hex(data: bytes) -> str:  
    return hashlib.sha256(data).hexdigest()  
  
  
def artifact_ref_from_path(path: str) -> ArtifactRef:  
    b = read_bytes_file(path)  
    return ArtifactRef(  
        path=path,  
        sha256=sha256_bytes_hex(b),  
        size_bytes=len(b),  
    )  
  
  
def build_release_manifest(  
    *,  
    workflow_version: str,  
    selectors_version: str,  
    framework_version: str,  
    workflow_path: Optional[str] = None,  
    selectors_path: Optional[str] = None,  
    framework_artifact_path: Optional[str] = None,  
    manifest_id: str = "RM-12A",  
    title: str = "Release Manifest",  
    notes: Optional[Sequence[str]] = None,  
) -> ReleaseManifest:  
    """  
    Build a deterministic manifest. If a component path is omitted, the component is recorded as version-only.  
    """  
    n = list(notes) if notes is not None else [  
        "This manifest is deterministic and contains no generated timestamps.",  
        "Hashes are sha256 of the artifact bytes as read at generation time.",  
    ]  
  
    components: List[ManifestComponent] = []  
  
    components.append(  
        ManifestComponent(  
            component_id="workflow",  
            version=workflow_version,  
            artifact=artifact_ref_from_path(workflow_path) if workflow_path else None,  
        )  
    )  
    components.append(  
        ManifestComponent(  
            component_id="selectors",  
            version=selectors_version,  
            artifact=artifact_ref_from_path(selectors_path) if selectors_path else None,  
        )  
    )  
    components.append(  
        ManifestComponent(  
            component_id="framework",  
            version=framework_version,  
            artifact=artifact_ref_from_path(framework_artifact_path) if framework_artifact_path else None,  
        )  
    )  
  
    # Ensure stable ordering by component_id (even if caller changes append order in future)  
    components_sorted = sorted(components, key=lambda c: c.component_id)  
  
    return ReleaseManifest(  
        manifest_id=manifest_id,  
        title=title,  
        components=components_sorted,  
        notes=n,  
    )  
  
  
def manifest_to_json(manifest: ReleaseManifest) -> str:  
    payload: Dict[str, object] = {  
        "manifest_id": manifest.manifest_id,  
        "title": manifest.title,  
        "components": [  
            {  
                "component_id": c.component_id,  
                "version": c.version,  
                "artifact": (  
                    None  
                    if c.artifact is None  
                    else {  
                        "path": c.artifact.path,  
                        "sha256": c.artifact.sha256,  
                        "size_bytes": c.artifact.size_bytes,  
                    }  
                ),  
            }  
            for c in manifest.components  
        ],  
        "notes": list(manifest.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_manifest_markdown(manifest: ReleaseManifest) -> str:  
    lines: List[str] = []  
    lines.append(f"# { _md(manifest.title) }")  
    lines.append("")  
    lines.append(f"**Manifest ID:** { _md(manifest.manifest_id) }")  
    lines.append("")  
    lines.append("## Components")  
    lines.append("")  
    for c in manifest.components:  
        lines.append(f"### { _md(c.component_id) }")  
        lines.append("")  
        lines.append(f"- **Version:** { _md(c.version) }")  
        if c.artifact is None:  
            lines.append("- **Artifact:** (version-only; no file recorded)")  
        else:  
            # Normalize to forward slashes for more stable display across Windows tools,  
            # while keeping the original path in the JSON.  
            display_path = c.artifact.path.replace("\\", "/")  
            lines.append(f"- **Artifact path:** { _md(display_path) }")  
            lines.append(f"- **sha256:** `{ _md(c.artifact.sha256) }`")  
            lines.append(f"- **Size (bytes):** { c.artifact.size_bytes }")  
        lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in manifest.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_manifest_json(path: str, manifest: ReleaseManifest) -> None:  
    write_text_file(path, manifest_to_json(manifest))  
  
  
def write_manifest_markdown(path: str, manifest: ReleaseManifest) -> None:  
    write_text_file(path, render_manifest_markdown(manifest))  