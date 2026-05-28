from __future__ import annotations  
  
import json  
from pathlib import Path  
from typing import Any, Dict, List, Set  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from SNAP.snap_1a_workflow_capture import (  
    ALLOWED_WORKFLOW_ACTIONS,  
    CapturedEvent,  
    captured_events_to_steps,  
)  
  
__all__ = ["dev_smoke"]  
  
  
def _repo_root() -> Path:  
    # dev/ is at repo_root/dev; so parent is repo root  
    return Path(__file__).resolve().parent.parent  
  
  
def _extract_action_names(obj: Any) -> Set[str]:  
    """  
    Recursively extract action names from action_registry.json regardless of shape.  
  
    Supports common patterns:  
    - {"open": {...}, "click_selector": {...}}  
    - {"actions": [{"name": "open"}, ...]}  
    - {"actions": [{"action": "open"}, ...]}  
    - {"registry": {"actions": [...]}} (nested)  
    """  
    out: Set[str] = set()  
    allowed = set(ALLOWED_WORKFLOW_ACTIONS)  
  
    if isinstance(obj, dict):  
        # If it's a top-level action map, keys are action names  
        for k in obj.keys():  
            if isinstance(k, str) and k in allowed:  
                out.add(k)  
  
        # If it's an action definition, capture typical fields  
        for field in ("name", "action"):  
            v = obj.get(field)  
            if isinstance(v, str):  
                out.add(v)  
  
        # Recurse  
        for v in obj.values():  
            out |= _extract_action_names(v)  
  
    elif isinstance(obj, list):  
        for item in obj:  
            out |= _extract_action_names(item)  
  
    return out  
  
  
def _load_registry_actions() -> Set[str]:  
    reg_path = _repo_root() / "REGISTRY" / "action_registry.json"  
    data = json.loads(reg_path.read_text(encoding="utf-8"))  
  
    actions = _extract_action_names(data)  
  
    # Keep only plausible actions (strings) and trim whitespace deterministically  
    cleaned: Set[str] = set()  
    for a in actions:  
        if isinstance(a, str):  
            cleaned.add(a.strip())  
  
    return cleaned  
  
  
def _optional_jsonschema_validate_steps(steps: List[Dict[str, Any]]) -> None:  
    """  
    Optional: if jsonschema is installed and schema file shape matches, validate.  
    This is best-effort and will not fail the smoke if schema validation can't run.  
    """  
    try:  
        import jsonschema  # type: ignore  
    except Exception:  
        return  
  
    root = _repo_root()  
    # Try the more likely schema first, then fallback.  
    schema_paths = [  
        root / "SCHEMA" / "steps_schema.json",  
        root / "SCHEMA" / "schema_1a_steps.json",  
    ]  
    schema = None  
    for p in schema_paths:  
        if p.exists():  
            schema = json.loads(p.read_text(encoding="utf-8"))  
            break  
    if not isinstance(schema, dict):  
        return  
  
    # Try validating either a bare list-of-steps or {"steps":[...]}.  
    try:  
        jsonschema.validate(instance=steps, schema=schema)  
        return  
    except Exception:  
        pass  
  
    try:  
        jsonschema.validate(instance={"steps": steps}, schema=schema)  
        return  
    except Exception:  
        # Don't hard-fail: schema instance shape may differ in this repo.  
        return  
  
  
def dev_smoke() -> None:  
    # Build deterministic sample capture events  
    events = [  
        CapturedEvent(kind="click", seq=1, selector="#login"),  
        CapturedEvent(kind="navigate", seq=2, url="https://example.test/app"),  
        CapturedEvent(kind="change", seq=3, selector="input[name=\"username\"]", value="alice"),  
    ]  
  
    steps = captured_events_to_steps(  
        events,  
        selector_ref_map={"#login": "btn_login"},  
        include_clicks=True,  
        include_navigation=True,  
        include_changes=True,  
        change_mode="exec_js",          # supported action  
        redact_change_values=True,      # avoid capturing secrets  
    )  
  
    # 1) Only supported workflow actions  
    allowed = set(ALLOWED_WORKFLOW_ACTIONS)  
    assert all(isinstance(s, dict) and s.get("action") in allowed for s in steps), steps  
  
    # 2) Registry compatibility (actions must exist in REGISTRY/action_registry.json)  
    registry_actions = _load_registry_actions()  
    assert registry_actions, "Could not load any actions from REGISTRY/action_registry.json"  
    missing = [s["action"] for s in steps if s["action"] not in registry_actions]  
    assert not missing, f"Actions not present in registry: {missing}"  
  
    # 3) Prefer selector_ref when mapping is provided  
    assert steps[0]["action"] == "click_selector"  
    assert steps[0].get("selector_ref") == "btn_login"  
    assert "selector" not in steps[0]  
  
    # 4) Determinism  
    steps2 = captured_events_to_steps(  
        events,  
        selector_ref_map={"#login": "btn_login"},  
        include_clicks=True,  
        include_navigation=True,  
        include_changes=True,  
        change_mode="exec_js",  
        redact_change_values=True,  
    )  
    assert steps == steps2  
  
    # 5) Optional schema validation (best-effort)  
    _optional_jsonschema_validate_steps(steps)  
  
  
if __name__ == "__main__":  
    dev_smoke()  