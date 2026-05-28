from __future__ import annotations  
  
import json  
import os  
from typing import Any, Dict, Iterable, List, Mapping, Set  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from SNAP.snap_1a_workflow_capture import CapturedEvent, captured_events_to_steps  
from SNAP.snap_1b_selector_pack import build_selector_ref_map, selectors_from_captured_events  
  
__all__ = ["dev_smoke"]  
  
  
_ALLOWED_ACTIONS: Set[str] = {  
    "open",  
    "click_selector",  
    "type_selector_secret",  
    "wait_for_selector",  
    "exec_js",  
    "exec_js_file",  
    "repeat",  
    "log",  
    "switch_back_to_main_tab",  
}  
  
  
def _walk_strings(obj: Any) -> Iterable[str]:  
    """  
    Deterministically extract all strings from JSON-like structures,  
    including dict keys and string values (recursive).  
    """  
    if isinstance(obj, dict):  
        for k in sorted(obj.keys()):  
            if isinstance(k, str):  
                yield k  
            yield from _walk_strings(obj[k])  
    elif isinstance(obj, list):  
        for v in obj:  
            yield from _walk_strings(v)  
    elif isinstance(obj, str):  
        yield obj  
  
  
def _load_json(path: str) -> Dict[str, Any]:  
    with open(path, "r", encoding="utf-8") as f:  
        obj = json.load(f)  
    if not isinstance(obj, dict):  
        raise TypeError(f"Expected JSON object at {path}")  
    return obj  
  
  
def _load_steps_schema(repo_root: str = ".") -> Dict[str, Any]:  
    p1 = os.path.join(repo_root, "SCHEMA", "schema_1a_steps.json")  
    p2 = os.path.join(repo_root, "SCHEMA", "steps_schema.json")  
    if os.path.isfile(p1):  
        return _load_json(p1)  
    if os.path.isfile(p2):  
        return _load_json(p2)  
    raise FileNotFoundError("No steps schema found in SCHEMA/ (schema_1a_steps.json or steps_schema.json).")  
  
  
def _validate_steps_with_jsonschema(steps: List[Dict[str, Any]], schema: Mapping[str, Any]) -> None:  
    """  
    Optional schema validation if jsonschema is installed.  
    Tries list-validation if schema looks like an array schema, else per-step validation.  
    """  
    try:  
        import jsonschema  # type: ignore  
    except Exception:  
        return  
  
    if isinstance(schema, Mapping) and schema.get("type") == "array" and "items" in schema:  
        jsonschema.validate(instance=steps, schema=schema)  
        return  
  
    # Fallback: validate each step against the schema (works for many oneOf/anyOf forms too)  
    for st in steps:  
        jsonschema.validate(instance=st, schema=schema)  
  
  
def dev_smoke() -> None:  
    repo_root = "."  
  
    # Minimal deterministic captured events -> steps  
    events = [  
        CapturedEvent(kind="click", seq=1, selector="#login"),  
        CapturedEvent(kind="change", seq=2, selector='input[name="username"]', value="alice"),  
        CapturedEvent(kind="navigate", seq=3, url="https://example.test/app"),  
    ]  
  
    selectors = selectors_from_captured_events(events, include_kinds=("click", "change"))  
    selector_ref_map = build_selector_ref_map(selectors, ref_prefix="cap")  
  
    steps = captured_events_to_steps(  
        events,  
        selector_ref_map=selector_ref_map,  
        include_clicks=True,  
        include_navigation=True,  
        include_changes=False,  
    )  
  
    assert isinstance(steps, list) and steps, "No steps produced from capture events"  
    for st in steps:  
        assert isinstance(st, dict), "Step is not a dict"  
        assert "action" in st and isinstance(st["action"], str), "Step missing string 'action' field"  
  
    # Enforce supported action set (framework constraint)  
    step_actions = [st["action"] for st in steps]  
    assert all(a in _ALLOWED_ACTIONS for a in step_actions), f"Unsupported actions found: {step_actions}"  
  
    # Enforce action exists in action registry (best-effort: string presence anywhere in registry JSON)  
    reg = _load_json(os.path.join(repo_root, "REGISTRY", "action_registry.json"))  
    registry_strings = set(_walk_strings(reg))  
    for a in step_actions:  
        assert a in registry_strings, f"Action not found in REGISTRY/action_registry.json (string scan): {a}"  
  
    # Prefer selector_ref when mapping is provided (at least for the click)  
    click_steps = [st for st in steps if st.get("action") == "click_selector"]  
    assert click_steps, "Expected at least one click_selector step"  
    cs = click_steps[0]  
    assert "selector_ref" in cs, "click_selector did not prefer selector_ref with a provided selector_ref_map"  
    assert "selector" not in cs, "click_selector unexpectedly included raw selector alongside selector_ref"  
  
    # Optional JSON Schema validation (if jsonschema installed)  
    schema = _load_steps_schema(repo_root=repo_root)  
    _validate_steps_with_jsonschema(steps, schema)  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  