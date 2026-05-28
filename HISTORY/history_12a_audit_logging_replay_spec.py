"""  
HISTORY-12A: Audit-Friendly Logging + Replay Spec (Milestone 12.5.3)  
  
Single responsibility:  
- Define a canonical, deterministic spec for audit logs and replay index artifacts.  
- Provide pure validators for events/index.  
- Provide deterministic renderers (Markdown/JSON) and deterministic JSONL serialization.  
- Provide deterministic SHA256 hashing of canonical event JSON.  
  
Determinism:  
- No timestamps generated (timestamps, if present, are caller-supplied strings).  
- Stable ordering for rendering/serialization (sort by seq then event_type then run_id).  
- JSON uses sort_keys=True.  
  
This module does NOT write runtime logs automatically and does NOT perform replay.  
It defines a stable, audit-friendly structure that other layers can emit/consume.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple  
import hashlib  
import json  
  
  
__all__ = [  
    "AuditLogSpec",  
    "AuditEvent",  
    "ReplayIndex",  
    "get_audit_log_spec",  
    "validate_audit_event",  
    "validate_replay_index",  
    "canonical_event_dict",  
    "event_to_canonical_json",  
    "events_to_jsonl",  
    "sha256_hex",  
    "build_replay_index",  
    "spec_to_json",  
    "render_spec_markdown",  
    "replay_index_to_json",  
    "render_replay_index_markdown",  
    "write_text_file",  
    "write_jsonl_file",  
]  
  
  
@dataclass(frozen=True, slots=True)  
class AuditLogSpec:  
    spec_id: str  
    title: str  
    allowed_event_types: Tuple[str, ...]  
    required_fields: Tuple[str, ...]  
    notes: Tuple[str, ...]  
  
  
@dataclass(frozen=True, slots=True)  
class AuditEvent:  
    """  
    Canonical event container.  
  
    ts is a caller-supplied string (e.g., ISO-8601). This module does not validate  
    timestamps beyond being a non-empty string (to keep deterministic + dependency-free).  
    """  
    seq: int  
    run_id: str  
    event_type: str  
    ts: str  
    data: Dict[str, Any]  
  
  
@dataclass(frozen=True, slots=True)  
class ReplayIndex:  
    """  
    Replay index ties a run_id to:  
      - bundle_fingerprint (immutable build identity)  
      - ordered event hashes (sha256 of canonical event JSON)  
    """  
    index_id: str  
    run_id: str  
    bundle_fingerprint: str  
    event_sha256: Tuple[str, ...]  
    total_events: int  
    notes: Tuple[str, ...]  
  
  
def get_audit_log_spec(  
    *,  
    spec_id: str = "AUDIT-LOG-SPEC-12A",  
    title: str = "Audit-Friendly Logging + Replay Spec",  
    notes: Optional[Sequence[str]] = None,  
) -> AuditLogSpec:  
    n = tuple(notes) if notes is not None else (  
        "This spec is deterministic and contains no generated timestamps.",  
        "Events are intended to be written as JSON Lines (JSONL): one event per line.",  
        "A replay index can reference a versioned bundle fingerprint and a stable list of event hashes.",  
    )  
    allowed = (  
        "run_started",  
        "doctor_decision",  
        "guard_decision",  
        "step_started",  
        "step_completed",  
        "artifact_written",  
        "run_completed",  
        "error",  
    )  
    required = ("seq", "run_id", "event_type", "ts", "data")  
    return AuditLogSpec(  
        spec_id=spec_id,  
        title=title,  
        allowed_event_types=allowed,  
        required_fields=required,  
        notes=n,  
    )  
  
  
def validate_audit_event(spec: AuditLogSpec, event: Mapping[str, Any]) -> List[str]:  
    """  
    Pure validation. Returns list of errors (empty => valid).  
    """  
    errs: List[str] = []  
    for k in spec.required_fields:  
        if k not in event:  
            errs.append(f"Missing required field: {k}")  
  
    seq = event.get("seq")  
    if not isinstance(seq, int) or isinstance(seq, bool):  
        errs.append("Field 'seq' must be int")  
    elif seq < 0:  
        errs.append("Field 'seq' must be >= 0")  
  
    run_id = event.get("run_id")  
    if not isinstance(run_id, str) or not run_id:  
        errs.append("Field 'run_id' must be non-empty str")  
  
    et = event.get("event_type")  
    if not isinstance(et, str) or not et:  
        errs.append("Field 'event_type' must be non-empty str")  
    elif et not in set(spec.allowed_event_types):  
        errs.append(f"Field 'event_type' not allowed: {et!r}")  
  
    ts = event.get("ts")  
    if not isinstance(ts, str) or not ts:  
        errs.append("Field 'ts' must be non-empty str")  
  
    data = event.get("data")  
    if not isinstance(data, dict):  
        errs.append("Field 'data' must be dict/object")  
  
    return errs  
  
  
def canonical_event_dict(spec: AuditLogSpec, event: Mapping[str, Any]) -> Dict[str, Any]:  
    """  
    Produce a canonical dict with only the required fields, stable types, and stable key presence.  
    Raises ValueError if invalid.  
    """  
    errs = validate_audit_event(spec, event)  
    if errs:  
        raise ValueError("; ".join(errs))  
  
    # Keep only the required fields to make hashes stable and avoid incidental noise.  
    # (callers should store extra info inside data if needed)  
    return {  
        "seq": int(event["seq"]),  
        "run_id": str(event["run_id"]),  
        "event_type": str(event["event_type"]),  
        "ts": str(event["ts"]),  
        "data": dict(event["data"]),  
    }  
  
  
def event_to_canonical_json(spec: AuditLogSpec, event: Mapping[str, Any]) -> str:  
    """  
    Deterministic canonical JSON (no indent; stable keys).  
    """  
    payload = canonical_event_dict(spec, event)  
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))  
  
  
def sha256_hex(text: str) -> str:  
    h = hashlib.sha256()  
    h.update(text.encode("utf-8"))  
    return h.hexdigest()  
  
  
def _sorted_events(spec: AuditLogSpec, events: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:  
    canon: List[Dict[str, Any]] = [canonical_event_dict(spec, e) for e in list(events)]  
    return sorted(canon, key=lambda e: (e["seq"], e["event_type"], e["run_id"], e["ts"]))  
  
  
def events_to_jsonl(spec: AuditLogSpec, events: Sequence[Mapping[str, Any]]) -> str:  
    """  
    Deterministic JSONL serialization. Events are sorted by:  
      seq, event_type, run_id, ts  
    """  
    lines: List[str] = []  
    for e in _sorted_events(spec, events):  
        lines.append(json.dumps(e, sort_keys=True, separators=(",", ":")))  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def build_replay_index(  
    spec: AuditLogSpec,  
    *,  
    run_id: str,  
    bundle_fingerprint: str,  
    events: Sequence[Mapping[str, Any]],  
    index_id: str = "REPLAY-INDEX-12A",  
    notes: Optional[Sequence[str]] = None,  
) -> ReplayIndex:  
    """  
    Build a deterministic replay index from events.  
    """  
    if not isinstance(run_id, str) or not run_id:  
        raise ValueError("run_id must be non-empty str")  
    if not isinstance(bundle_fingerprint, str) or not bundle_fingerprint:  
        raise ValueError("bundle_fingerprint must be non-empty str")  
  
    n = tuple(notes) if notes is not None else (  
        "event_sha256 is computed from canonical event JSON (sort_keys=True; separators=(',',':')).",  
        "Events are ordered by (seq, event_type, run_id, ts) before hashing.",  
    )  
  
    sorted_events = _sorted_events(spec, events)  
    hashes: List[str] = []  
    for e in sorted_events:  
        # enforce run_id consistency by policy (audit-friendly)  
        if e["run_id"] != run_id:  
            raise ValueError(f"Event run_id mismatch: expected {run_id!r}, got {e['run_id']!r}")  
        hashes.append(sha256_hex(json.dumps(e, sort_keys=True, separators=(",", ":"))))  
  
    return ReplayIndex(  
        index_id=index_id,  
        run_id=run_id,  
        bundle_fingerprint=bundle_fingerprint,  
        event_sha256=tuple(hashes),  
        total_events=len(hashes),  
        notes=n,  
    )  
  
  
def validate_replay_index(index: ReplayIndex) -> List[str]:  
    errs: List[str] = []  
    if not index.index_id:  
        errs.append("index_id is required")  
    if not index.run_id:  
        errs.append("run_id is required")  
    if not index.bundle_fingerprint:  
        errs.append("bundle_fingerprint is required")  
    if index.total_events != len(index.event_sha256):  
        errs.append("total_events does not match length of event_sha256")  
    for h in index.event_sha256:  
        if not isinstance(h, str) or len(h) != 64:  
            errs.append(f"Invalid sha256 hex: {h!r}")  
            break  
    return errs  
  
  
def spec_to_json(spec: AuditLogSpec) -> str:  
    payload: Dict[str, Any] = {  
        "spec_id": spec.spec_id,  
        "title": spec.title,  
        "allowed_event_types": list(spec.allowed_event_types),  
        "required_fields": list(spec.required_fields),  
        "notes": list(spec.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_spec_markdown(spec: AuditLogSpec) -> str:  
    lines: List[str] = []  
    lines.append(f"# { _md(spec.title) }")  
    lines.append("")  
    lines.append(f"**Spec ID:** { _md(spec.spec_id) }")  
    lines.append("")  
    lines.append("## Allowed event types")  
    lines.append("")  
    for t in spec.allowed_event_types:  
        lines.append(f"- `{_md(t)}`")  
    lines.append("")  
    lines.append("## Required fields")  
    lines.append("")  
    for f in spec.required_fields:  
        lines.append(f"- `{_md(f)}`")  
    lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in spec.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def replay_index_to_json(index: ReplayIndex) -> str:  
    payload: Dict[str, Any] = {  
        "index_id": index.index_id,  
        "run_id": index.run_id,  
        "bundle_fingerprint": index.bundle_fingerprint,  
        "event_sha256": list(index.event_sha256),  
        "total_events": index.total_events,  
        "notes": list(index.notes),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def render_replay_index_markdown(index: ReplayIndex) -> str:  
    lines: List[str] = []  
    lines.append("# Replay Index")  
    lines.append("")  
    lines.append(f"**Index ID:** { _md(index.index_id) }")  
    lines.append(f"**Run ID:** `{ _md(index.run_id) }`")  
    lines.append(f"**Bundle fingerprint:** `{ _md(index.bundle_fingerprint) }`")  
    lines.append(f"**Total events:** `{ index.total_events }`")  
    lines.append("")  
    lines.append("## Event hashes (sha256)")  
    lines.append("")  
    if not index.event_sha256:  
        lines.append("(none)")  
        lines.append("")  
    else:  
        for h in index.event_sha256:  
            lines.append(f"- `{h}`")  
        lines.append("")  
    lines.append("## Notes")  
    lines.append("")  
    for n in index.notes:  
        lines.append(f"- { _md(n) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_jsonl_file(path: str, content_jsonl: str) -> None:  
    # JSONL is plain text; keep newline normalization deterministic  
    write_text_file(path, content_jsonl)  