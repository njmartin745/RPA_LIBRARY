"""  
GUARD-1A: Workflow grammar gate guard.  
  
Single responsibility:  
- Evaluate a workflow-grammar-gate report against deterministic policy thresholds,  
  optionally comparing to a baseline report (delta policy), and return a decision  
  suitable for CI gating.  
  
Builds on:  
- REPORT-1C for summary extraction  
- DIFF-1A for baseline delta computation  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Any, Dict, List, Mapping, Optional  
  
from DIFF.diff_1a_workflow_grammar_gate_report_diff import diff_workflow_grammar_gate_reports  
from REPORT.report_1c_workflow_grammar_gate_report_summary import build_grammar_gate_report_summary  
  
__all__ = [  
    "WorkflowGrammarGateGuardDecision",  
    "guard_workflow_grammar_gate_report",  
]  
  
  
@dataclass(frozen=True)  
class WorkflowGrammarGateGuardDecision:  
    ok: bool  
    exit_code: int  
    reasons: List[str]  
    summary: Dict[str, Any]  
    diff: Optional[Dict[str, Any]] = None  
  
  
def guard_workflow_grammar_gate_report(  
    report: Mapping[str, Any],  
    *,  
    baseline_report: Optional[Mapping[str, Any]] = None,  
    max_total_violations: int = 0,  
    max_files_with_violations: int = 0,  
    max_delta_total_violations: int = 0,  
) -> WorkflowGrammarGateGuardDecision:  
    """  
    Guard a grammar gate report.  
  
    Policy:  
    - total_violations <= max_total_violations  
    - files_with_violations <= max_files_with_violations  
    - if baseline_report provided: delta_total_violations <= max_delta_total_violations  
  
    exit_code:  
    - 0 if ok else 2  
    """  
    summary = build_grammar_gate_report_summary(report)  
  
    reasons: List[str] = []  
  
    tv = int(summary.get("total_violations", 0))  
    fw = int(summary.get("files_with_violations", 0))  
  
    if tv > int(max_total_violations):  
        reasons.append(f"total_violations {tv} > {int(max_total_violations)}")  
  
    if fw > int(max_files_with_violations):  
        reasons.append(f"files_with_violations {fw} > {int(max_files_with_violations)}")  
  
    d: Optional[Dict[str, Any]] = None  
    if baseline_report is not None:  
        d = diff_workflow_grammar_gate_reports(baseline_report, report)  
        delta_tv = int(d.get("delta_total_violations", 0))  
        if delta_tv > int(max_delta_total_violations):  
            reasons.append(  
                f"delta_total_violations {delta_tv} > {int(max_delta_total_violations)}"  
            )  
  
    ok = len(reasons) == 0  
    return WorkflowGrammarGateGuardDecision(  
        ok=bool(ok),  
        exit_code=0 if ok else 2,  
        reasons=reasons,  
        summary=dict(summary),  
        diff=d,  
    )  