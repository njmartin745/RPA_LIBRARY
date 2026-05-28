"""  
REPORT-1B: Deterministic text rendering for workflow grammar gate reports.  
  
Single responsibility:  
- Convert the REPORT-1A grammar gate report dict into a stable, human-readable text summary.  
- No I/O; formatting only.  
"""  
  
from __future__ import annotations  
  
from typing import Any, Mapping, Sequence, Optional, List, Dict, Tuple  
  
__all__ = [  
    "format_grammar_gate_report_text",  
]  
  
  
def _get_file_path(file_item: Mapping[str, Any]) -> str:  
    return (  
        str(file_item.get("path") or "")  
        or str(file_item.get("file_path") or "")  
        or str(file_item.get("file") or "")  
        or "<unknown>"  
    )  
  
  
def _get_violations(file_item: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:  
    v = file_item.get("violations")  
    return v if isinstance(v, list) else []  
  
  
def _get_violation_action(v: Mapping[str, Any]) -> str:  
    return str(v.get("action") or v.get("unsupported_action") or "<unknown>")  
  
  
def _get_violation_path(v: Mapping[str, Any]) -> str:  
    return str(v.get("path") or v.get("json_path") or "<unknown>")  
  
  
def format_grammar_gate_report_text(  
    report: Mapping[str, Any],  
    *,  
    include_ok_files: bool = False,  
    max_files: int = 200,  
    max_violations_per_file: int = 200,  
) -> str:  
    """  
    Deterministically format a grammar gate report dict.  
  
    - include_ok_files: if False, omits files with 0 violations.  
    - max_files/max_violations_per_file: deterministic truncation (appends "...").  
    """  
    total_files = int(report.get("total_files") or 0)  
    total_violations = int(report.get("total_violations") or 0)  
    files = report.get("files")  
    files_list: List[Mapping[str, Any]] = files if isinstance(files, list) else []  
  
    # Deterministic ordering by path (fallback to stable string)  
    keyed: List[Tuple[str, Mapping[str, Any]]] = [(_get_file_path(f), f) for f in files_list]  
    keyed.sort(key=lambda x: x[0])  
  
    lines: List[str] = [f"workflow_grammar_gate: files={total_files} violations={total_violations}"]  
  
    shown_files = 0  
    hidden_files = 0  
  
    for path, f in keyed:  
        violations = _get_violations(f)  
        vcount = len(violations)  
        wrote_file = f.get("wrote_file")  
        wrote_str = "unknown" if wrote_file is None else ("true" if bool(wrote_file) else "false")  
  
        if (not include_ok_files) and vcount == 0:  
            continue  
  
        if shown_files >= max_files:  
            hidden_files += 1  
            continue  
  
        lines.append(f"- {path} (violations={vcount}, wrote_file={wrote_str})")  
        shown_files += 1  
  
        shown_v = 0  
        hidden_v = 0  
        for v in violations:  
            if shown_v >= max_violations_per_file:  
                hidden_v += 1  
                continue  
            action = _get_violation_action(v)  
            vpath = _get_violation_path(v)  
            lines.append(f"  * action={action!r} path={vpath!r}")  
            shown_v += 1  
  
        if hidden_v:  
            lines.append(f"  ... ({hidden_v} more violation(s))")  
  
    if hidden_files:  
        lines.append(f"... ({hidden_files} more file(s))")  
  
    return "\n".join(lines)  