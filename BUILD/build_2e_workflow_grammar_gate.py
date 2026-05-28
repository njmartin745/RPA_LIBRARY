"""  
BUILD-2E: Workflow-level wrapper around BUILD-2D step grammar enforcement.  
  
Single responsibility:  
- Apply step grammar validation/sanitization to a *workflow dict* (not just steps).  
- Keep behavior pure and deterministic; do not mutate inputs.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple  
  
from BUILD.build_2d_step_grammar_gate import (  
    ALLOWED_ACTIONS,  
    GrammarViolation,  
    assert_supported_actions,  
    find_unsupported_actions,  
    strip_unsupported_actions,  
)  
  
__all__ = [  
    "WorkflowGateResult",  
    "find_workflow_unsupported_actions",  
    "assert_workflow_supported_actions",  
    "sanitize_workflow_steps",  
]  
  
  
@dataclass(frozen=True)  
class WorkflowGateResult:  
    """Result of gating a workflow at the workflow-dict level."""  
    violations: Tuple[GrammarViolation, ...]  
    sanitized_workflow: Dict[str, Any]  
  
  
def _copy_workflow_shallow(workflow: Mapping[str, Any]) -> Dict[str, Any]:  
    # Shallow copy is enough because we replace "steps" with a new list when sanitizing.  
    return dict(workflow)  
  
  
def find_workflow_unsupported_actions(  
    workflow: Mapping[str, Any],  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
) -> List[GrammarViolation]:  
    """  
    Find unsupported actions in workflow["steps"] (including nested repeat blocks).  
    If steps is missing or not a list, treat as empty (no violations here).  
    """  
    steps = workflow.get("steps")  
    if not isinstance(steps, list):  
        return []  
    return find_unsupported_actions(steps, allowed_actions=allowed_actions)  
  
  
def assert_workflow_supported_actions(  
    workflow: Mapping[str, Any],  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
) -> None:  
    """  
    Raises ValueError if workflow contains unsupported/invalid actions in workflow["steps"].  
    """  
    steps = workflow.get("steps")  
    if not isinstance(steps, list):  
        # No steps => nothing to validate here; schema validation is handled elsewhere.  
        return  
    assert_supported_actions(steps, allowed_actions=allowed_actions)  
  
  
def sanitize_workflow_steps(  
    workflow: Mapping[str, Any],  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
    *,  
    drop_empty_repeat: bool = True,  
) -> WorkflowGateResult:  
    """  
    Returns a sanitized copy of workflow with unsupported actions removed from workflow["steps"].  
  
    This does NOT attempt to convert unsupported actions to supported ones.  
    """  
    steps = workflow.get("steps")  
    violations = []  
    sanitized_steps: Optional[List[Dict[str, Any]]] = None  
  
    if isinstance(steps, list):  
        violations = find_unsupported_actions(steps, allowed_actions=allowed_actions)  
        sanitized_steps = strip_unsupported_actions(  
            steps,  
            allowed_actions=allowed_actions,  
            drop_empty_repeat=drop_empty_repeat,  
        )  
  
    out = _copy_workflow_shallow(workflow)  
    if sanitized_steps is not None:  
        out["steps"] = sanitized_steps  
  
    return WorkflowGateResult(violations=tuple(violations), sanitized_workflow=out)  