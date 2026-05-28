"""  
STATE-1C — Retry / Resume helpers (additive to STATE-1B).  
  
Implements small helpers to:  
- read JSONL manifest rows robustly  
- extract de-duped failed IDs in stable order  
- write a minimal retry manifest (JSONL) containing only failed IDs in queued state  
  
This module does NOT modify or redefine STATE-1B behavior; it only reads/writes  
JSONL in a compatible, minimal shape.  
"""  
  
from __future__ import annotations  
  
import json  
from pathlib import Path  
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple, Union  
  
__all__ = ["read_manifest_rows", "extract_failed_ids", "write_retry_manifest"]  
  
  
def read_manifest_rows(path: Union[str, Path]) -> List[Dict[str, Any]]:  
    """  
    Load JSONL rows robustly.  
  
    - Ignores blank/whitespace-only lines.  
    - Raises ValueError on invalid JSON with line number and a short line preview.  
    """  
    p = Path(path)  
    rows: List[Dict[str, Any]] = []  
  
    if not p.exists():  
        raise FileNotFoundError(str(p))  
  
    with p.open("r", encoding="utf-8") as f:  
        for idx, raw in enumerate(f, start=1):  
            line = raw.strip()  
            if not line:  
                continue  
            try:  
                obj = json.loads(line)  
            except json.JSONDecodeError as e:  
                preview = (line[:160] + "...") if len(line) > 160 else line  
                raise ValueError(f"Invalid JSON in {p} at line {idx}: {e.msg}. Line: {preview!r}") from e  
  
            if not isinstance(obj, dict):  
                raise ValueError(f"Invalid row type in {p} at line {idx}: expected object/dict, got {type(obj).__name__}")  
            rows.append(obj)  
  
    return rows  
  
  
def _is_failed_row(row: Mapping[str, Any]) -> bool:  
    """  
    Determine if a row represents a failure.  
  
    Primary signal: row['status'] in {'fail','failed'}  
    Fallbacks: row['ok'] is False, or row['outcome'] indicates failure.  
    """  
    status = row.get("status")  
    if isinstance(status, str):  
        s = status.strip().lower()  
        if s in {"fail", "failed"}:  
            return True  
        if s in {"success", "succeeded", "queued", "skipped"}:  
            return False  
  
    ok = row.get("ok")  
    if ok is False:  
        return True  
  
    outcome = row.get("outcome")  
    if isinstance(outcome, str) and outcome.strip().lower() in {"fail", "failed", "error"}:  
        return True  
  
    return False  
  
  
def extract_failed_ids(  
    rows: Sequence[Mapping[str, Any]],  
    id_field_candidates: Tuple[str, ...] = ("ACCOUNT_ID", "LOCATION_ID", "ID", "key_ID"),  
) -> List[str]:  
    """  
    Return de-duped failed IDs in stable order.  
  
    For each failed row, the first present candidate key is used. Values are  
    coerced to str and stripped; empty IDs are ignored.  
    """  
    seen = set()  
    out: List[str] = []  
  
    for row in rows:  
        if not _is_failed_row(row):  
            continue  
  
        found: Any = None  
        for k in id_field_candidates:  
            if k in row and row.get(k) is not None:  
                found = row.get(k)  
                break  
  
        if found is None:  
            continue  
  
        s = str(found).strip()  
        if not s:  
            continue  
        if s in seen:  
            continue  
  
        seen.add(s)  
        out.append(s)  
  
    return out  
  
  
def write_retry_manifest(path: Union[str, Path], ids: Iterable[str], *, id_field: str = "ACCOUNT_ID") -> Path:  
    """  
    Write a minimal JSONL manifest containing only the failed IDs in a queued state.  
  
    Each line:  
      {"<id_field>": "<id>", "status": "queued"}  
  
    Returns the output Path.  
    """  
    p = Path(path)  
    p.parent.mkdir(parents=True, exist_ok=True)  
  
    # De-dupe while preserving order (in case caller passes duplicates).  
    seen = set()  
    ordered: List[str] = []  
    for v in ids:  
        s = str(v).strip()  
        if not s or s in seen:  
            continue  
        seen.add(s)  
        ordered.append(s)  
  
    with p.open("w", encoding="utf-8", newline="\n") as f:  
        for s in ordered:  
            row = {id_field: s, "status": "queued"}  
            f.write(json.dumps(row, ensure_ascii=False) + "\n")  
  
    return p  