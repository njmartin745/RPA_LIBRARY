"""  
RUN-1A: Workflow grammar gate run orchestration.  
  
Single responsibility:  
- Orchestrate a single workflow-grammar-gate run by calling:  
  - DOCTOR-1B (pipeline-backed diagnosis)  
  - GUARD-1A (policy evaluation; optional baseline)  
  - HISTORY-1A (optional JSONL append)  
  
No CLI parsing here; callers supply arguments explicitly.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Any, Dict, Mapping, Optional  
  
from DOCTOR.doctor_1b_workflow_grammar_gate import (  
    WorkflowGrammarGateDiagnosis,  
    doctor_workflow_grammar_gate_diagnosis,  
)  
from GUARD.guard_1a_workflow_grammar_gate_guard import (  
    WorkflowGrammarGateGuardDecision,  
    guard_workflow_grammar_gate_report,  
)  
from HISTORY.history_1a_workflow_grammar_gate_history import (  
    append_workflow_grammar_gate_history_jsonl,  
    build_workflow_grammar_gate_history_record,  
)  
  
__all__ = [  
    "WorkflowGrammarGateRunResult",  
    "run_workflow_grammar_gate",  
]  
  
  
@dataclass(frozen=True)  
class WorkflowGrammarGateRunResult:  
    ok: bool  
    exit_code: int  
    diagnosis: WorkflowGrammarGateDiagnosis  
    guard: Optional[WorkflowGrammarGateGuardDecision]  
    history_record: Optional[Dict[str, Any]]  
  
  
def run_workflow_grammar_gate(  
    root_dir: str,  
    *,  
    mode: str = "check",  
    in_place: bool = True,  
    output_dir: Optional[str] = None,  
    # report formatting (passed to DOCTOR)  
    include_ok_files: bool = False,  
    max_files: int = 200,  
    max_violations_per_file: int = 200,  
    # guard enablement  
    apply_guard: Optional[bool] = None,  
    # guard policy  
    baseline_report: Optional[Mapping[str, Any]] = None,  
    max_total_violations: int = 0,  
    max_files_with_violations: int = 0,  
    max_delta_total_violations: int = 0,  
    # history  
    history_jsonl_path: Optional[str] = None,  
    history_meta: Optional[Mapping[str, Any]] = None,  
) -> WorkflowGrammarGateRunResult:  
    """  
    Execute one run:  
    - diagnose workflow tree under root_dir (check or fix)  
    - optionally evaluate guard policy (defaults to enabled only for mode="check")  
    - optionally append a HISTORY-1A record to history_jsonl_path  
    """  
    diag = doctor_workflow_grammar_gate_diagnosis(  
        str(root_dir),  
        mode=str(mode),  
        in_place=bool(in_place),  
        output_dir=output_dir,  
        include_ok_files=bool(include_ok_files),  
        max_files=int(max_files),  
        max_violations_per_file=int(max_violations_per_file),  
    )  
  
    do_guard = bool(apply_guard) if apply_guard is not None else (str(mode) == "check")  
  
    guard_dec: Optional[WorkflowGrammarGateGuardDecision] = None  
    if do_guard and diag.report is not None:  
        guard_dec = guard_workflow_grammar_gate_report(  
            diag.report,  
            baseline_report=baseline_report,  
            max_total_violations=int(max_total_violations),  
            max_files_with_violations=int(max_files_with_violations),  
            max_delta_total_violations=int(max_delta_total_violations),  
        )  
  
    final_exit = int(diag.exit_code)  
    final_ok = bool(diag.ok)  
  
    if guard_dec is not None:  
        final_exit = max(final_exit, int(guard_dec.exit_code))  
        final_ok = bool(final_ok and guard_dec.ok)  
  
    hist_rec: Optional[Dict[str, Any]] = None  
    if history_jsonl_path is not None:  
        meta: Dict[str, Any] = dict(history_meta) if history_meta is not None else {}  
        meta["apply_guard"] = bool(do_guard)  
  
        if guard_dec is not None:  
            meta["guard_ok"] = bool(guard_dec.ok)  
            meta["guard_reasons"] = list(guard_dec.reasons)  
            if guard_dec.diff is not None:  
                meta["guard_diff"] = dict(guard_dec.diff)  
  
        hist_rec = build_workflow_grammar_gate_history_record(  
            root_dir=str(root_dir),  
            mode=str(mode),  
            ok=bool(final_ok),  
            exit_code=int(final_exit),  
            report_text=str(diag.report_text),  
            report=diag.report,  
            meta=meta if meta else None,  
        )  
        append_workflow_grammar_gate_history_jsonl(str(history_jsonl_path), hist_rec)  
  
    return WorkflowGrammarGateRunResult(  
        ok=bool(final_ok),  
        exit_code=int(final_exit),  
        diagnosis=diag,  
        guard=guard_dec,  
        history_record=hist_rec,  
    )  