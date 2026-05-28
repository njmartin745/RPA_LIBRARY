"""  
BUILD-2A — Repeat Support (Milestone 12.5.7)  
  
Purpose  
-------  
Provide deterministic, rule-based helpers for BUILD-2A that:  
- preserve `repeat` blocks (instead of flattening them)  
- normalize actions using an alias->canonical mapping (ACTION_MAP)  
- filter steps to those allowed by the action registry  
- validate steps recursively, including nested `repeat` blocks  
  
Notes  
-----  
- This module is intentionally pure/deterministic (no I/O, no registry reads).  
- It is designed to be called by BUILD/build_2a_nl_spec_generator.py.  
"""  
  
from __future__ import annotations  
  
from typing import Any, Dict, List, Mapping, Sequence, Set  
  
__all__ = [  
    "normalized_allowed_actions",  
    "normalize_and_filter_steps_keep_repeat",  
    "validate_steps_allow_repeat",  
    "dev_smoke",  
]  
  
  
def normalized_allowed_actions(allowed_raw: Set[str], action_map: Mapping[str, str]) -> Set[str]:  
    """Normalize registry actions using the same alias->canonical mapping used for steps."""  
    return {action_map.get(a, a) for a in allowed_raw}  
  
  
def _normalize_action(action: str, action_map: Mapping[str, str]) -> str:  
    return action_map.get(action, action)  
  
  
def _coerce_repeat_times(v: Any) -> int:  
    """  
    Coerce repeat `times` to a deterministic positive int.  
    Missing/invalid/<=0 values become 1.  
    """  
    try:  
        i = int(v)  
    except Exception:  
        return 1  
    return i if i >= 1 else 1  
  
  
def normalize_and_filter_steps_keep_repeat(  
    steps: Sequence[Dict[str, Any]],  
    allowed_raw: Set[str],  
    *,  
    action_map: Mapping[str, str],  
) -> List[Dict[str, Any]]:  
    """  
    Normalize and filter steps:  
    - Apply alias->canonical action mapping  
    - Drop unsupported actions (per normalized registry allow-list)  
    - Drop `log` steps (BUILD-2A emits them only as scaffolding)  
    - Preserve `repeat` blocks *if* `repeat` is allowed; otherwise flatten them  
    """  
    allowed_norm = normalized_allowed_actions(allowed_raw, action_map)  
  
    out: List[Dict[str, Any]] = []  
    for st in steps:  
        if not isinstance(st, dict):  
            continue  
  
        action0 = st.get("action")  
        if not isinstance(action0, str) or not action0.strip():  
            continue  
  
        action = _normalize_action(action0.strip(), action_map)  
  
        # Keep BUILD output deterministic and execution-focused.  
        if action == "log":  
            continue  
  
        if action == "repeat":  
            inner = st.get("steps")  
            inner_list: List[Dict[str, Any]] = inner if isinstance(inner, list) else []  
            inner_out = normalize_and_filter_steps_keep_repeat(  
                inner_list, allowed_raw, action_map=action_map  
            )  
  
            # If repeat is not supported in the registry, flatten deterministically.  
            if "repeat" not in allowed_norm:  
                out.extend(inner_out)  
                continue  
  
            new_repeat: Dict[str, Any] = {  
                "action": "repeat",  
                "times": _coerce_repeat_times(st.get("times", 1)),  
                "steps": inner_out,  
            }  
  
            name = st.get("name")  
            if isinstance(name, str) and name.strip():  
                new_repeat["name"] = name.strip()  
  
            step_id = st.get("step_id")  
            if isinstance(step_id, str) and step_id.strip():  
                new_repeat["step_id"] = step_id.strip()  
  
            out.append(new_repeat)  
            continue  
  
        # If typing isn't supported, deterministically convert to exec_js placeholder.  
        if action == "type_selector_secret" and action not in allowed_norm:  
            if "exec_js" in allowed_norm:  
                new_step = dict(st)  
                new_step["action"] = "exec_js"  
                new_step.pop("secret", None)  
                new_step.setdefault(  
                    "script",  
                    "return { ok: true, note: 'TODO: implement typing via supported actions' };",  
                )  
                out.append(new_step)  
            continue  
  
        if action not in allowed_norm:  
            continue  
  
        new_step = dict(st)  
        new_step["action"] = action  
        out.append(new_step)  
  
    return out  
  
  
def validate_steps_allow_repeat(  
    steps: Sequence[Dict[str, Any]],  
    allowed_raw: Set[str],  
    *,  
    action_map: Mapping[str, str],  
) -> None:  
    """  
    Validate steps against normalized allowed actions, allowing nested `repeat` blocks.  
    This is a lightweight deterministic validation (schema validation is handled elsewhere).  
    """  
    allowed_norm = normalized_allowed_actions(allowed_raw, action_map)  
  
    def _walk(seq: Sequence[Dict[str, Any]], path: str) -> None:  
        for i, st in enumerate(seq):  
            if not isinstance(st, dict):  
                raise ValueError(f"Step {path}[{i}] is not a dict: {type(st)}")  
  
            action0 = st.get("action")  
            if not isinstance(action0, str) or not action0.strip():  
                raise ValueError(f"Step {path}[{i}] missing/invalid action")  
  
            action = _normalize_action(action0.strip(), action_map)  
  
            if action == "repeat":  
                if "repeat" not in allowed_norm:  
                    raise ValueError(f"Unsupported action at {path}[{i}]: 'repeat' not in registry")  
  
                times = st.get("times", 1)  
                _ = _coerce_repeat_times(times)  # validate/coerce  
  
                inner = st.get("steps")  
                if not isinstance(inner, list):  
                    raise ValueError(f"Repeat step {path}[{i}] missing/invalid 'steps' list")  
  
                _walk(inner, f"{path}[{i}].steps")  
                continue  
  
            if action not in allowed_norm:  
                raise ValueError(  
                    f"Unsupported action at {path}[{i}] (not in registry, normalized): {action!r}"  
                )  
  
    _walk(list(steps), "steps")  
  
  
def dev_smoke() -> None:  
    allowed_raw = {  
        "open",  
        "repeat",  
        "click_selector",  
        "wait_for_selector",  
        "exec_js",  
    }  
    action_map = {  
        "click": "click_selector",  
        "wait_for_element": "wait_for_selector",  
        "javascript": "exec_js",  
    }  
  
    steps_in = [  
        {  
            "action": "repeat",  
            "times": "1",  
            "name": "Repeat smoke",  
            "steps": [  
                {"action": "click", "selector_ref": "X"},  
                {"action": "log", "message": "dropped"},  
            ],  
        }  
    ]  
    steps_out = normalize_and_filter_steps_keep_repeat(steps_in, allowed_raw, action_map=action_map)  
  
    assert steps_out and steps_out[0]["action"] == "repeat"  
    assert steps_out[0]["steps"] and steps_out[0]["steps"][0]["action"] == "click_selector"  
  
    validate_steps_allow_repeat(steps_out, allowed_raw, action_map=action_map)  
  
  
if __name__ == "__main__":  
    dev_smoke()  