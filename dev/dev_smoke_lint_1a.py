# dev_smoke_lint_1a.py  
from __future__ import annotations  
  
import json  
import tempfile  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from LINT.lint_1a_steps_validator import load_steps_schema, validate_steps_data  
  
  
def _dummy_value(expected_type: str, allowed: list | None) -> object:  
    if allowed:  
        return allowed[0]  
    t = (expected_type or "any").lower()  
    if t == "string":  
        return "x"  
    if t == "int":  
        return 1  
    if t == "float":  
        return 1.0  
    if t == "bool":  
        return True  
    if t == "object":  
        return {}  
    if t == "list":  
        return []  
    return "x"  
  
  
def _build_min_valid_step(schema: dict) -> dict:  
    actions = schema["actions"]  
    if not actions:  
        raise AssertionError("No actions found in schema; SCHEMA-1A output missing/empty")  
  
    # pick the "easiest" action: fewest required fields (excluding 'action')  
    best = None  
    best_req_count = 10**9  
    for a, info in actions.items():  
        req = [f for f in (info.required_fields or []) if f != "action"]  
        if len(req) < best_req_count:  
            best = info  
            best_req_count = len(req)  
  
    assert best is not None  
    step = {"action": best.action}  
  
    for f in (best.required_fields or []):  
        if f == "action":  
            continue  
        expected_type = (best.field_types or {}).get(f, "any")  
        allowed = (best.allowed_values or {}).get(f)  
        step[f] = _dummy_value(expected_type, allowed)  
  
    return step  
  
  
def main() -> int:  
    schema = load_steps_schema()  
  
    # 1) generate a minimal valid steps.json (in-memory + temp file for realism)  
    valid_step = _build_min_valid_step(schema)  
    valid_steps_obj = [valid_step]  
  
    report_ok = validate_steps_data(valid_steps_obj, schema)  
    assert report_ok["valid"] is True, f"Expected valid, got: {json.dumps(report_ok, indent=2)}"  
  
    # 2) invalid: unknown action  
    bad_steps_obj = [{"action": "__no_such_action__"}]  
    report_bad = validate_steps_data(bad_steps_obj, schema)  
    assert report_bad["valid"] is False  
    assert report_bad["errors"], "Expected errors for unknown action"  
  
    # 3) invalid: missing required field (only if the chosen action has any required besides action)  
    #    If none, pick any action that has required fields besides action.  
    best = schema["actions"][valid_step["action"]]  
    req_non_action = [f for f in (best.required_fields or []) if f != "action"]  
    if req_non_action:  
        missing = dict(valid_step)  
        missing.pop(req_non_action[0], None)  
        report_missing = validate_steps_data([missing], schema)  
        assert report_missing["valid"] is False  
        assert any(e.get("code") == "REQUIRED" for e in report_missing.get("errors", [])), "Expected REQUIRED error"  
    else:  
        # fallback: find any action with additional required fields  
        for a, info in schema["actions"].items():  
            req = [f for f in (info.required_fields or []) if f != "action"]  
            if req:  
                step2 = {"action": a}  # intentionally missing req fields  
                rep2 = validate_steps_data([step2], schema)  
                assert rep2["valid"] is False  
                break  
  
    # also write a temp steps.json file just to ensure JSON round-trip is fine for local runs  
    with tempfile.TemporaryDirectory() as td:  
        p = Path(td) / "steps.json"  
        p.write_text(json.dumps(valid_steps_obj, indent=2), encoding="utf-8")  
  
    print("PASS: LINT-1A")  
    print(f"  schema: {schema.get('schema_path')}")  
    print(f"  valid_action_used: {valid_step.get('action')}")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  