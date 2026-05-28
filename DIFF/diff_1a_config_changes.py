# DIFF/diff_1a_config_changes.py  
"""  
DIFF-1A — Workflow & Selector Change Diff + Version Stamp  
  
Deterministic change-tracking utilities:  
- compute stable fingerprints (hashes) for workflows + selectors + schema  
- diff two fingerprints  
- write fingerprint + diff reports (JSON + MD)  
  
No Selenium.  
"""  
  
from __future__ import annotations  
  
import hashlib  
import json  
from dataclasses import dataclass  
from datetime import datetime, timezone  
from pathlib import Path  
from typing import Any, Dict, List, Optional, Tuple  
  
__all__ = [  
    "compute_fingerprint",  
    "write_fingerprint",  
    "diff_fingerprints",  
    "write_diff_report",  
]  
  
  
def _utc_now_iso() -> str:  
    return datetime.now(timezone.utc).isoformat()  
  
  
def _sha256_bytes(b: bytes) -> str:  
    h = hashlib.sha256()  
    h.update(b)  
    return h.hexdigest()  
  
  
def _sha256_text(s: str) -> str:  
    return _sha256_bytes(s.encode("utf-8"))  
  
  
def _read_bytes(p: Path) -> bytes:  
    return p.read_bytes()  
  
  
def _normalize_json_bytes(raw: bytes) -> Optional[bytes]:  
    """  
    Parse JSON and re-dump with sorted keys to normalize content before hashing.  
    Returns normalized bytes, or None if parsing fails.  
    """  
    try:  
        obj = json.loads(raw.decode("utf-8"))  
        norm = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))  
        return norm.encode("utf-8")  
    except Exception:  
        return None  
  
  
def _file_hash(p: Path) -> str:  
    raw = _read_bytes(p)  
    if p.suffix.lower() == ".json":  
        norm = _normalize_json_bytes(raw)  
        if norm is not None:  
            return _sha256_bytes(norm)  
    return _sha256_bytes(raw)  
  
  
def _relpath_posix(p: Path, root: Path) -> str:  
    try:  
        return p.resolve().relative_to(root.resolve()).as_posix()  
    except Exception:  
        return p.as_posix()  
  
  
def _list_files(base: Path) -> List[Path]:  
    if not base.exists():  
        return []  
    if base.is_file():  
        return [base]  
    files = [p for p in base.rglob("*") if p.is_file()]  
    return sorted(files, key=lambda x: x.as_posix().lower())  
  
  
def _aggregate_hash(items: List[Tuple[str, str]]) -> str:  
    """  
    items: list of (relative_path, file_hash)  
    Deterministic aggregate: sha256 over sorted lines.  
    """  
    lines = [f"{path}\t{h}" for path, h in sorted(items, key=lambda t: t[0].lower())]  
    return _sha256_text("\n".join(lines) + ("\n" if lines else ""))  
  
  
def _safe_stat(p: Path) -> dict:  
    try:  
        st = p.stat()  
        return {"size": int(st.st_size), "mtime": float(st.st_mtime)}  
    except Exception:  
        return {"size": None, "mtime": None}  
  
  
def compute_fingerprint(  
    *,  
    root: str | Path = ".",  
    workflows_dir: str | Path = "workflows",  
    selectors_path: str | Path = "data/selectors.json",  
    schema_dir: str | Path = "SCHEMA",  
) -> dict:  
    rootp = Path(root)  
    wf_base = (rootp / workflows_dir).resolve()  
    sel_path = (rootp / selectors_path).resolve()  
    schema_base = (rootp / schema_dir).resolve()  
  
    # Workflows  
    wf_files = _list_files(wf_base)  
    wf_entries: List[dict] = []  
    wf_items: List[Tuple[str, str]] = []  
    for p in wf_files:  
        rel = _relpath_posix(p, rootp)  
        h = _file_hash(p)  
        meta = _safe_stat(p)  
        wf_entries.append({"path": rel, "hash": h, **meta})  
        wf_items.append((rel, h))  
    wf_agg = _aggregate_hash(wf_items)  
  
    # Selectors (single file)  
    selectors_obj: dict  
    if sel_path.exists() and sel_path.is_file():  
        sel_hash = _file_hash(sel_path)  
        sel_meta = _safe_stat(sel_path)  
        selectors_obj = {"path": _relpath_posix(sel_path, rootp), "hash": sel_hash, **sel_meta}  
    else:  
        selectors_obj = {"path": _relpath_posix(sel_path, rootp), "hash": None, "size": None, "mtime": None}  
  
    # Schema  
    schema_files = _list_files(schema_base)  
    schema_entries: List[dict] = []  
    schema_items: List[Tuple[str, str]] = []  
    for p in schema_files:  
        rel = _relpath_posix(p, rootp)  
        h = _file_hash(p)  
        meta = _safe_stat(p)  
        schema_entries.append({"path": rel, "hash": h, **meta})  
        schema_items.append((rel, h))  
    schema_agg = _aggregate_hash(schema_items)  
  
    overall_parts = [  
        ("workflows.aggregate_hash", wf_agg),  
        ("selectors.hash", selectors_obj.get("hash") or ""),  
        ("schema.aggregate_hash", schema_agg),  
    ]  
    overall_hash = _aggregate_hash(overall_parts)  
  
    return {  
        "generated_at": _utc_now_iso(),  
        "workflows": {"files": wf_entries, "aggregate_hash": wf_agg},  
        "selectors": selectors_obj,  
        "schema": {"files": schema_entries, "aggregate_hash": schema_agg},  
        "overall_hash": overall_hash,  
    }  
  
  
