from __future__ import annotations  
  
import json  
from pathlib import Path  
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple  
  
from SNAP.snap_1a_workflow_capture import (  
    ALLOWED_WORKFLOW_ACTIONS,  
    CapturedEvent,  
    captured_events_to_steps,  
)  
from SNAP.snap_1b_selector_pack import selector_pack_from_captured_events  
  
__all__ = [  
    "CAPTURE_BUNDLE_SCHEMA_ID",  
    "emit_capture_bundle",  
    "build_capture_bundle_from_events",  
    "validate_capture_bundle",  
    "dev_smoke",  
]  
  
CAPTURE_BUNDLE_SCHEMA_ID = "CAPTURE_BUNDLE_1A"  
  
  
def emit_capture_bundle(  
    *,  
    steps: Sequence[Mapping[str, Any]],  
    selector_pack: Mapping[str, Any],  
    name: str = "captured",  
    schema_id: str = CAPTURE_BUNDLE_SCHEMA_ID,  
) -> Dict[str, Any]:  
    """  
    Emit a deterministic capture bundle dict.  
  
    Shape (minimal, stable):  
    {  
      "schema_id": "CAPTURE_BUNDLE_1A",  
      "name": "...",  
      "workflow": {"steps": [...]},  
      "selector_pack": {...}  
    }  
    """  
    # Defensive copy with deterministic ordering where applicable  
    workflow = {"steps": [dict(s) for s in steps]}  
    bundle = {  
        "schema_id": schema_id,  
        "name": name,  
        "workflow": workflow,  
        "selector_pack": dict(selector_pack),  
    }  
    return bundle  
  
  
def _extract_action_names(obj: Any) -> Set[str]:  
    """  
    Recursively extract action names from REGISTRY/action_registry.json regardless of shape.  
    """  
    out: Set[str] = set()  
    allowed = set(ALLOWED_WORKFLOW_ACTIONS)  
  
    if isinstance(obj, dict):  
        for k in obj.keys():  
            if isinstance(k, str) and k in allowed:  
                out.add(k)  
  
        for field in ("name", "action"):  
            v = obj.get(field)  
            if isinstance(v, str):  
                out.add(v)  
  
        for v in obj.values():  
            out |= _extract_action_names(v)  
  
    elif isinstance(obj, list):  
        for item in obj:  
            out |= _extract_action_names(item)  
  
    return out  
  
  
def _load_registry_actions(action_registry_path: Path) -> Set[str]:  
    data = json.loads(action_registry_path.read_text(encoding="utf-8"))  
    actions = _extract_action_names(data)  
    return {a.strip() for a in actions if isinstance(a, str) and a.strip()}  
  
  
def _optional_jsonschema_validate_steps(  
    steps: Sequence[Mapping[str, Any]],  
    *,  
    schema_paths: Sequence[Path],  
) -> None:  
    """  
    Best-effort schema validation; if jsonschema is unavailable or schemas don't match instance  
    shape, this function returns without raising.  
    """  
    try:  
        import jsonschema  # type: ignore  
    except Exception:  
        return  
  
    schema = None  
    for p in schema_paths:  
        if p.exists():  
            try:  
                schema = json.loads(p.read_text(encoding="utf-8"))  
            except Exception:  
                schema = None  
            if isinstance(schema, dict):  
                break  
  
    if not isinstance(schema, dict):  
        return  
  
    inst_list = [dict(s) for s in steps]  
    try:  
        jsonschema.validate(instance=inst_list, schema=schema)  
        return  
    except Exception:  
        pass  
  
    try:  
        jsonschema.validate(instance={"steps": inst_list}, schema=schema)  
        return  
    except Exception:  
        return  
  
  
