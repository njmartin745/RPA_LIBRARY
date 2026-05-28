from __future__ import annotations  
  
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple  
  
__all__ = [  
    "selector_pack_ref_to_selector",  
    "materialize_selector_refs_in_steps",  
    "materialize_selector_refs_in_bundle",  
    "dev_smoke",  
]  
  
  
def selector_pack_ref_to_selector(selector_pack: Mapping[str, Any]) -> Dict[str, str]:  
    """  
    Build a mapping of selector_ref -> CSS selector from a selector pack.  
  
    Expected pack shape (as produced by SNAP.snap_1b_selector_pack.build_selector_pack):  
      {"selectors": {"ref": {"selector": "...", "type": "css"}, ...}}  
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
        if isinstance(sel, str) and sel.strip():  
            out[ref] = sel.strip()  
    return out  
  
  
def materialize_selector_refs_in_steps(  
    steps: Sequence[Mapping[str, Any]],  
    ref_to_selector: Mapping[str, str],  
    *,  
    drop_selector_ref: bool = True,  
    require_all: bool = True,  
    verify_if_both_present: bool = True,  
) -> List[Dict[str, Any]]:  
    """  
    Return new steps where any step with `selector_ref` gets a concrete `selector`  
    using `ref_to_selector`.  
  
    - Pure: does not mutate input steps.  
    - Deterministic: preserves step order.  
    """  
    out: List[Dict[str, Any]] = []  
    for i, step in enumerate(steps):  
        if not isinstance(step, Mapping):  
            raise ValueError(f"Step {i} is not a mapping")  
  
        new_step = dict(step)  
        ref = new_step.get("selector_ref")  
        sel = new_step.get("selector")  
  
        if isinstance(ref, str) and ref.strip():  
            ref = ref.strip()  
            resolved = ref_to_selector.get(ref)  
  
            if resolved is None:  
                if require_all:  
                    raise KeyError(f"Step {i} selector_ref not found in selector pack: {ref}")  
            else:  
                if isinstance(sel, str) and sel.strip():  
                    if verify_if_both_present and sel.strip() != resolved:  
                        raise ValueError(  
                            f"Step {i} has selector and selector_ref but they disagree: "  
                            f"{sel.strip()} != {resolved}"  
                        )  
                else:  
                    new_step["selector"] = resolved  
  
            if drop_selector_ref:  
                new_step.pop("selector_ref", None)  
  
        out.append(new_step)  
  
    return out  
  
  
def materialize_selector_refs_in_bundle(  
    bundle: Mapping[str, Any],  
    *,  
    drop_selector_ref: bool = True,  
    require_all: bool = True,  
    verify_if_both_present: bool = True,  
) -> Dict[str, Any]:  
    """  
    Return a new bundle with materialized workflow steps using its embedded selector_pack.  
    """  
    wf = bundle.get("workflow")  
    sp = bundle.get("selector_pack")  
  
    if not isinstance(wf, Mapping):  
        raise ValueError("bundle.workflow must be a mapping")  
    if not isinstance(sp, Mapping):  
        raise ValueError("bundle.selector_pack must be a mapping")  
  
    steps = wf.get("steps")  
    if not isinstance(steps, list):  
        raise ValueError("bundle.workflow.steps must be a list")  
  
    ref_to_sel = selector_pack_ref_to_selector(sp)  
    new_steps = materialize_selector_refs_in_steps(  
        steps,  
        ref_to_sel,  
        drop_selector_ref=drop_selector_ref,  
        require_all=require_all,  
        verify_if_both_present=verify_if_both_present,  
    )  
  
    new_bundle = dict(bundle)  
    new_bundle["workflow"] = dict(wf)  
    new_bundle["workflow"]["steps"] = new_steps  
    return new_bundle  
  
  
def dev_smoke() -> None:  
    steps = [  
        {"action": "click_selector", "selector_ref": "cap_aaa"},  
        {"action": "wait_for_selector", "selector": "#already"},  
    ]  
    sp = {"selectors": {"cap_aaa": {"selector": "#login", "type": "css"}}}  
    b = {"schema_id": "CAPTURE_BUNDLE_1A", "name": "x", "workflow": {"steps": steps}, "selector_pack": sp}  
  
    b2 = materialize_selector_refs_in_bundle(b, drop_selector_ref=True)  
    s0 = b2["workflow"]["steps"][0]  
    assert s0["selector"] == "#login"  
    assert "selector_ref" not in s0  