def write_fingerprint(  
    fp: dict,  
    *,  
    out_dir: str | Path = "reports",  
    name: str = "fingerprint",  
) -> Path:  
    outp = Path(out_dir)  
    outp.mkdir(parents=True, exist_ok=True)  
    path = outp / f"{name}.json"  
    path.write_text(json.dumps(fp, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")  
    return path  
  
  
def _index_by_path(files: List[dict]) -> Dict[str, dict]:  
    out: Dict[str, dict] = {}  
    for f in files:  
        if isinstance(f, dict) and isinstance(f.get("path"), str):  
            out[f["path"]] = f  
    return out  
  
  
def _diff_file_sets(a_files: List[dict], b_files: List[dict]) -> dict:  
    a_idx = _index_by_path(a_files or [])  
    b_idx = _index_by_path(b_files or [])  
  
    a_paths = set(a_idx.keys())  
    b_paths = set(b_idx.keys())  
  
    added = sorted(list(b_paths - a_paths))  
    removed = sorted(list(a_paths - b_paths))  
  
    changed: List[dict] = []  
    unchanged: List[str] = []  
  
    for p in sorted(list(a_paths & b_paths)):  
        ah = a_idx[p].get("hash")  
        bh = b_idx[p].get("hash")  
        if ah != bh:  
            changed.append({"path": p, "a_hash": ah, "b_hash": bh})  
        else:  
            unchanged.append(p)  
  
    return {  
        "added": [{"path": p, "b_hash": b_idx[p].get("hash")} for p in added],  
        "removed": [{"path": p, "a_hash": a_idx[p].get("hash")} for p in removed],  
        "changed": changed,  
        "unchanged": unchanged,  
        "counts": {  
            "added": len(added),  
            "removed": len(removed),  
            "changed": len(changed),  
            "unchanged": len(unchanged),  
        },  
    }  
  
  
def diff_fingerprints(a: dict, b: dict) -> dict:  
    a_wf = (a or {}).get("workflows") or {}  
    b_wf = (b or {}).get("workflows") or {}  
    a_schema = (a or {}).get("schema") or {}  
    b_schema = (b or {}).get("schema") or {}  
  
    wf_diff = _diff_file_sets(a_wf.get("files") or [], b_wf.get("files") or [])  
    schema_diff = _diff_file_sets(a_schema.get("files") or [], b_schema.get("files") or [])  
  
    a_sel = (a or {}).get("selectors") or {}  
    b_sel = (b or {}).get("selectors") or {}  
    a_sel_hash = a_sel.get("hash")  
    b_sel_hash = b_sel.get("hash")  
    selectors_changed = a_sel_hash != b_sel_hash  
  
    overall_changed = (a or {}).get("overall_hash") != (b or {}).get("overall_hash")  
  
    return {  
        "generated_at": _utc_now_iso(),  
        "overall": {  
            "changed": bool(overall_changed),  
            "a_hash": (a or {}).get("overall_hash"),  
            "b_hash": (b or {}).get("overall_hash"),  
        },  
        "workflows": {  
            "aggregate_changed": a_wf.get("aggregate_hash") != b_wf.get("aggregate_hash"),  
            "a_aggregate_hash": a_wf.get("aggregate_hash"),  
            "b_aggregate_hash": b_wf.get("aggregate_hash"),  
            **wf_diff,  
        },  
        "selectors": {  
            "changed": bool(selectors_changed),  
            "a_path": a_sel.get("path"),  
            "b_path": b_sel.get("path"),  
            "a_hash": a_sel_hash,  
            "b_hash": b_sel_hash,  
        },  
        "schema": {  
            "aggregate_changed": a_schema.get("aggregate_hash") != b_schema.get("aggregate_hash"),  
            "a_aggregate_hash": a_schema.get("aggregate_hash"),  
            "b_aggregate_hash": b_schema.get("aggregate_hash"),  
            **schema_diff,  
        },  
        "agent_summary": {  
            "workflow_files_changed": int((wf_diff.get("counts") or {}).get("changed", 0)),  
            "workflow_files_added": int((wf_diff.get("counts") or {}).get("added", 0)),  
            "workflow_files_removed": int((wf_diff.get("counts") or {}).get("removed", 0)),  
            "selectors_changed": bool(selectors_changed),  
            "schema_files_changed": int((schema_diff.get("counts") or {}).get("changed", 0)),  
            "schema_files_added": int((schema_diff.get("counts") or {}).get("added", 0)),  
            "schema_files_removed": int((schema_diff.get("counts") or {}).get("removed", 0)),  
        },  
    }  
  
  
def write_diff_report(  
    diff: dict,  
    *,  
    out_dir: str | Path = "reports",  
    name: str = "diff",  
) -> dict:  
    outp = Path(out_dir)  
    outp.mkdir(parents=True, exist_ok=True)  
  
    json_path = outp / f"{name}.json"  
    md_path = outp / f"{name}.md"  
  
    json_path.write_text(json.dumps(diff, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")  
  
    # Markdown (human friendly)  
    o = diff.get("overall") if isinstance(diff, dict) else {}  
    wf = diff.get("workflows") if isinstance(diff, dict) else {}  
    sel = diff.get("selectors") if isinstance(diff, dict) else {}  
    sch = diff.get("schema") if isinstance(diff, dict) else {}  
  
    def _md_list(entries: List[dict], label_hash: str) -> str:  
        if not entries:  
            return "- (none)\n"  
        lines = []  
        for e in entries:  
            p = e.get("path")  
            h = e.get(label_hash)  
            lines.append(f"- `{p}` — `{h}`")  
        return "\n".join(lines) + "\n"  
  
    md = []  
    md.append(f"# Config Diff Report — {name}\n")  
    md.append(f"- Generated at (UTC): `{diff.get('generated_at')}`")  
    md.append(f"- Overall changed: `{o.get('changed')}`")  
    md.append(f"- A overall hash: `{o.get('a_hash')}`")  
    md.append(f"- B overall hash: `{o.get('b_hash')}`\n")  
  
    md.append("## Workflows\n")  
    md.append(f"- Aggregate changed: `{wf.get('aggregate_changed')}`")  
    md.append(f"- A aggregate: `{wf.get('a_aggregate_hash')}`")  
    md.append(f"- B aggregate: `{wf.get('b_aggregate_hash')}`\n")  
  
    md.append("### Added workflows\n")  
    md.append(_md_list(wf.get("added") or [], "b_hash"))  
    md.append("### Removed workflows\n")  
    md.append(_md_list(wf.get("removed") or [], "a_hash"))  
    md.append("### Changed workflows\n")  
    if wf.get("changed"):  
        for e in wf["changed"]:  
            md.append(f"- `{e.get('path')}`")  
            md.append(f"  - a: `{e.get('a_hash')}`")  
            md.append(f"  - b: `{e.get('b_hash')}`")  
        md.append("")  
    else:  
        md.append("- (none)\n")  
  
    md.append("## Selectors\n")  
    md.append(f"- Changed: `{sel.get('changed')}`")  
    md.append(f"- A: `{sel.get('a_path')}` — `{sel.get('a_hash')}`")  
    md.append(f"- B: `{sel.get('b_path')}` — `{sel.get('b_hash')}`\n")  
  
    md.append("## Schema\n")  
    md.append(f"- Aggregate changed: `{sch.get('aggregate_changed')}`")  
    md.append(f"- A aggregate: `{sch.get('a_aggregate_hash')}`")  
    md.append(f"- B aggregate: `{sch.get('b_aggregate_hash')}`\n")  
  
    md.append("### Added schema files\n")  
    md.append(_md_list(sch.get("added") or [], "b_hash"))  
    md.append("### Removed schema files\n")  
    md.append(_md_list(sch.get("removed") or [], "a_hash"))  
    md.append("### Changed schema files\n")  
    if sch.get("changed"):  
        for e in sch["changed"]:  
            md.append(f"- `{e.get('path')}`")  
            md.append(f"  - a: `{e.get('a_hash')}`")  
            md.append(f"  - b: `{e.get('b_hash')}`")  
        md.append("")  
    else:  
        md.append("- (none)\n")  
  
    md_path.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")  
  
    return {"json": str(json_path), "md": str(md_path)}  