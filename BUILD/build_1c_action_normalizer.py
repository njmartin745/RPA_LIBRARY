from __future__ import annotations  
  
from typing import Any, Dict, List, Mapping  
  
__all__ = [  
    "ACTION_ALIASES",  
    "normalize_action_name",  
    "normalize_step_actions",  
    "normalize_steps_actions",  
    "normalize_workflow_actions",  
    "dev_smoke",  
]  
  
# Keep this intentionally small and explicit (do not mask other invalid actions).  
ACTION_ALIASES: dict[str, str] = {  
    "get": "open",  
}  
  
  
def normalize_action_name(action: Any) -> Any:  
    if not isinstance(action, str):  
        return action  
    return ACTION_ALIASES.get(action, action)  
  
  
def normalize_step_actions(step: Mapping[str, Any]) -> Dict[str, Any]:  
    """  
    Pure: returns a new dict.  
    Also normalizes nested repeat.steps if present.  
    """  
    out: Dict[str, Any] = dict(step)  
  
    if "action" in out:  
        out["action"] = normalize_action_name(out["action"])  
  
    # Handle nested steps (e.g., repeat)  
    nested = out.get("steps")  
    if isinstance(nested, list) and all(isinstance(s, dict) for s in nested):  
        out["steps"] = normalize_steps_actions(nested)  # type: ignore[arg-type]  
  
    return out  
  
  
def normalize_steps_actions(steps: List[Mapping[str, Any]]) -> List[Dict[str, Any]]:  
    """Pure: returns a new list of new dicts."""  
    return [normalize_step_actions(s) for s in steps]  
  
  
def normalize_workflow_actions(workflow: Mapping[str, Any]) -> Dict[str, Any]:  
    """  
    Pure: returns a new workflow dict with normalized actions in workflow['steps'].  
    """  
    out: Dict[str, Any] = dict(workflow)  
    steps = out.get("steps")  
    if isinstance(steps, list) and all(isinstance(s, dict) for s in steps):  
        out["steps"] = normalize_steps_actions(steps)  # type: ignore[arg-type]  
    return out  
  
  
def dev_smoke() -> None:  
    wf = {  
        "metadata": {"generator": "SMOKE"},  
        "steps": [  
            {"action": "get", "url": "https://example.com"},  
            {"action": "repeat", "times": 1, "steps": [{"action": "get", "url": "https://x"}]},  
        ],  
    }  
  
    norm = normalize_workflow_actions(wf)  
  
    assert wf["steps"][0]["action"] == "get"  # original unchanged  
    assert norm["steps"][0]["action"] == "open"  
    assert norm["steps"][1]["steps"][0]["action"] == "open"  