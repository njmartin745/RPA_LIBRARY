"""  
GUARD-1A: Workflow grammar guard.  
  
Single responsibility:  
- Provide a GUARD-layer wrapper around RUN-1A gating that:  
  - returns a workflow dict safe to execute (validated or sanitized)  
  - optionally raises a more informative ValueError message on violations  
"""  
  
from __future__ import annotations  
from pathlib import Path   
from dataclasses import dataclass  
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union, Literal  
  
from BUILD.build_2d_step_grammar_gate import ALLOWED_ACTIONS, GrammarViolation  
from RUN.run_1a_workflow_grammar_gate import (  
    RunWorkflowGateOutcome,  
    gate_workflow_dict_for_run,  
    gate_workflow_path_for_run,  
)  
  
__all__ = [  
    "GuardOnViolationMode",  
    "WorkflowGrammarGuardConfig",  
    "format_grammar_violations_summary",  
    "guard_workflow_dict_for_execution",  
    "guard_workflow_path_for_execution",  
]  
  
  
GuardOnViolationMode = Literal["raise", "sanitize"]  
  
  
@dataclass(frozen=True)  
class WorkflowGrammarGuardConfig:  
    on_violation: GuardOnViolationMode = "raise"  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS  
    drop_empty_repeat: bool = True  
  
    # file-specific options (only used by guard_workflow_path_for_execution)  
    in_place_sanitize: bool = False  
    output_path: Optional[str] = None  
  
  
def format_grammar_violations_summary(  
    violations: Sequence[GrammarViolation],  
    *,  
    source: Optional[str] = None,  
    max_items: int = 20,  
) -> str:  
    """  
    Deterministically format a compact summary for exceptions/logs.  
    """  
    src = f" in {source}" if source else ""  
    n = len(violations)  
    head = f"Unsupported workflow action(s) detected{src}: {n} violation(s)."  
    if n == 0:  
        return head  
  
    lines = [head]  
    for i, v in enumerate(violations[: max_items if max_items >= 0 else n], start=1):  
        lines.append(f"{i:02d}. action={v.action!r} path={v.path!r}")  
    if max_items >= 0 and n > max_items:  
        lines.append(f"... ({n - max_items} more)")  
    return "\n".join(lines)  
  
  
def guard_workflow_dict_for_execution(  
    workflow: Mapping[str, Any],  
    *,  
    config: WorkflowGrammarGuardConfig = WorkflowGrammarGuardConfig(),  
) -> Dict[str, Any]:  
    """  
    Returns a workflow dict safe to execute.  
  
    - config.on_violation="raise": raises ValueError with a friendly summary  
    - config.on_violation="sanitize": returns sanitized workflow  
    """  
    if config.on_violation == "raise":  
        try:  
            out = gate_workflow_dict_for_run(  
                workflow,  
                on_violation="raise",  
                allowed_actions=config.allowed_actions,  
                drop_empty_repeat=config.drop_empty_repeat,  
            )  
            return out.workflow  
        except ValueError:  
            # Re-run in sanitize mode (in-memory) to collect deterministic violations for message.  
            out2 = gate_workflow_dict_for_run(  
                workflow,  
                on_violation="sanitize",  
                allowed_actions=config.allowed_actions,  
                drop_empty_repeat=config.drop_empty_repeat,  
            )  
            raise ValueError(format_grammar_violations_summary(out2.violations)) from None  
  
    if config.on_violation == "sanitize":  
        out = gate_workflow_dict_for_run(  
            workflow,  
            on_violation="sanitize",  
            allowed_actions=config.allowed_actions,  
            drop_empty_repeat=config.drop_empty_repeat,  
        )  
        return out.workflow  
  
    raise ValueError(f"Unsupported on_violation mode: {config.on_violation!r}")  
  
  
def guard_workflow_path_for_execution(  
    path: Union[str, "Path"],  
    *,  
    config: WorkflowGrammarGuardConfig = WorkflowGrammarGuardConfig(),  
) -> Dict[str, Any]:  
    """  
    Returns a workflow dict safe to execute from a JSON file path.  
  
    - config.on_violation="raise": raises ValueError with a friendly summary  
    - config.on_violation="sanitize": returns sanitized workflow (and optionally writes per config)  
    """  
    if config.on_violation == "raise":  
        try:  
            out = gate_workflow_path_for_run(  
                path,  
                on_violation="raise",  
                allowed_actions=config.allowed_actions,  
                drop_empty_repeat=config.drop_empty_repeat,  
            )  
            return out.workflow  
        except ValueError:  
            out2 = gate_workflow_path_for_run(  
                path,  
                on_violation="sanitize",  
                allowed_actions=config.allowed_actions,  
                in_place_sanitize=False,  
                output_path=None,  
                drop_empty_repeat=config.drop_empty_repeat,  
            )  
            raise ValueError(  
                format_grammar_violations_summary(out2.violations, source=str(path))  
            ) from None  
  
    if config.on_violation == "sanitize":  
        out = gate_workflow_path_for_run(  
            path,  
            on_violation="sanitize",  
            allowed_actions=config.allowed_actions,  
            in_place_sanitize=config.in_place_sanitize,  
            output_path=config.output_path,  
            drop_empty_repeat=config.drop_empty_repeat,  
        )  
        return out.workflow  
  
    raise ValueError(f"Unsupported on_violation mode: {config.on_violation!r}")  