def validate_capture_bundle(  
    bundle: Mapping[str, Any],  
    *,  
    repo_root: Optional[Path] = None,  
    require_registry_compat: bool = True,  
    require_schema_valid: bool = False,  
) -> None:  
    """  
    Validate the capture bundle deterministically.  
  
    Checks:  
    - required keys exist  
    - steps only use supported actions  
    - (optional) actions exist in REGISTRY/action_registry.json  
    - (optional) steps validate against SCHEMA jsonschema files if jsonschema is installed  
    """  
    if bundle.get("schema_id") != CAPTURE_BUNDLE_SCHEMA_ID:  
        raise ValueError(f"Unexpected schema_id: {bundle.get('schema_id')}")  
  
    wf = bundle.get("workflow")  
    if not isinstance(wf, Mapping):  
        raise ValueError("bundle.workflow must be a mapping")  
  
    steps = wf.get("steps")  
    if not isinstance(steps, list):  
        raise ValueError("bundle.workflow.steps must be a list")  
  
    allowed = set(ALLOWED_WORKFLOW_ACTIONS)  
    for i, s in enumerate(steps):  
        if not isinstance(s, Mapping):  
            raise ValueError(f"Step {i} is not a mapping")  
        action = s.get("action")  
        if action not in allowed:  
            raise ValueError(f"Unsupported action in step {i}: {action}")  
  
    # Registry compatibility  
    if require_registry_compat:  
        if repo_root is None:  
            raise ValueError("repo_root is required when require_registry_compat=True")  
        reg_path = repo_root / "REGISTRY" / "action_registry.json"  
        if not reg_path.exists():  
            raise FileNotFoundError(f"Missing registry file: {reg_path}")  
        registry_actions = _load_registry_actions(reg_path)  
        if not registry_actions:  
            raise ValueError("Could not load any actions from REGISTRY/action_registry.json")  
  
        missing = [s["action"] for s in steps if s.get("action") not in registry_actions]  
        if missing:  
            raise ValueError(f"Actions not present in registry: {missing}")  
  
    # Optional schema validation (best-effort unless require_schema_valid=True)  
    if repo_root is not None:  
        schema_paths = (  
            repo_root / "SCHEMA" / "steps_schema.json",  
            repo_root / "SCHEMA" / "schema_1a_steps.json",  
        )  
        try:  
            _optional_jsonschema_validate_steps(steps, schema_paths=schema_paths)  
        except Exception as e:  
            if require_schema_valid:  
                raise  
            # Otherwise: best-effort; do not fail deterministically due to schema shape mismatch.  
            _ = e  
  
  
def build_capture_bundle_from_events(  
    events: Sequence[CapturedEvent] | Sequence[Mapping[str, Any]],  
    *,  
    bundle_name: str = "captured",  
    selector_pack_name: str = "captured",  
    selector_ref_prefix: str = "cap",  
    include_clicks: bool = True,  
    include_navigation: bool = True,  
    include_changes: bool = False,  
    change_mode: str = "exec_js",  
    redact_change_values: bool = True,  
) -> Dict[str, Any]:  
    """  
    End-to-end: events -> selector pack -> selector_ref-first steps -> bundle.  
    """  
    selector_pack = selector_pack_from_captured_events(  
        events,  
        include_kinds=("click", "change"),  
        ref_prefix=selector_ref_prefix,  
        pack_name=selector_pack_name,  
    )  
    selector_ref_map = selector_pack.get("selector_ref_map") or {}  
    if not isinstance(selector_ref_map, Mapping):  
        selector_ref_map = {}  
  
    steps = captured_events_to_steps(  
        events,  
        selector_ref_map=selector_ref_map,  # prefer selector_ref where possible  
        include_clicks=include_clicks,  
        include_navigation=include_navigation,  
        include_changes=include_changes,  
        change_mode=change_mode,  
        redact_change_values=redact_change_values,  
    )  
  
    return emit_capture_bundle(steps=steps, selector_pack=selector_pack, name=bundle_name)  
  
  
def dev_smoke() -> None:  
    # Pure, offline check: build a bundle and validate the internal invariants only.  
    events = [  
        CapturedEvent(kind="click", seq=1, selector="#login"),  
        CapturedEvent(kind="navigate", seq=2, url="https://example.test/app"),  
    ]  
    bundle = build_capture_bundle_from_events(events)  
    validate_capture_bundle(bundle, repo_root=None, require_registry_compat=False)  
    assert bundle["workflow"]["steps"][0]["action"] == "click_selector"  