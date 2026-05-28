"""  
DOCTOR-1B: Workflow grammar gate diagnosis (PIPE-backed).  
  
Single responsibility:  
- Provide a programmatic "doctor" API that runs the PIPE workflow grammar gate  
  and returns a deterministic diagnosis object (status + report text).  
  
Notes:  
- No CLI parsing here (CLI-1H owns argv handling).  
- Does not duplicate BUILD/REPORT logic; delegates to PIPE + REPORT-1B.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Any, Dict, Optional  
  
from PIPE.pipe_1a_workflow_grammar_gate_pipeline import run_workflow_grammar_gate_pipeline  
from REPORT.report_1b_workflow_grammar_gate_report_text import format_grammar_gate_report_text  
  
__all__ = [  
    "WorkflowGrammarGateDiagnosis",  
    "doctor_workflow_grammar_gate_diagnosis",  
]  
  
  
@dataclass(frozen=True)  
class WorkflowGrammarGateDiagnosis:  
    ok: bool  
    exit_code: int  
    report: Optional[Dict[str, Any]]  
    report_text: str  
  
  
def doctor_workflow_grammar_gate_diagnosis(  
    root_dir: str,  
    *,  
    mode: str = "check",  
    in_place: bool = True,  
    output_dir: Optional[str] = None,  
    include_ok_files: bool = False,  
    max_files: int = 200,  
    max_violations_per_file: int = 200,  
) -> WorkflowGrammarGateDiagnosis:  
    """  
    Run the workflow grammar gate pipeline and return a diagnosis.  
  
    mode:  
      - "check": no writes; exit_code 2 if violations found  
      - "fix": sanitize (writes depend on in_place/output_dir); exit_code 0 unless error  
    """  
    res = run_workflow_grammar_gate_pipeline(  
        root_dir,  
        mode=str(mode),  
        in_place=bool(in_place),  
        output_dir=output_dir,  
        report_json_path=None,  
    )  
  
    exit_code = int(getattr(res, "exit_code", 1))  
  
    outcome = getattr(res, "outcome", None)  
    if outcome is None or getattr(outcome, "report", None) is None:  
        txt = f"workflow_grammar_gate: error exit_code={exit_code}"  
        return WorkflowGrammarGateDiagnosis(  
            ok=False,  
            exit_code=exit_code,  
            report=None,  
            report_text=txt,  
        )  
  
    report = outcome.report  
    txt = format_grammar_gate_report_text(  
        report,  
        include_ok_files=bool(include_ok_files),  
        max_files=int(max_files),  
        max_violations_per_file=int(max_violations_per_file),  
    )  
  
    return WorkflowGrammarGateDiagnosis(  
        ok=(exit_code == 0),  
        exit_code=exit_code,  
        report=report,  
        report_text=txt,  
    )  