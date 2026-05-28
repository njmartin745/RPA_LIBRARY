"""  
BUILD-2F: File-level workflow grammar gating.  
  
Single responsibility:  
- Load a workflow JSON file (dict with "steps"), validate or sanitize its step actions  
  using BUILD-2E/2D gates, and optionally write the sanitized workflow back.  
  
This module is additive: it does not modify any existing builders; it provides a  
safe wrapper you can call from CLI/build scripts.  
"""  
  
from __future__ import annotations  
  
import json  
from dataclasses import dataclass  
from pathlib import Path  
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple  
  
from BUILD.build_2d_step_grammar_gate import ALLOWED_ACTIONS, GrammarViolation  
from BUILD.build_2e_workflow_grammar_gate import (  
    WorkflowGateResult,  
    assert_workflow_supported_actions,  
    sanitize_workflow_steps,  
)  
  
__all__ = [  
    "WorkflowFileGateResult",  
    "load_workflow_json_file",  
    "dump_workflow_json_text",  
    "gate_workflow_file_assert",  
    "gate_workflow_file_sanitize",  
]  
  
  
@dataclass(frozen=True)  
class WorkflowFileGateResult:  
    path: str  
    violations: Tuple[GrammarViolation, ...]  
    wrote_file: bool  
    sanitized_workflow: Dict[str, Any]  
  
  
def load_workflow_json_file(path: str | Path) -> Dict[str, Any]:  
    """  
    Loads a workflow JSON file and returns the parsed dict.  
  
    Raises:  
      ValueError if JSON root is not an object/dict.  
    """  
    p = Path(path)  
    text = p.read_text(encoding="utf-8")  
    obj = json.loads(text)  
    if not isinstance(obj, dict):  
        raise ValueError(f"Workflow JSON root must be an object/dict: {str(p)}")  
    return obj  
  
  
def dump_workflow_json_text(  
    workflow: Mapping[str, Any],  
    *,  
    indent: int = 2,  
    sort_keys: bool = True,  
) -> str:  
    """  
    Deterministically serializes workflow dict to JSON text.  
    """  
    return json.dumps(workflow, indent=indent, sort_keys=sort_keys, ensure_ascii=False) + "\n"  
  
  
def gate_workflow_file_assert(  
    path: str | Path,  
    *,  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
) -> WorkflowFileGateResult:  
    """  
    Loads and asserts that workflow["steps"] contains only supported actions.  
    Does not modify the file.  
    """  
    wf = load_workflow_json_file(path)  
    assert_workflow_supported_actions(wf, allowed_actions=allowed_actions)  
  
    # If assert passes, violations are empty by definition (no need to recompute).  
    return WorkflowFileGateResult(  
        path=str(Path(path)),  
        violations=tuple(),  
        wrote_file=False,  
        sanitized_workflow=dict(wf),  
    )  
  
  
def gate_workflow_file_sanitize(  
    path: str | Path,  
    *,  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
    in_place: bool = True,  
    output_path: Optional[str | Path] = None,  
    drop_empty_repeat: bool = True,  
    indent: int = 2,  
    sort_keys: bool = True,  
) -> WorkflowFileGateResult:  
    """  
    Loads workflow JSON, removes unsupported actions from workflow["steps"], and writes  
    sanitized JSON to disk.  
  
    Writing behavior:  
    - If output_path is provided, writes there.  
    - Else if in_place=True, overwrites the input file.  
    - Else, does not write (returns sanitized_workflow only).  
  
    Returns:  
      WorkflowFileGateResult with violations and sanitized_workflow.  
    """  
    src = Path(path)  
    wf = load_workflow_json_file(src)  
  
    gated: WorkflowGateResult = sanitize_workflow_steps(  
        wf,  
        allowed_actions=allowed_actions,  
        drop_empty_repeat=drop_empty_repeat,  
    )  
  
    wrote = False  
    dest: Optional[Path] = None  
    if output_path is not None:  
        dest = Path(output_path)  
    elif in_place:  
        dest = src  
  
    if dest is not None:  
        dest.write_text(  
            dump_workflow_json_text(gated.sanitized_workflow, indent=indent, sort_keys=sort_keys),  
            encoding="utf-8",  
        )  
        wrote = True  
  
    return WorkflowFileGateResult(  
        path=str(src),  
        violations=gated.violations,  
        wrote_file=wrote,  
        sanitized_workflow=gated.sanitized_workflow,  
    )  