"""  
REPORT-12B: Bundle Fingerprint (Milestone 12.3.2)  
  
Single responsibility:  
- Compute a deterministic bundle fingerprint from a ReleaseManifest.  
- Render fingerprint records as Markdown/JSON for auditability.  
  
Design:  
- Fingerprint intentionally ignores artifact paths to remain stable across machines/dirs.  
- Inputs are component_id + version + artifact sha256 + artifact size_bytes (if present).  
- Output is sha256 hex of a canonical, line-based input string.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Dict, List, Optional, Sequence  
import hashlib  
import json  
  
from REPORT.report_12a_release_manifest import ReleaseManifest  
  
  
__all__ = [  
    "BundleFingerprint",  
    "canonical_fingerprint_input",  
    "compute_bundle_fingerprint",  
    "fingerprint_to_json",  
    "render_fingerprint_markdown",  
    "write_text_file",  
    "write_fingerprint_json",  
    "write_fingerprint_markdown",  
]  
  
  
@dataclass(frozen=True, slots=True)  
class BundleFingerprint:  
    fingerprint_id: str  
    algorithm: str  
    fingerprint: str  
    input_canonical: str  
    notes: List[str]  
  
  
def canonical_fingerprint_input(manifest: ReleaseManifest) -> str:  
    """  
    Canonical deterministic input string for hashing.  
  
    Format (one line per component, in manifest.components order):  
      component_id|version|artifact_sha256|artifact_size_bytes  
    """  
    lines: List[str] = []  
    for c in manifest.components:  
        art_sha = "" if c.artifact is None else c.artifact.sha256  
        art_size = "" if c.artifact is None else str(c.artifact.size_bytes)  
        lines.append(f"{c.component_id}|{c.version}|{art_sha}|{art_size}")  
    return "\n".join(lines) + "\n"  
  
  
def _sha256_hex(text: str) -> str:  
    return hashlib.sha256(text.encode("utf-8")).hexdigest()  
  
  
def compute_bundle_fingerprint(  
    manifest: ReleaseManifest,  
    *,  
    fingerprint_id: str = "BF-12B",  
    algorithm: str = "sha256",  
    notes: Optional[Sequence[str]] = None,  
) -> BundleFingerprint:  
    """  
    Compute a deterministic fingerprint. Currently supports sha256 only.  
    """  
    if algorithm != "sha256":  
        raise ValueError("Only sha256 is supported for deterministic bundle fingerprinting")  
  
    inp = canonical_fingerprint_input(manifest)  
    fp = _sha256_hex(inp)  
  
    n = list(notes) if notes is not None else [  
        "Fingerprint ignores artifact paths; it hashes versions + artifact sha256 + artifact sizes.",  
        "Canonical input is line-based: component_id|version|artifact_sha256|artifact_size_bytes.",  
    ]  
  
    return BundleFingerprint(  
        fingerprint_id=fingerprint_id,  
        algorithm=algorithm,  
        fingerprint=fp,  
        input_canonical=inp,  
        notes=n,  
    )  
  
  
def fingerprint_to_json(bf: BundleFingerprint) -> str:  
    payload: Dict[str, object] = {  
        "fingerprint_id": bf.fingerprint_id,  
        "algorithm": bf.algorithm,  
        "fingerprint": bf.fingerprint,  
        "input_canonical": bf.input_canonical,  
        "notes": list(bf.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_fingerprint_markdown(bf: BundleFingerprint) -> str:  
    lines: List[str] = []  
    lines.append("# Bundle Fingerprint")  
    lines.append("")  
    lines.append(f"**Fingerprint ID:** { _md(bf.fingerprint_id) }")  
    lines.append(f"**Algorithm:** { _md(bf.algorithm) }")  
    lines.append("")  
    lines.append(f"**Fingerprint:** `{ _md(bf.fingerprint) }`")  
    lines.append("")  
    lines.append("## Canonical Input")  
    lines.append("")  
    lines.append("```text")  
    lines.append(_md(bf.input_canonical).rstrip("\n"))  
    lines.append("```")  
    lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in bf.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_fingerprint_json(path: str, bf: BundleFingerprint) -> None:  
    write_text_file(path, fingerprint_to_json(bf))  
  
  
def write_fingerprint_markdown(path: str, bf: BundleFingerprint) -> None:  
    write_text_file(path, render_fingerprint_markdown(bf))  