"""  
report_12g_evidence_bundle_assembler.py  
  
Milestone 12.5.7 — Evidence bundle assembler  
  
Deterministically assembles a single "evidence bundle" object from caller-supplied  
inputs (dicts/strings) that typically come from prior 12.5.x modules:  
- Alerting signals outputs (12.5.2)  
- Audit logging + replay spec/index (12.5.3)  
- Replay index verification result (12.5.4)  
- Incident packet manifest (12.5.5)  
- Release readiness gate policy/decision (12.5.6)  
  
Design goals:  
- Pure functions wherever practical.  
- Deterministic JSON and Markdown renderers.  
- Stable fingerprinting (sha256 over canonical JSON without timestamps).  
- Optional artifact inventory hashing for provided artifact *text* (sha256/size).  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from hashlib import sha256  
import json  
from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence, Tuple, List  
  
  
__all__ = [  
    "EVIDENCE_BUNDLE_SCHEMA_ID",  
    "canonical_json_dumps",  
    "sha256_hex_of_text",  
    "build_artifact_text_inventory",  
    "compute_bundle_fingerprint_sha256",  
    "assemble_evidence_bundle",  
    "render_evidence_bundle_markdown",  
    "validate_evidence_bundle_basic",  
]  
  
  
EVIDENCE_BUNDLE_SCHEMA_ID = "report_12g_evidence_bundle_assembler/v1"  
  
  
def canonical_json_dumps(obj: Any) -> str:  
    """  
    Deterministic JSON serializer:  
    - sort_keys=True ensures stable key ordering for dicts (including nested dicts)  
    - separators minimize whitespace deterministically  
    - ensure_ascii=False preserves unicode consistently  
    """  
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)  
  
  
def sha256_hex_of_text(text: str) -> str:  
    """  
    Deterministic SHA256 hex of UTF-8 encoded text.  
    """  
    h = sha256()  
    h.update(text.encode("utf-8"))  
    return h.hexdigest()  
  
  
def _as_strict_str(x: Any) -> str:  
    if x is None:  
        return ""  
    if isinstance(x, str):  
        return x  
    return str(x)  
  
  
def build_artifact_text_inventory(artifacts_text: Mapping[str, str]) -> List[Dict[str, Any]]:  
    """  
    Deterministically builds an inventory from provided artifact text content.  
  
    Input:  
      artifacts_text: mapping artifact_name -> artifact_text  
  
    Output: list of entries sorted by artifact_name:  
      [  
        {"name": "...", "sha256": "...", "size_bytes": 123},  
        ...  
      ]  
    """  
    items: List[Tuple[str, str]] = sorted((k, artifacts_text[k]) for k in artifacts_text.keys())  
    out: List[Dict[str, Any]] = []  
    for name, text in items:  
        b = text.encode("utf-8")  
        out.append(  
            {  
                "name": name,  
                "sha256": sha256(b).hexdigest(),  
                "size_bytes": len(b),  
            }  
        )  
    return out  
  
  
def compute_bundle_fingerprint_sha256(bundle_without_fingerprint: Mapping[str, Any]) -> str:  
    """  
    Stable fingerprint of the bundle derived from canonical JSON of the bundle object,  
    excluding the fingerprint field itself (caller responsibility).  
    """  
    canon = canonical_json_dumps(bundle_without_fingerprint)  
    h = sha256()  
    h.update(canon.encode("utf-8"))  
    return h.hexdigest()  
  
  
def assemble_evidence_bundle(  
    *,  
    bundle_id: str,  
    scope: str,  
    created_date: Optional[str] = None,  
    notes: Optional[str] = None,  
    # Inputs from prior modules are accepted as dicts for compatibility/decoupling.  
    alerting: Optional[Mapping[str, Any]] = None,  
    audit_log_spec: Optional[Mapping[str, Any]] = None,  
    replay_index: Optional[Mapping[str, Any]] = None,  
    replay_verification: Optional[Mapping[str, Any]] = None,  
    incident_packet_manifest: Optional[Mapping[str, Any]] = None,  
    release_readiness: Optional[Mapping[str, Any]] = None,  
    # Optional artifact hashing from provided text (NO file IO here; caller supplies text).  
    artifacts_text: Optional[Mapping[str, str]] = None,  
) -> Dict[str, Any]:  
    """  
    Assemble an evidence bundle deterministically.  
  
    No timestamps are generated. If a created_date is desired, the caller must provide it  
    (e.g., "2026-04-23"). This keeps the module deterministic.  
    """  
    if not isinstance(bundle_id, str) or not bundle_id.strip():  
        raise ValueError("bundle_id must be a non-empty string")  
    if not isinstance(scope, str) or not scope.strip():  
        raise ValueError("scope must be a non-empty string")  
  
    sections: Dict[str, Any] = {}  
  
    if alerting is not None:  
        sections["alerting"] = dict(alerting)  
    if audit_log_spec is not None:  
        sections["audit_log_spec"] = dict(audit_log_spec)  
    if replay_index is not None:  
        sections["replay_index"] = dict(replay_index)  
    if replay_verification is not None:  
        sections["replay_verification"] = dict(replay_verification)  
    if incident_packet_manifest is not None:  
        sections["incident_packet_manifest"] = dict(incident_packet_manifest)  
    if release_readiness is not None:  
        sections["release_readiness"] = dict(release_readiness)  
  
    artifact_inventory: Optional[List[Dict[str, Any]]] = None  
    if artifacts_text is not None:  
        artifact_inventory = build_artifact_text_inventory(artifacts_text)  
  
    # Build bundle WITHOUT fingerprint first  
    bundle_wo_fp: Dict[str, Any] = {  
        "schema": EVIDENCE_BUNDLE_SCHEMA_ID,  
        "bundle_id": bundle_id,  
        "scope": scope,  
        "created_date": created_date,  
        "notes": notes,  
        "sections": sections,  
        "artifact_inventory": artifact_inventory,  
    }  
  
    # Fingerprint of canonical JSON (excluding fingerprint)  
    fp = compute_bundle_fingerprint_sha256(bundle_wo_fp)  
  
    # Final bundle includes fingerprint  
    bundle: Dict[str, Any] = dict(bundle_wo_fp)  
    bundle["bundle_fingerprint_sha256"] = fp  
    return bundle  
  
  
_SECTION_ORDER: Tuple[Tuple[str, str], ...] = (  
    ("release_readiness", "Release readiness"),  
    ("alerting", "Alerting"),  
    ("replay_verification", "Replay verification"),  
    ("replay_index", "Replay index"),  
    ("audit_log_spec", "Audit log spec"),  
    ("incident_packet_manifest", "Incident packet manifest"),  
)  
  
  
def render_evidence_bundle_markdown(bundle: Mapping[str, Any]) -> str:  
    """  
    Deterministic Markdown renderer for an evidence bundle.  
    Uses a stable section order and canonical JSON blocks.  
    """  
    schema = _as_strict_str(bundle.get("schema"))  
    bundle_id = _as_strict_str(bundle.get("bundle_id"))  
    scope = _as_strict_str(bundle.get("scope"))  
    created_date = bundle.get("created_date")  
    notes = bundle.get("notes")  
    fp = _as_strict_str(bundle.get("bundle_fingerprint_sha256"))  
  
    lines: List[str] = []  
    lines.append(f"# Evidence Bundle: {bundle_id}".rstrip())  
    lines.append("")  
    lines.append(f"- Schema: `{schema}`")  
    lines.append(f"- Scope: `{scope}`")  
    if created_date is not None:  
        lines.append(f"- Created date: `{_as_strict_str(created_date)}`")  
    if notes is not None:  
        lines.append(f"- Notes: {_as_strict_str(notes)}")  
    lines.append(f"- Fingerprint (sha256): `{fp}`")  
    lines.append("")  
  
    sections = bundle.get("sections") or {}  
    if not isinstance(sections, Mapping):  
        sections = {}  
  
    lines.append("## Sections")  
    lines.append("")  
  
    # Render sections in stable order; then any extras sorted by key  
    seen = set()  
    for key, title in _SECTION_ORDER:  
        if key in sections:  
            seen.add(key)  
            lines.append(f"### {title}")  
            lines.append("")  
            lines.append("```json")  
            lines.append(canonical_json_dumps(sections[key]))  
            lines.append("```")  
            lines.append("")  
  
    extra_keys = sorted(k for k in sections.keys() if k not in seen)  
    for key in extra_keys:  
        lines.append(f"### {key}")  
        lines.append("")  
        lines.append("```json")  
        lines.append(canonical_json_dumps(sections[key]))  
        lines.append("```")  
        lines.append("")  
  
    inv = bundle.get("artifact_inventory")  
    if inv is not None:  
        lines.append("## Artifact inventory (text-based)")  
        lines.append("")  
        # Render a deterministic table (expects inventory already sorted by name)  
        lines.append("| name | sha256 | size_bytes |")  
        lines.append("|---|---|---:|")  
        if isinstance(inv, Sequence):  
            for entry in inv:  
                if not isinstance(entry, Mapping):  
                    continue  
                name = _as_strict_str(entry.get("name"))  
                sh = _as_strict_str(entry.get("sha256"))  
                sz = entry.get("size_bytes")  
                sz_s = _as_strict_str(sz)  
                lines.append(f"| `{name}` | `{sh}` | {sz_s} |")  
        lines.append("")  
  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def validate_evidence_bundle_basic(bundle: Mapping[str, Any]) -> Tuple[bool, List[str]]:  
    """  
    Lightweight structural validation (deterministic).  
    Does not require any upstream module schemas; only checks required fields exist.  
    """  
    problems: List[str] = []  
  
    if not isinstance(bundle, Mapping):  
        return False, ["bundle is not a mapping"]  
  
    if bundle.get("schema") != EVIDENCE_BUNDLE_SCHEMA_ID:  
        problems.append("schema mismatch or missing")  
  
    bundle_id = bundle.get("bundle_id")  
    if not isinstance(bundle_id, str) or not bundle_id.strip():  
        problems.append("bundle_id missing/invalid")  
  
    scope = bundle.get("scope")  
    if not isinstance(scope, str) or not scope.strip():  
        problems.append("scope missing/invalid")  
  
    sections = bundle.get("sections")  
    if sections is None or not isinstance(sections, Mapping):  
        problems.append("sections missing/invalid")  
  
    fp = bundle.get("bundle_fingerprint_sha256")  
    if not isinstance(fp, str) or len(fp) != 64:  
        problems.append("bundle_fingerprint_sha256 missing/invalid")  
  
    return (len(problems) == 0), problems  