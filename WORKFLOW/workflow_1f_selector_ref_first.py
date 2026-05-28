from __future__ import annotations  
  
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple  
  
__all__ = [  
    "selector_pack_selector_to_ref",  
    "enforce_selector_ref_first_in_steps",  
    "enforce_selector_ref_first_in_workflow",  
    "enforce_selector_ref_first_in_bundle",  
    "dev_smoke",  
]  
  
  
_SELECTOR_ACTIONS = {"click_selector", "wait_for_selector", "type_selector_secret"}  
  
  
def selector_pack_selector_to_ref(selector_pack: Mapping[str, Any]) -> Dict[str, str]:  
    """  
    Build a deterministic mapping: css selector -> selector_ref  
    If multiple refs share the same selector, the lexicographically smallest ref wins.  
    """  
    selectors_obj = selector_pack.get("selectors")  
    if not isinstance(selectors_obj, Mapping):  
        raise ValueError("selector_pack.selectors must be a mapping")  
  
    out: Dict[str, str] = {}  
    for ref, meta in selectors_obj.items():  
        if not isinstance(ref, str) or not ref.strip():  
            continue  
        if not isinstance(meta, Mapping):  
            continue  
  
        sel = meta.get("selector")  
        if not isinstance(sel, str) or not sel.strip():  
            continue  
        sel = sel.strip()  
  
        existing = out.get(sel)  
        if existing is None or ref < existing:  
            out[sel] = ref  
    return out  
  
  
def _enforce_on_step(  
    step: Mapping[str, Any],  
    selector_to_ref: Mapping[str, str],  
    *,  
    drop_selector_when_ref_present: bool,  
    strict: bool,  
) -> Dict[str, Any]:  
    if not isinstance(step, Mapping):  
        raise ValueError("Step must be a mapping")  
  
    new_step: Dict[str, Any] = dict(step)  
    action = new_step.get("action")  
  
    # Recurse into repeat.steps  
    if action == "repeat":  
        nested = new_step.get("steps")  
        if isinstance(nested, list):  
            new_step["steps"] = enforce_selector_ref_first_in_steps(  
                nested,  
                selector_to_ref,  
                drop_selector_when_ref_present=drop_selector_when_ref_present,  
                strict=strict,  
            )  
        return new_step  
  
    # Only operate on selector-based actions (or anything that has selector/selector_ref fields).  
    if action is not None and isinstance(action, str) and action not in _SELECTOR_ACTIONS:  
        # Still allow removing raw selector if selector_ref is present on unexpected actions.  
        if drop_selector_when_ref_present and "selector_ref" in new_step and "selector" in new_step:  
            new_step.pop("selector", None)  
        return new_step  
  
    ref = new_step.get("selector_ref")  
    sel = new_step.get("selector")  
  
    ref_s = ref.strip() if isinstance(ref, str) else ""  
    sel_s = sel.strip() if isinstance(sel, str) else ""  
  
    # If selector_ref already present: prefer it and optionally drop selector  
    if ref_s:  
        new_step["selector_ref"] = ref_s  
        if drop_selector_when_ref_present:  
            new_step.pop("selector", None)  
  
        if strict and sel_s:  
            mapped_ref = selector_to_ref.get(sel_s)  
            if mapped_ref is not None and mapped_ref != ref_s:  
                raise ValueError(f"selector_ref/selector mismatch: {ref_s} vs {mapped_ref} for selector={sel_s}")  
        return new_step  
  
    # If only selector is present: try to convert to selector_ref  
    if sel_s:  
        mapped_ref = selector_to_ref.get(sel_s)  
        if mapped_ref is None:  
            if strict:  
                raise KeyError(f"selector not found in selector pack (cannot enforce selector_ref-first): {sel_s}")  
            return new_step  
  
        new_step["selector_ref"] = mapped_ref  
        if drop_selector_when_ref_present:  
            new_step.pop("selector", None)  
        else:  
            new_step["selector"] = sel_s  
        return new_step  
  
    return new_step  
  
  
