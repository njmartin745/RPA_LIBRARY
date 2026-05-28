"""  
REPORT-1C: Workflow grammar gate report summary.  
  
Single responsibility:  
- Provide a small, deterministic summary extractor + compact one-line formatter  
  for workflow grammar gate report dicts.  
  
This is intentionally tolerant of minor schema variations and uses best-effort  
fallbacks when summary fields are absent.  
"""  
  
from __future__ import annotations  
  
from typing import Any, Dict, List, Mapping, Optional  
  
__all__ = [  
    "build_grammar_gate_report_summary",  
    "format_grammar_gate_summary_line",  
]  
  
  
def _extract_files_list(report: Mapping[str, Any]) -> List[Mapping[str, Any]]:  
    for k in ("files", "items", "results", "workflows"):  
        v = report.get(k)  
        if isinstance(v, list) and all(isinstance(i, dict) for i in v):  
            return v  # type: ignore[return-value]  
    return []  
  
  
def _violation_count(item: Mapping[str, Any]) -> int:  
    for k in ("violation_count", "violations_count", "n_violations", "count"):  
        v = item.get(k)  
        if isinstance(v, int):  
            return int(v)  
  
    viols = item.get("violations")  
    if isinstance(viols, list):  
        return len(viols)  
  
    errs = item.get("errors")  
    if isinstance(errs, list):  
        return len(errs)  
  
    return 0  
  
  
def build_grammar_gate_report_summary(report: Mapping[str, Any]) -> Dict[str, Any]:  
    """  
    Extract a compact summary from a workflow grammar gate report dict.  
  
    Returns a JSON-serializable dict:  
      { ok, total_files, total_violations, files_with_violations }  
    """  
    summ = report.get("summary") if isinstance(report.get("summary"), dict) else None  
    total_files: Optional[int] = None  
    total_violations: Optional[int] = None  
    files_with_violations: Optional[int] = None  
  
    if isinstance(summ, dict):  
        tf = summ.get("total_files")  
        tv = summ.get("total_violations")  
        fw = summ.get("files_with_violations")  
        if isinstance(tf, int):  
            total_files = int(tf)  
        if isinstance(tv, int):  
            total_violations = int(tv)  
        if isinstance(fw, int):  
            files_with_violations = int(fw)  
  
    if total_files is None or total_violations is None or files_with_violations is None:  
        items = _extract_files_list(report)  
        counts = [_violation_count(it) for it in items]  
        if total_files is None:  
            total_files = int(len(items))  
        if total_violations is None:  
            total_violations = int(sum(counts))  
        if files_with_violations is None:  
            files_with_violations = int(sum(1 for c in counts if c > 0))  
  
    ok = int(total_violations) == 0  
    return {  
        "ok": bool(ok),  
        "total_files": int(total_files),  
        "total_violations": int(total_violations),  
        "files_with_violations": int(files_with_violations),  
    }  
  
  
def format_grammar_gate_summary_line(  
    report: Mapping[str, Any],  
    *,  
    label: str = "workflow_grammar_gate",  
) -> str:  
    """  
    Deterministic compact one-line status suitable for CI logs.  
    """  
    s = build_grammar_gate_report_summary(report)  
    status = "OK" if s["ok"] else "FAIL"  
    if s["ok"]:  
        return f"{label} {status} files={s['total_files']} violations={s['total_violations']}"  
    return (  
        f"{label} {status} files={s['total_files']} "  
        f"violations={s['total_violations']} files_with_violations={s['files_with_violations']}"  
    )  