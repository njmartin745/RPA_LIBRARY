"""  
BUILD-2D: Step grammar enforcement / gating.  
  
Single responsibility:  
- Validate that a workflow "steps" list only uses supported STEP_GRAMMAR actions.  
- Provide pure, deterministic helpers to find/strip unsupported steps.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple  
  
  
__all__ = [  
    "ALLOWED_ACTIONS",  
    "GrammarViolation",  
    "find_unsupported_actions",  
    "assert_supported_actions",  
    "strip_unsupported_actions",  
]  
  
  
ALLOWED_ACTIONS: Tuple[str, ...] = (  
    "open",  
    "click_selector",  
    "type_selector_secret",  
    "wait_for_selector",  
    "exec_js",  
    "exec_js_file",  
    "repeat",  
    "log",  
    "switch_back_to_main_tab",  
)  
  
  
@dataclass(frozen=True)  
class GrammarViolation:  
    """Represents a single unsupported action occurrence in a workflow."""  
    action: str  
    path: str  # e.g. "$[3]" or "$[1].steps[0]"  
  
    def to_dict(self) -> Dict[str, str]:  
        return {"action": self.action, "path": self.path}  
  
  
def _as_list(x: Any) -> List[Any]:  
    if x is None:  
        return []  
    if isinstance(x, list):  
        return x  
    return [x]  
  
  
def _iter_steps_with_paths(  
    steps: Sequence[Mapping[str, Any]],  
    base_path: str = "$",  
) -> Iterable[Tuple[Mapping[str, Any], str]]:  
    for i, step in enumerate(steps):  
        path = f"{base_path}[{i}]"  
        yield step, path  
        if isinstance(step, Mapping) and step.get("action") == "repeat":  
            nested = step.get("steps")  
            if isinstance(nested, list):  
                yield from _iter_steps_with_paths(nested, base_path=f"{path}.steps")  
  
  
def find_unsupported_actions(  
    steps: Sequence[Mapping[str, Any]],  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
) -> List[GrammarViolation]:  
    """  
    Returns a list of all unsupported action occurrences (including nested repeat steps).  
    Pure function; does not mutate input.  
    """  
    allowed: Set[str] = set(allowed_actions)  
    violations: List[GrammarViolation] = []  
  
    for step, path in _iter_steps_with_paths(steps):  
        action = step.get("action") if isinstance(step, Mapping) else None  
        if not isinstance(action, str) or action.strip() == "":  
            # Missing/invalid action is considered a violation to keep behavior strict/deterministic.  
            violations.append(GrammarViolation(action=str(action), path=path))  
            continue  
        if action not in allowed:  
            violations.append(GrammarViolation(action=action, path=path))  
  
    return violations  
  
  
def assert_supported_actions(  
    steps: Sequence[Mapping[str, Any]],  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
    *,  
    max_show: int = 10,  
) -> None:  
    """  
    Raises ValueError if any step contains an action not in allowed_actions.  
    """  
    violations = find_unsupported_actions(steps, allowed_actions=allowed_actions)  
    if not violations:  
        return  
  
    sample = violations[: max(1, int(max_show))]  
    details = ", ".join([f"{v.action}@{v.path}" for v in sample])  
    more = "" if len(violations) <= len(sample) else f" (+{len(violations) - len(sample)} more)"  
    raise ValueError(  
        "Workflow contains unsupported/invalid actions. "  
        f"Allowed={tuple(allowed_actions)}; Found={details}{more}"  
    )  
  
  
def strip_unsupported_actions(  
    steps: Sequence[Mapping[str, Any]],  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
    *,  
    drop_empty_repeat: bool = True,  
) -> List[Dict[str, Any]]:  
    """  
    Returns a sanitized copy of steps where unsupported actions are removed.  
  
    Notes:  
    - This is deterministic and pure (does not mutate input).  
    - If a repeat block becomes empty and drop_empty_repeat=True, the repeat block is removed.  
    - This does NOT attempt to "convert" unsupported actions (e.g., wait_seconds) into  
      supported ones, because the grammar does not define an equivalent.  
    """  
    allowed: Set[str] = set(allowed_actions)  
    out: List[Dict[str, Any]] = []  
  
    for step in _as_list(list(steps)):  
        if not isinstance(step, Mapping):  
            continue  
  
        action = step.get("action")  
        if not isinstance(action, str) or action not in allowed:  
            continue  
  
        new_step: Dict[str, Any] = dict(step)  
  
        if action == "repeat":  
            nested = step.get("steps")  
            nested_list = nested if isinstance(nested, list) else []  
            new_nested = strip_unsupported_actions(  
                nested_list,  
                allowed_actions=allowed_actions,  
                drop_empty_repeat=drop_empty_repeat,  
            )  
            new_step["steps"] = new_nested  
            if drop_empty_repeat and len(new_nested) == 0:  
                continue  
  
        out.append(new_step)  
  
    return out  