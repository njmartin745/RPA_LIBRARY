"""  
DOCTOR-1A: Workflow grammar gate (programmatic check/fix).  
  
Single responsibility:  
- Provide a DOCTOR-layer API to (a) check workflows for unsupported actions without writing,  
  or (b) sanitize workflows (in-place or to output_dir), and always produce a structured report.  
  
Builds on:  
- BUILD-2G for tree gating  
- REPORT-1A for deterministic report generation  
"""  
  
from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from dataclasses import dataclass  
from typing import Any, Dict, Optional, Sequence, Literal  
  
from BUILD.build_2d_step_grammar_gate import ALLOWED_ACTIONS  
from BUILD.build_2g_workflow_tree_grammar_gate import (  
    WorkflowTreeGateResult,  
    gate_workflow_tree_sanitize,  
)  
from REPORT.report_1a_workflow_grammar_gate_report import build_grammar_gate_report  
  
__all__ = [  
    "DoctorWorkflowGrammarGateOutcome",  
    "doctor_check_workflow_grammar",  
    "doctor_fix_workflow_grammar",  
]  
  
  
DoctorMode = Literal["check", "fix"]  
  
  
@dataclass(frozen=True)  
class DoctorWorkflowGrammarGateOutcome:  
    mode: DoctorMode  
    root_dir: str  
    output_dir: Optional[str]  
    in_place: bool  
    tree_result: WorkflowTreeGateResult  
    report: Dict[str, Any]  
  
    @property  
    def total_files(self) -> int:  
        return self.tree_result.total_files  
  
    @property  
    def total_violations(self) -> int:  
        return self.tree_result.total_violations  
  
  
def doctor_check_workflow_grammar(  
    root_dir: str,  
    *,  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
    recursive: bool = True,  
    drop_empty_repeat: bool = True,  
) -> DoctorWorkflowGrammarGateOutcome:  
    """  
    Checks workflows under root_dir for unsupported actions.  
  
    - Does not write files (in-memory sanitize only)  
    - Returns a report including all violations found  
    """  
    tree_result = gate_workflow_tree_sanitize(  
        root_dir,  
        allowed_actions=allowed_actions,  
        recursive=recursive,  
        in_place=False,  
        output_dir=None,  
        drop_empty_repeat=drop_empty_repeat,  
    )  
    report = build_grammar_gate_report(tree_result)  
    return DoctorWorkflowGrammarGateOutcome(  
        mode="check",  
        root_dir=str(root_dir),  
        output_dir=None,  
        in_place=False,  
        tree_result=tree_result,  
        report=report,  
    )  
  
  
def doctor_fix_workflow_grammar(  
    root_dir: str,  
    *,  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
    recursive: bool = True,  
    in_place: bool = True,  
    output_dir: Optional[str] = None,  
    drop_empty_repeat: bool = True,  
) -> DoctorWorkflowGrammarGateOutcome:  
    """  
    Sanitizes workflows under root_dir by stripping unsupported actions.  
  
    Writing behavior:  
    - If output_dir is set: writes sanitized copies there (preserving relative paths)  
    - Else if in_place=True: overwrites inputs  
    - Else: in-memory only  
    """  
    tree_result = gate_workflow_tree_sanitize(  
        root_dir,  
        allowed_actions=allowed_actions,  
        recursive=recursive,  
        in_place=in_place,  
        output_dir=output_dir,  
        drop_empty_repeat=drop_empty_repeat,  
    )  
    report = build_grammar_gate_report(tree_result)  
    return DoctorWorkflowGrammarGateOutcome(  
        mode="fix",  
        root_dir=str(root_dir),  
        output_dir=str(output_dir) if output_dir is not None else None,  
        in_place=bool(in_place),  
        tree_result=tree_result,  
        report=report,  
    )  