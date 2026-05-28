"""  
REPORT-12C: Promotion Record (Milestone 12.3.3)  
  
Single responsibility:  
- Create a deterministic promotion record that can be stored with release artifacts:  
  - from_env -> to_env  
  - promotion decision (allowed/failed/missing)  
  - release manifest (versions + artifact hashes)  
  - bundle fingerprint (immutable identity)  
  - evidence used for gating (optionally redacted)  
  
Determinism:  
- No timestamps generated in this module.  
- Evidence is normalized into JSON-safe, stable structures.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union  
import json  
  
from REGISTRY.reg_12b_promotion_gates import PromotionDecision  
from REPORT.report_12a_release_manifest import ReleaseManifest  
from REPORT.report_12b_bundle_fingerprint import BundleFingerprint  
  
  
__all__ = [  
    "PromotionRecord",  
    "normalize_evidence_for_json",  
    "redact_evidence",  
    "build_promotion_record",  
    "promotion_record_to_json",  
    "render_promotion_record_markdown",  
    "write_text_file",  
    "write_promotion_record_json",  
    "write_promotion_record_markdown",  
]  
  
  
JsonScalar = Union[str, int, float, bool, None]  
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]  
  
  
@dataclass(frozen=True, slots=True)  
class PromotionRecord:  
    record_id: str  
    title: str  
    policy_id: str  
    from_env: str  
    to_env: str  
    decision: PromotionDecision  
    manifest: ReleaseManifest  
    fingerprint: BundleFingerprint  
    evidence: Dict[str, JsonValue]  
    redacted_keys: List[str]  
    notes: List[str]  
  
  
def _is_scalar(v: object) -> bool:  
    return v is None or isinstance(v, (str, int, float, bool))  
  
  
def _normalize_json_value(v: object) -> JsonValue:  
    """  
    Normalize arbitrary evidence into deterministic JSON-safe structures.  
  
    Allowed:  
    - None/bool/int/float/str  
    - list/tuple of allowed values (order preserved)  
    - dict with str keys and allowed values (keys sorted)  
    - set/frozenset of scalars (converted to sorted list of scalars)  
  
    Raises ValueError for unsupported types (to preserve determinism).  
    """  
    if _is_scalar(v):  
        return v  # type: ignore[return-value]  
  
    if isinstance(v, (list, tuple)):  
        return [_normalize_json_value(x) for x in v]  
  
    if isinstance(v, dict):  
        out: Dict[str, JsonValue] = {}  
        for k in sorted(v.keys(), key=lambda x: str(x)):  
            if not isinstance(k, str):  
                raise ValueError("Evidence dict keys must be strings")  
            out[k] = _normalize_json_value(v[k])  
        return out  
  
    if isinstance(v, (set, frozenset)):  
        # Only scalars are allowed in sets to keep stable sorting semantics.  
        vals = list(v)  
        for x in vals:  
            if not _is_scalar(x):  
                raise ValueError("Evidence set values must be JSON scalars")  
        # Sort by (type_name, string_value) to keep deterministic for mixed scalar types.  
        vals_sorted = sorted(vals, key=lambda x: (type(x).__name__, str(x)))  
        return [x for x in vals_sorted]  # type: ignore[list-item]  
  
    raise ValueError(f"Unsupported evidence value type: {type(v).__name__}")  
  
  
def normalize_evidence_for_json(evidence: Mapping[str, object]) -> Dict[str, JsonValue]:  
    """  
    Return a deterministic, JSON-safe dict:  
    - keys sorted  
    - values normalized recursively  
    """  
    out: Dict[str, JsonValue] = {}  
    for k in sorted(evidence.keys()):  
        if not isinstance(k, str):  
            raise ValueError("Evidence keys must be strings")  
        out[k] = _normalize_json_value(evidence[k])  
    return out  
  
  
def redact_evidence(  
    evidence: Mapping[str, object],  
    *,  
    redacted_keys: Sequence[str],  
    redaction_token: str = "***REDACTED***",  
) -> Tuple[Dict[str, object], List[str]]:  
    """  
    Redact specified keys. Returns (new_evidence, redacted_keys_sorted_present).  
    Redaction is applied before normalization.  
    """  
    redact_set = set(redacted_keys)  
    out: Dict[str, object] = {}  
    present_redacted: List[str] = []  
  
    for k in sorted(evidence.keys()):  
        v = evidence[k]  
        if k in redact_set:  
            out[k] = redaction_token  
            present_redacted.append(k)  
        else:  
            out[k] = v  
  
    return out, present_redacted  
  
  
def build_promotion_record(  
    *,  
    policy_id: str,  
    decision: PromotionDecision,  
    manifest: ReleaseManifest,  
    fingerprint: BundleFingerprint,  
    evidence: Mapping[str, object],  
    record_id: str = "PR-12C",  
    title: str = "Promotion Record",  
    redacted_keys: Optional[Sequence[str]] = None,  
    notes: Optional[Sequence[str]] = None,  
) -> PromotionRecord:  
    """  
    Build a deterministic promotion record. Caller supplies all inputs (including any timestamps externally).  
    """  
    n = list(notes) if notes is not None else [  
        "This record is deterministic and contains no generated timestamps.",  
        "Evidence is stored in a normalized JSON-safe form; secrets should be redacted by the caller.",  
    ]  
  
    rk = list(redacted_keys) if redacted_keys is not None else []  
    evidence_redacted, redacted_present = redact_evidence(evidence, redacted_keys=rk)  
    evidence_norm = normalize_evidence_for_json(evidence_redacted)  
  
    return PromotionRecord(  
        record_id=record_id,  
        title=title,  
        policy_id=policy_id,  
        from_env=decision.from_env,  
        to_env=decision.to_env,  
        decision=decision,  
        manifest=manifest,  
        fingerprint=fingerprint,  
        evidence=evidence_norm,  
        redacted_keys=sorted(redacted_present),  
        notes=n,  
    )  
  
  
def promotion_record_to_json(record: PromotionRecord) -> str:  
    payload: Dict[str, object] = {  
        "record_id": record.record_id,  
        "title": record.title,  
        "policy_id": record.policy_id,  
        "from_env": record.from_env,  
        "to_env": record.to_env,  
        "decision": {  
            "allowed": record.decision.allowed,  
            "from_env": record.decision.from_env,  
            "to_env": record.decision.to_env,  
            "failed_gates": list(record.decision.failed_gates),  
            "missing_evidence": list(record.decision.missing_evidence),  
            "details": list(record.decision.details),  
        },  
        "fingerprint": {  
            "fingerprint_id": record.fingerprint.fingerprint_id,  
            "algorithm": record.fingerprint.algorithm,  
            "fingerprint": record.fingerprint.fingerprint,  
            "input_canonical": record.fingerprint.input_canonical,  
            "notes": list(record.fingerprint.notes),  
        },  
        "manifest": {  
            "manifest_id": record.manifest.manifest_id,  
            "title": record.manifest.title,  
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
                for c in record.manifest.components  
            ],  
            "notes": list(record.manifest.notes),  
        },  
        "evidence": dict(record.evidence),  
        "redacted_keys": list(record.redacted_keys),  
        "notes": list(record.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_promotion_record_markdown(record: PromotionRecord) -> str:  
    lines: List[str] = []  
    lines.append(f"# { _md(record.title) }")  
    lines.append("")  
    lines.append(f"**Record ID:** { _md(record.record_id) }")  
    lines.append(f"**Policy ID:** { _md(record.policy_id) }")  
    lines.append(f"**Promotion:** { _md(record.from_env) } → { _md(record.to_env) }")  
    lines.append("")  
    lines.append(f"**Allowed:** `{record.decision.allowed}`")  
    lines.append("")  
    lines.append("## Bundle Fingerprint")  
    lines.append("")  
    lines.append(f"- **Algorithm:** { _md(record.fingerprint.algorithm) }")  
    lines.append(f"- **Fingerprint:** `{ _md(record.fingerprint.fingerprint) }`")  
    lines.append("")  
    lines.append("## Decision Details")  
    lines.append("")  
    if record.decision.failed_gates:  
        lines.append("- **Failed gates:** " + ", ".join([_md(x) for x in record.decision.failed_gates]))  
    else:  
        lines.append("- **Failed gates:** (none)")  
    if record.decision.missing_evidence:  
        lines.append("- **Missing evidence keys:** " + ", ".join([_md(x) for x in record.decision.missing_evidence]))  
    else:  
        lines.append("- **Missing evidence keys:** (none)")  
    lines.append("")  
    lines.append("### Gate Evaluation Log")  
    lines.append("")  
    for d in record.decision.details:  
        lines.append(f"- { _md(d) }")  
    lines.append("")  
    lines.append("## Manifest Summary")  
    lines.append("")  
    for c in record.manifest.components:  
        lines.append(f"- **{ _md(c.component_id) }**: { _md(c.version) }")  
    lines.append("")  
    lines.append("## Evidence (normalized)")  
    lines.append("")  
    if record.redacted_keys:  
        lines.append("- **Redacted keys:** " + ", ".join([_md(k) for k in record.redacted_keys]))  
        lines.append("")  
    lines.append("```json")  
    lines.append(json.dumps(record.evidence, indent=2, sort_keys=True))  
    lines.append("```")  
    lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in record.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_promotion_record_json(path: str, record: PromotionRecord) -> None:  
    write_text_file(path, promotion_record_to_json(record))  
  
  
def write_promotion_record_markdown(path: str, record: PromotionRecord) -> None:  
    write_text_file(path, render_promotion_record_markdown(record))  