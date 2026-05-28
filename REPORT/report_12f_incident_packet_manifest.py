"""  
REPORT-12F: Incident Packet Manifest (Milestone 12.5.5)  
  
Single responsibility:  
- Define a canonical, deterministic "incident packet" manifest structure.  
- Provide pure validators.  
- Provide deterministic JSON/Markdown renderers.  
- Provide deterministic SHA256 fingerprinting over canonical JSON.  
  
Determinism:  
- No timestamps generated.  
- Stable ordering of artifacts (by kind, label, path).  
- JSON uses sort_keys=True and stable separators for canonical hashing.  
  
This module does NOT collect artifacts. It only describes them.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple  
import hashlib  
import json  
  
  
__all__ = [  
    "ArtifactRef",  
    "IncidentPacket",  
    "get_incident_packet_template",  
    "validate_incident_packet",  
    "canonical_packet_dict",  
    "packet_to_json",  
    "render_packet_markdown",  
    "sha256_hex",  
    "packet_fingerprint_sha256",  
    "write_text_file",  
    "write_packet_json",  
    "write_packet_markdown",  
]  
  
  
@dataclass(frozen=True, slots=True)  
class ArtifactRef:  
    """  
    Reference to an artifact related to an incident.  
  
    - kind: logical artifact type (e.g., "run_log", "screenshot", "run_report", "audit_log_jsonl", "replay_index_json")  
    - label: short identifier (e.g., "latest", "run-2026-01-01", "step-3")  
    - path: path or URI-like string (framework chooses meaning)  
    - sha256: optional integrity hash (hex, 64 chars) if already computed elsewhere  
    """  
    kind: str  
    label: str  
    path: str  
    sha256: Optional[str] = None  
  
  
@dataclass(frozen=True, slots=True)  
class IncidentPacket:  
    packet_id: str  
    title: str  
    incident_id: str  
    run_id: str  
    env: str  
    summary: str  
    artifacts: Tuple[ArtifactRef, ...]  
    notes: Tuple[str, ...]  
  
  
def sha256_hex(text: str) -> str:  
    h = hashlib.sha256()  
    h.update(text.encode("utf-8"))  
    return h.hexdigest()  
  
  
def _sorted_artifacts(artifacts: Sequence[ArtifactRef]) -> List[ArtifactRef]:  
    return sorted(list(artifacts), key=lambda a: (a.kind, a.label, a.path, a.sha256 or ""))  
  
  
def get_incident_packet_template(  
    *,  
    packet_id: str = "INCIDENT-PACKET-12F",  
    title: str = "Incident Packet Manifest",  
    incident_id: str = "INCIDENT-UNSET",  
    run_id: str = "RUN-UNSET",  
    env: str = "prod",  
    summary: str = "Describe impact, scope, and suspected cause.",  
    notes: Optional[Sequence[str]] = None,  
) -> IncidentPacket:  
    n = tuple(notes) if notes is not None else (  
        "This packet is deterministic and contains no generated timestamps.",  
        "Prefer immutable references (bundle fingerprint, replay index, audit log JSONL) when possible.",  
        "Include enough evidence to reproduce: workflow, selectors bundle, logs, screenshots, reports.",  
    )  
    return IncidentPacket(  
        packet_id=packet_id,  
        title=title,  
        incident_id=incident_id,  
        run_id=run_id,  
        env=env,  
        summary=summary,  
        artifacts=tuple(),  
        notes=n,  
    )  
  
  
def validate_incident_packet(packet: IncidentPacket) -> List[str]:  
    errs: List[str] = []  
    if not packet.packet_id:  
        errs.append("packet_id is required")  
    if not packet.title:  
        errs.append("title is required")  
    if not packet.incident_id:  
        errs.append("incident_id is required")  
    if not packet.run_id:  
        errs.append("run_id is required")  
    if not packet.env:  
        errs.append("env is required")  
    if not isinstance(packet.summary, str):  
        errs.append("summary must be a str")  
  
    seen = set()  
    for a in packet.artifacts:  
        if not a.kind:  
            errs.append("artifact.kind is required")  
        if not a.label:  
            errs.append("artifact.label is required")  
        if not a.path:  
            errs.append("artifact.path is required")  
        key = (a.kind, a.label, a.path)  
        if key in seen:  
            errs.append(f"Duplicate artifact ref: kind={a.kind!r} label={a.label!r} path={a.path!r}")  
        seen.add(key)  
        if a.sha256 is not None:  
            if not isinstance(a.sha256, str) or len(a.sha256) != 64:  
                errs.append(f"artifact.sha256 must be 64-char hex or None: {a.sha256!r}")  
    return errs  
  
  
def canonical_packet_dict(packet: IncidentPacket) -> Dict[str, Any]:  
    errs = validate_incident_packet(packet)  
    if errs:  
        raise ValueError("; ".join(errs))  
  
    return {  
        "packet_id": packet.packet_id,  
        "title": packet.title,  
        "incident_id": packet.incident_id,  
        "run_id": packet.run_id,  
        "env": packet.env,  
        "summary": packet.summary,  
        "artifacts": [  
            {  
                "kind": a.kind,  
                "label": a.label,  
                "path": a.path,  
                "sha256": a.sha256,  
            }  
            for a in _sorted_artifacts(packet.artifacts)  
        ],  
        "notes": list(packet.notes),  
    }  
  
  
def packet_to_json(packet: IncidentPacket) -> str:  
    payload = canonical_packet_dict(packet)  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def packet_fingerprint_sha256(packet: IncidentPacket) -> str:  
    """  
    Deterministic fingerprint of the packet contents.  
    """  
    payload = canonical_packet_dict(packet)  
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"))  
    return sha256_hex(canon)  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_packet_markdown(packet: IncidentPacket) -> str:  
    fp = packet_fingerprint_sha256(packet)  
  
    lines: List[str] = []  
    lines.append(f"# { _md(packet.title) }")  
    lines.append("")  
    lines.append(f"**Packet ID:** { _md(packet.packet_id) }")  
    lines.append(f"**Incident ID:** `{ _md(packet.incident_id) }`")  
    lines.append(f"**Run ID:** `{ _md(packet.run_id) }`")  
    lines.append(f"**Environment:** `{ _md(packet.env) }`")  
    lines.append(f"**Fingerprint (sha256):** `{fp}`")  
    lines.append("")  
    lines.append("## Summary")  
    lines.append("")  
    lines.append(_md(packet.summary))  
    lines.append("")  
    lines.append("## Artifacts")  
    lines.append("")  
    arts = _sorted_artifacts(packet.artifacts)  
    if not arts:  
        lines.append("(none)")  
        lines.append("")  
    else:  
        for a in arts:  
            if a.sha256:  
                lines.append(f"- `{_md(a.kind)}` `{_md(a.label)}` — {_md(a.path)} (sha256 `{a.sha256}`)")  
            else:  
                lines.append(f"- `{_md(a.kind)}` `{_md(a.label)}` — {_md(a.path)}")  
        lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in packet.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_packet_json(path: str, packet: IncidentPacket) -> None:  
    write_text_file(path, packet_to_json(packet))  
  
  
def write_packet_markdown(path: str, packet: IncidentPacket) -> None:  
    write_text_file(path, render_packet_markdown(packet))  