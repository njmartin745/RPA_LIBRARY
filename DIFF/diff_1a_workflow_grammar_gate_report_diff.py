"""  
DIFF-1A: Workflow grammar gate report diff.  
  
Single responsibility:  
- Compute a deterministic structured diff between two workflow-grammar-gate  
  report dicts (as produced by REPORT/PIPE/DOCTOR layers).  
"""  
  
from __future__ import annotations  
  
from typing import Any, Dict, Iterable, List, Mapping, Tuple  
  
__all__ = [  
    "DIFF_SCHEMA_ID",  
    "diff_workflow_grammar_gate_reports",  
]  
  
DIFF_SCHEMA_ID = "DIFF-1A.workflow_grammar_gate_report"  
  
  
def _as_list(x: Any) -> List[Any]:  
    if x is None:  
        return []  
    if isinstance(x, list):  
        return x  
    return []  
  
  
def _extract_files_list(report: Mapping[str, Any]) -> List[Mapping[str, Any]]:  
    """  
    Best-effort extraction of the per-file list from a report dict.  
    Supports common keys without assuming a single schema layout.  
    """  
    for k in ("files", "items", "results", "workflows"):  
        v = report.get(k)  
        if isinstance(v, list) and all(isinstance(i, dict) for i in v):  
            return v  # type: ignore[return-value]  
    return []  
  
  
def _file_path(item: Mapping[str, Any]) -> str:  
    for k in ("path", "file", "rel_path", "workflow_path"):  
        v = item.get(k)  
        if isinstance(v, str) and v:  
            return v  
    return ""  
  
  
def _violation_count(item: Mapping[str, Any]) -> int:  
    """  
    Best-effort extraction of violation count from a per-file item.  
    """  
    for k in ("violation_count", "violations_count", "n_violations", "count"):  
        v = item.get(k)  
        if isinstance(v, int):  
            return int(v)  
  
    viols = item.get("violations")  
    if isinstance(viols, list):  
        return len(viols)  
  
    # Sometimes nested like {"errors":[...]}  
    errs = item.get("errors")  
    if isinstance(errs, list):  
        return len(errs)  
  
    return 0  
  
  
def _index_report(report: Mapping[str, Any]) -> Dict[str, int]:  
    idx: Dict[str, int] = {}  
    for item in _extract_files_list(report):  
        p = _file_path(item)  
        if not p:  
            continue  
        idx[p] = int(_violation_count(item))  
    return idx  
  
  
def _total_violations(report: Mapping[str, Any], idx: Mapping[str, int]) -> int:  
    summ = report.get("summary")  
    if isinstance(summ, dict):  
        tv = summ.get("total_violations")  
        if isinstance(tv, int):  
            return int(tv)  
    # fallback: sum per-file counts  
    return int(sum(idx.values()))  
  
  
def _total_files(report: Mapping[str, Any], idx: Mapping[str, int]) -> int:  
    summ = report.get("summary")  
    if isinstance(summ, dict):  
        tf = summ.get("total_files")  
        if isinstance(tf, int):  
            return int(tf)  
    # fallback: number of indexed file items  
    return int(len(idx))  
  
  
def diff_workflow_grammar_gate_reports(  
    old_report: Mapping[str, Any],  
    new_report: Mapping[str, Any],  
) -> Dict[str, Any]:  
    """  
    Compute a structured diff between two grammar-gate reports.  
  
    Returns a JSON-serializable dict with deterministic ordering of lists.  
    """  
    old_idx = _index_report(old_report)  
    new_idx = _index_report(new_report)  
  
    old_paths = set(old_idx.keys())  
    new_paths = set(new_idx.keys())  
  
    added = sorted(new_paths - old_paths)  
    removed = sorted(old_paths - new_paths)  
  
    changed: List[Dict[str, Any]] = []  
    for p in sorted(old_paths & new_paths):  
        ov = int(old_idx.get(p, 0))  
        nv = int(new_idx.get(p, 0))  
        if ov != nv:  
            changed.append(  
                {  
                    "path": p,  
                    "old_violations": ov,  
                    "new_violations": nv,  
                    "delta_violations": nv - ov,  
                }  
            )  
  
    old_total_v = _total_violations(old_report, old_idx)  
    new_total_v = _total_violations(new_report, new_idx)  
  
    out: Dict[str, Any] = {  
        "schema": DIFF_SCHEMA_ID,  
        "old": {  
            "total_files": _total_files(old_report, old_idx),  
            "total_violations": old_total_v,  
        },  
        "new": {  
            "total_files": _total_files(new_report, new_idx),  
            "total_violations": new_total_v,  
        },  
        "delta_total_violations": int(new_total_v - old_total_v),  
        "added_files": added,  
        "removed_files": removed,  
        "changed_files": changed,  
    }  
    return out  