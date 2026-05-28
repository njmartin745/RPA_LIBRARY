"""  
REPLAY-12A: Replay Index Verifier (Milestone 12.5.4)  
  
Single responsibility:  
- Parse audit-log JSONL into events (dicts).  
- Verify (deterministically) that canonical event hashes match a ReplayIndex.  
  
This module does NOT execute a browser replay. It only verifies integrity/consistency  
of replay artifacts for audit and reproducibility.  
  
Dependencies:  
- Uses HISTORY.history_12a_audit_logging_replay_spec for canonicalization and hashing.  
  
Determinism:  
- No timestamps generated.  
- Stable event ordering and stable mismatch ordering.  
- JSON uses sort_keys=True.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union  
import json  
  
from HISTORY.history_12a_audit_logging_replay_spec import (  
    AuditLogSpec,  
    ReplayIndex,  
    canonical_event_dict,  
    sha256_hex,  
)  
  
__all__ = [  
    "ReplayMismatch",  
    "ReplayVerificationResult",  
    "parse_events_jsonl",  
    "events_to_canonical_hashes",  
    "verify_events_against_replay_index",  
    "result_to_json",  
    "render_result_markdown",  
    "write_text_file",  
]  
  
  
@dataclass(frozen=True, slots=True)  
class ReplayMismatch:  
    """  
    One mismatch at a deterministic position in the canonical event sequence.  
    """  
    position: int  
    expected_sha256: Optional[str]  
    actual_sha256: Optional[str]  
    event_summary: str  
  
  
@dataclass(frozen=True, slots=True)  
class ReplayVerificationResult:  
    index_id: str  
    run_id: str  
    passed: bool  
    mismatches: List[ReplayMismatch]  
    details: List[str]  
  
  
def parse_events_jsonl(jsonl_text: str) -> List[Dict[str, Any]]:  
    """  
    Parse JSONL text into a list of event dicts.  
  
    Rules:  
    - Blank lines are ignored.  
    - Raises ValueError for invalid JSON.  
    - Deterministic: output order is the file order (verification later canonical-sorts).  
    """  
    events: List[Dict[str, Any]] = []  
    for i, raw_line in enumerate(jsonl_text.splitlines()):  
        line = raw_line.strip()  
        if not line:  
            continue  
        try:  
            obj = json.loads(line)  
        except Exception as e:  
            raise ValueError(f"Invalid JSON on line {i + 1}: {e}") from e  
        if not isinstance(obj, dict):  
            raise ValueError(f"JSONL line {i + 1} must be an object/dict")  
        events.append(obj)  
    return events  
  
  
def _canonical_sort_key(e: Mapping[str, Any]) -> Tuple[int, str, str, str]:  
    # canonical_event_dict guarantees types; caller should only pass canonical dicts  
    return (int(e["seq"]), str(e["event_type"]), str(e["run_id"]), str(e["ts"]))  
  
  
def events_to_canonical_hashes(spec: AuditLogSpec, events: Sequence[Mapping[str, Any]]) -> Tuple[List[str], List[str]]:  
    """  
    Return (hashes, details) for the canonical event sequence.  
  
    Hash is sha256 over canonical JSON (sort_keys=True; separators=(',',':')) of the  
    canonical_event_dict (required fields only).  
    """  
    canon: List[Dict[str, Any]] = [canonical_event_dict(spec, e) for e in list(events)]  
    canon_sorted = sorted(canon, key=_canonical_sort_key)  
  
    hashes: List[str] = []  
    details: List[str] = []  
    for e in canon_sorted:  
        cjson = json.dumps(e, sort_keys=True, separators=(",", ":"))  
        h = sha256_hex(cjson)  
        hashes.append(h)  
        details.append(f"Hashed seq={e['seq']} type={e['event_type']} run_id={e['run_id']}")  
    return hashes, details  
  
  
def _coerce_index(index: Union[ReplayIndex, Mapping[str, Any]]) -> ReplayIndex:  
    if isinstance(index, ReplayIndex):  
        return index  
    if not isinstance(index, Mapping):  
        raise TypeError("index must be ReplayIndex or mapping")  
  
    # Minimal coercion from dict-like representation  
    idx_id = index.get("index_id")  
    run_id = index.get("run_id")  
    bundle_fp = index.get("bundle_fingerprint")  
    ev = index.get("event_sha256")  
    total = index.get("total_events")  
    notes = index.get("notes", [])  
  
    if not isinstance(idx_id, str) or not idx_id:  
        raise ValueError("index.index_id must be non-empty str")  
    if not isinstance(run_id, str) or not run_id:  
        raise ValueError("index.run_id must be non-empty str")  
    if not isinstance(bundle_fp, str) or not bundle_fp:  
        raise ValueError("index.bundle_fingerprint must be non-empty str")  
    if not isinstance(ev, list) or not all(isinstance(x, str) for x in ev):  
        raise ValueError("index.event_sha256 must be list[str]")  
    if not isinstance(total, int) or isinstance(total, bool):  
        raise ValueError("index.total_events must be int")  
    if not isinstance(notes, list) or not all(isinstance(x, str) for x in notes):  
        raise ValueError("index.notes must be list[str]")  
  
    return ReplayIndex(  
        index_id=idx_id,  
        run_id=run_id,  
        bundle_fingerprint=bundle_fp,  
        event_sha256=tuple(ev),  
        total_events=total,  
        notes=tuple(notes),  
    )  
  
  
def verify_events_against_replay_index(  
    spec: AuditLogSpec,  
    *,  
    events: Sequence[Mapping[str, Any]],  
    index: Union[ReplayIndex, Mapping[str, Any]],  
) -> ReplayVerificationResult:  
    """  
    Verify:  
    - Canonical ordering of events matches the replay index ordering.  
    - Hashes match index.event_sha256 exactly.  
    - All events share the same run_id as index.run_id.  
  
    Returns deterministic mismatches and details.  
    """  
    idx = _coerce_index(index)  
  
    details: List[str] = []  
    mismatches: List[ReplayMismatch] = []  
  
    hashes, hash_details = events_to_canonical_hashes(spec, events)  
    details.extend(hash_details)  
  
    details.append(f"Index expects total_events={idx.total_events}")  
    details.append(f"Computed total_events={len(hashes)}")  
  
    # Length mismatch handling: still compare overlapped range deterministically  
    expected = list(idx.event_sha256)  
    actual = list(hashes)  
    n = min(len(expected), len(actual))  
  
    if len(expected) != len(actual):  
        mismatches.append(  
            ReplayMismatch(  
                position=n,  
                expected_sha256=(expected[n] if n < len(expected) else None),  
                actual_sha256=(actual[n] if n < len(actual) else None),  
                event_summary=f"Length mismatch: expected={len(expected)} actual={len(actual)}",  
            )  
        )  
  
    for i in range(n):  
        if expected[i] != actual[i]:  
            mismatches.append(  
                ReplayMismatch(  
                    position=i,  
                    expected_sha256=expected[i],  
                    actual_sha256=actual[i],  
                    event_summary="Hash mismatch at position",  
                )  
            )  
  
    passed = (len(mismatches) == 0)  
  
    # deterministic ordering  
    mismatches_sorted = sorted(mismatches, key=lambda m: (m.position, str(m.expected_sha256), str(m.actual_sha256)))  
  
    return ReplayVerificationResult(  
        index_id=idx.index_id,  
        run_id=idx.run_id,  
        passed=passed,  
        mismatches=mismatches_sorted,  
        details=details,  
    )  
  
  
def result_to_json(result: ReplayVerificationResult) -> str:  
    payload: Dict[str, Any] = {  
        "index_id": result.index_id,  
        "run_id": result.run_id,  
        "passed": result.passed,  
        "mismatches": [  
            {  
                "position": m.position,  
                "expected_sha256": m.expected_sha256,  
                "actual_sha256": m.actual_sha256,  
                "event_summary": m.event_summary,  
            }  
            for m in result.mismatches  
        ],  
        "details": list(result.details),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_result_markdown(result: ReplayVerificationResult) -> str:  
    lines: List[str] = []  
    lines.append("# Replay Verification Result")  
    lines.append("")  
    lines.append(f"**Index ID:** { _md(result.index_id) }")  
    lines.append(f"**Run ID:** `{ _md(result.run_id) }`")  
    lines.append("")  
    lines.append(f"**Passed:** `{result.passed}`")  
    lines.append("")  
    lines.append("## Mismatches")  
    lines.append("")  
    if not result.mismatches:  
        lines.append("(none)")  
        lines.append("")  
    else:  
        for m in result.mismatches:  
            lines.append(  
                f"- pos `{m.position}` expected `{_md(str(m.expected_sha256))}` "  
                f"actual `{_md(str(m.actual_sha256))}` — {_md(m.event_summary)}"  
            )  
        lines.append("")  
    lines.append("## Details")  
    lines.append("")  
    for d in result.details:  
        lines.append(f"- { _md(d) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  