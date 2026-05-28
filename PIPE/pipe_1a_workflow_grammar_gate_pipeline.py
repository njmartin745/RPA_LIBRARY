"""  
PIPE-1A: Workflow grammar gate pipeline runner.  
  
Single responsibility:  
- Provide a CI/pipeline-friendly programmatic runner to:  
  - check workflows (no writes) and return an exit_code based on violations  
  - fix workflows (sanitize) with optional in-place or output-dir writes  
  - optionally write a deterministic JSON report  
  
Builds on:  
- DOCTOR-1A (check/fix orchestration + report dict)  
- REPORT-1A JSON text dumping  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from pathlib import Path  
from typing import Optional, Sequence, Literal  
  
from BUILD.build_2d_step_grammar_gate import ALLOWED_ACTIONS  
from DOCTOR.doctor_1a_workflow_grammar_gate import (  
    DoctorWorkflowGrammarGateOutcome,  
    doctor_check_workflow_grammar,  
    doctor_fix_workflow_grammar,  
)  
from REPORT.report_1a_workflow_grammar_gate_report import dump_grammar_gate_report_json_text  
  
__all__ = [  
    "PipelineMode",  
    "WorkflowGrammarGatePipelineResult",  
    "run_workflow_grammar_gate_pipeline",  
]  
  
PipelineMode = Literal["check", "fix"]  
  
  
@dataclass(frozen=True)  
class WorkflowGrammarGatePipelineResult:  
    mode: PipelineMode  
    root_dir: str  
    exit_code: int  # 0 ok, 2 violations in check-mode, 1 error  
    outcome: Optional[DoctorWorkflowGrammarGateOutcome]  
    report_path: Optional[str]  
    wrote_report: bool  
  
  
def _write_report(report_path: str, report: dict) -> None:  
    p = Path(report_path)  
    p.parent.mkdir(parents=True, exist_ok=True)  
    p.write_text(dump_grammar_gate_report_json_text(report), encoding="utf-8")  
  
  
def run_workflow_grammar_gate_pipeline(  
    root_dir: str,  
    *,  
    mode: PipelineMode = "check",  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
    recursive: bool = True,  
    in_place: bool = True,  
    output_dir: Optional[str] = None,  
    report_json_path: Optional[str] = None,  
    drop_empty_repeat: bool = True,  
) -> WorkflowGrammarGatePipelineResult:  
    """  
    Runs workflow grammar gating in a pipeline-friendly way.  
  
    Exit codes:  
      - mode="check": 0 if no violations, else 2  
      - mode="fix": always 0 (unless error)  
      - 1 on unexpected errors / invalid root_dir  
  
    root_dir must exist (file or directory), else returns exit_code=1.  
    """  
    try:  
        rp = Path(root_dir)  
        if not rp.exists():  
            return WorkflowGrammarGatePipelineResult(  
                mode=mode,  
                root_dir=str(root_dir),  
                exit_code=1,  
                outcome=None,  
                report_path=report_json_path,  
                wrote_report=False,  
            )  
  
        if mode == "check":  
            outcome = doctor_check_workflow_grammar(  
                str(root_dir),  
                allowed_actions=allowed_actions,  
                recursive=recursive,  
                drop_empty_repeat=drop_empty_repeat,  
            )  
            wrote = False  
            if report_json_path is not None:  
                _write_report(report_json_path, outcome.report)  
                wrote = True  
            exit_code = 0 if outcome.total_violations == 0 else 2  
            return WorkflowGrammarGatePipelineResult(  
                mode=mode,  
                root_dir=str(root_dir),  
                exit_code=exit_code,  
                outcome=outcome,  
                report_path=report_json_path,  
                wrote_report=wrote,  
            )  
  
        if mode == "fix":  
            outcome = doctor_fix_workflow_grammar(  
                str(root_dir),  
                allowed_actions=allowed_actions,  
                recursive=recursive,  
                in_place=in_place,  
                output_dir=output_dir,  
                drop_empty_repeat=drop_empty_repeat,  
            )  
            wrote = False  
            if report_json_path is not None:  
                _write_report(report_json_path, outcome.report)  
                wrote = True  
            return WorkflowGrammarGatePipelineResult(  
                mode=mode,  
                root_dir=str(root_dir),  
                exit_code=0,  
                outcome=outcome,  
                report_path=report_json_path,  
                wrote_report=wrote,  
            )  
  
        return WorkflowGrammarGatePipelineResult(  
            mode=mode,  
            root_dir=str(root_dir),  
            exit_code=1,  
            outcome=None,  
            report_path=report_json_path,  
            wrote_report=False,  
        )  
  
    except Exception:  
        return WorkflowGrammarGatePipelineResult(  
            mode=mode,  
            root_dir=str(root_dir),  
            exit_code=1,  
            outcome=None,  
            report_path=report_json_path,  
            wrote_report=False,  
        )  