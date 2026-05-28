"""  
RUN-1A: Pre-run workflow grammar gate.  
  
Single responsibility:  
- Provide a RUN-layer wrapper to assert/sanitize workflow step actions before execution,  
  using BUILD-2E/2F logic (no duplication).  
  
This module does not execute workflows; it only gates them for safe execution.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from pathlib import Path  
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union, Literal  
  
from BUILD.build_2d_step_grammar_gate import ALLOWED_ACTIONS, GrammarViolation  
from BUILD.build_2e_workflow_grammar_gate import (  
    WorkflowGateResult,  
    assert_workflow_supported_actions,  
    sanitize_workflow_steps,  
)  
from BUILD.build_2f_workflow_file_grammar_gate import (  
    WorkflowFileGateResult,  
    gate_workflow_file_assert,  
    gate_workflow_file_sanitize,  
    load_workflow_json_file,  
)  
  
__all__ = [  
    "RunWorkflowGateOutcome",  
    "gate_workflow_dict_for_run",  
    "gate_workflow_path_for_run",  
]  
  
  
OnViolationMode = Literal["raise", "sanitize"]  
  
  
@dataclass(frozen=True)  
class RunWorkflowGateOutcome:  
    """  
    RUN-facing result of gating.  
  
    - violations: any unsupported actions found (possibly empty)  
    - workflow: workflow dict to run (original copy if raise-mode passes; sanitized if sanitize-mode)  
    - source_path: optional provenance when gating from a file  
    """  
    violations: Tuple[GrammarViolation, ...]  
    workflow: Dict[str, Any]  
    source_path: Optional[str] = None  
  
  
def gate_workflow_dict_for_run(  
    workflow: Mapping[str, Any],  
    *,  
    on_violation: OnViolationMode = "raise",  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
    drop_empty_repeat: bool = True,  
) -> RunWorkflowGateOutcome:  
    """  
    Gate an in-memory workflow dict for execution.  
  
    on_violation:  
      - "raise": raises ValueError if unsupported actions exist  
      - "sanitize": strips unsupported actions and returns sanitized workflow + violations  
    """  
    if on_violation == "raise":  
        assert_workflow_supported_actions(workflow, allowed_actions=allowed_actions)  
        return RunWorkflowGateOutcome(violations=tuple(), workflow=dict(workflow), source_path=None)  
  
    if on_violation == "sanitize":  
        gated: WorkflowGateResult = sanitize_workflow_steps(  
            workflow,  
            allowed_actions=allowed_actions,  
            drop_empty_repeat=drop_empty_repeat,  
        )  
        return RunWorkflowGateOutcome(  
            violations=gated.violations,  
            workflow=gated.sanitized_workflow,  
            source_path=None,  
        )  
  
    raise ValueError(f"Unsupported on_violation mode: {on_violation!r}")  
  
  
def gate_workflow_path_for_run(  
    path: Union[str, Path],  
    *,  
    on_violation: OnViolationMode = "raise",  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
    in_place_sanitize: bool = False,  
    output_path: Optional[Union[str, Path]] = None,  
    drop_empty_repeat: bool = True,  
) -> RunWorkflowGateOutcome:  
    """  
    Gate a workflow JSON file for execution.  
  
    on_violation:  
      - "raise": loads and asserts; returns workflow if valid  
      - "sanitize": sanitizes; optionally writes (in_place_sanitize/output_path); returns sanitized  
  
    Notes:  
      - If on_violation="sanitize" and neither in_place_sanitize nor output_path are provided,  
        sanitization is performed in-memory only.  
    """  
    p = Path(path)  
  
    if on_violation == "raise":  
        gate_workflow_file_assert(p, allowed_actions=allowed_actions)  
        wf = load_workflow_json_file(p)  
        return RunWorkflowGateOutcome(violations=tuple(), workflow=wf, source_path=str(p))  
  
    if on_violation == "sanitize":  
        res: WorkflowFileGateResult = gate_workflow_file_sanitize(  
            p,  
            allowed_actions=allowed_actions,  
            in_place=bool(in_place_sanitize) and output_path is None,  
            output_path=str(output_path) if output_path is not None else None,  
            drop_empty_repeat=drop_empty_repeat,  
        )  
        return RunWorkflowGateOutcome(  
            violations=res.violations,  
            workflow=res.sanitized_workflow,  
            source_path=str(p),  
        )  
  
    raise ValueError(f"Unsupported on_violation mode: {on_violation!r}")  