def enforce_selector_ref_first_in_steps(  
    steps: Sequence[Mapping[str, Any]],  
    selector_to_ref: Mapping[str, str],  
    *,  
    drop_selector_when_ref_present: bool = True,  
    strict: bool = False,  
) -> List[Dict[str, Any]]:  
    """  
    Enforce selector_ref-first policy on a step list:  
      - If selector_ref exists, optionally drop selector  
      - If selector exists (and selector_ref missing), convert to selector_ref if selector is in pack  
      - Recurse into repeat.steps  
    Pure (no mutation), deterministic.  
    """  
    out: List[Dict[str, Any]] = []  
    for step in steps:  
        out.append(  
            _enforce_on_step(  
                step,  
                selector_to_ref,  
                drop_selector_when_ref_present=drop_selector_when_ref_present,  
                strict=strict,  
            )  
        )  
    return out  
  
  
def enforce_selector_ref_first_in_workflow(  
    workflow: Mapping[str, Any],  
    selector_pack: Mapping[str, Any],  
    *,  
    drop_selector_when_ref_present: bool = True,  
    strict: bool = False,  
) -> Dict[str, Any]:  
    """  
    Apply selector_ref-first policy to a workflow dict shaped like {"steps": [...]}.  
    Returns a new workflow dict.  
    """  
    if not isinstance(workflow, Mapping):  
        raise ValueError("workflow must be a mapping")  
  
    steps = workflow.get("steps")  
    if not isinstance(steps, list):  
        return dict(workflow)  
  
    selector_to_ref = selector_pack_selector_to_ref(selector_pack)  
    out = dict(workflow)  
    out["steps"] = enforce_selector_ref_first_in_steps(  
        steps,  
        selector_to_ref,  
        drop_selector_when_ref_present=drop_selector_when_ref_present,  
        strict=strict,  
    )  
    return out  
  
  
def enforce_selector_ref_first_in_bundle(  
    bundle: Mapping[str, Any],  
    *,  
    drop_selector_when_ref_present: bool = True,  
    strict: bool = False,  
) -> Dict[str, Any]:  
    """  
    Apply selector_ref-first policy to bundle["workflow"] using bundle["selector_pack"].  
    Returns a new bundle dict.  
    """  
    if not isinstance(bundle, Mapping):  
        raise ValueError("bundle must be a mapping")  
  
    wf = bundle.get("workflow")  
    sp = bundle.get("selector_pack")  
    if not isinstance(wf, Mapping):  
        raise ValueError("bundle.workflow must be a mapping")  
    if not isinstance(sp, Mapping):  
        raise ValueError("bundle.selector_pack must be a mapping")  
  
    new_bundle = dict(bundle)  
    new_bundle["workflow"] = enforce_selector_ref_first_in_workflow(  
        wf,  
        sp,  
        drop_selector_when_ref_present=drop_selector_when_ref_present,  
        strict=strict,  
    )  
    return new_bundle  
  
  
def dev_smoke() -> None:  
    bundle = {  
        "schema_id": "CAPTURE_BUNDLE_1A",  
        "name": "x",  
        "workflow": {  
            "steps": [  
                {"action": "click_selector", "selector": "#a"},  
                {"action": "wait_for_selector", "selector_ref": "cap_002", "selector": "#b"},  
                {"action": "repeat", "times": 2, "steps": [{"action": "click_selector", "selector": "#a"}]},  
            ]  
        },  
        "selector_pack": {  
            "schema_id": "SELECTOR_PACK_1A",  
            "name": "x",  
            "selectors": {  
                "cap_001": {"selector": "#a", "type": "css"},  
                "cap_002": {"selector": "#b", "type": "css"},  
            },  
        },  
    }  
  
    out = enforce_selector_ref_first_in_bundle(bundle, drop_selector_when_ref_present=True, strict=True)  
    s0 = out["workflow"]["steps"][0]  
    assert s0["selector_ref"] == "cap_001"  
    assert "selector" not in s0  
  
    s1 = out["workflow"]["steps"][1]  
    assert s1["selector_ref"] == "cap_002"  
    assert "selector" not in s1  
  
    s2 = out["workflow"]["steps"][2]["steps"][0]  
    assert s2["selector_ref"] == "cap_001"  
    assert "selector" not in s2  