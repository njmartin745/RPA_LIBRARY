"""
WORKFLOW-1E — Workflow Steps Normalizer

Purpose
-------
Convert workflow definitions into a deterministic
canonical representation suitable for validation,
diffing, fingerprinting, bundling, and execution.

This module establishes the canonical workflow
representation used throughout the platform,
ensuring logically equivalent workflows produce
identical structures for review, validation,
deployment, and runtime execution.

Public API
----------
normalize_workflow_steps(...)
normalize_workflow_dict(...)
normalize_capture_bundle_workflow(...)

Dependencies
------------
SNAP-1A

Architecture Position
---------------------
Capture Bundle
        ↓
WORKFLOW-1E
        ↓
VAL-2A
        ↓
BUILD-3B
        ↓
BUILD-3C
        ↓
Runtime

Status
------
Audited

Notes
-----
Normalization Responsibilities:

Workflow
        ↓
Remove None Fields
        ↓
Trim Strings
        ↓
Normalize Repeat Structures
        ↓
Coerce Repeat Counts
        ↓
Validate (Optional)
        ↓
Deterministic Key Ordering

Produces stable workflow representations for
review, fingerprint generation, validation,
and deployment packaging.

Responsibilities
----------------
- Remove None values
- Trim string values
- Normalize repeat structures
- Coerce repeat counts
- Normalize nested workflow trees
- Enforce deterministic key ordering
- Support optional strict validation
- Produce canonical workflow representations

Normalization Rules
-------------------
1. Remove fields with None values
2. Trim leading and trailing whitespace
3. Normalize nested repeat structures
4. Convert repeat count strings to integers
5. Normalize action names
6. Preserve workflow ordering
7. Apply deterministic key ordering

Validation Behavior
-------------------
When strict=True:

- Action names must be valid
- Required fields must exist
- Selector actions must contain either
  selector_ref or selector
- Open actions must contain a URL

When strict=False:

- Normalization proceeds without enforcing
  action validity requirements
- Workflow cleanup remains deterministic
- Validation is deferred to later stages

Deterministic Guarantees
------------------------
The normalization process is:

- Pure (no mutation of inputs)
- Repeatable
- Order preserving
- Deterministic
- Fingerprint friendly

Equivalent workflow definitions produce
equivalent normalized output.

Architecture Notes
------------------
This module is the foundation of workflow
determinism throughout the platform.

Downstream systems including validation,
diffing, fingerprinting, deploy bundle
generation, and runtime execution rely on
the canonical workflow representations
produced here.

Together with WORKFLOW-1F, this module forms
the workflow preparation pipeline:

Capture
    ↓
WORKFLOW-1E
    ↓
WORKFLOW-1F
    ↓
Validation
    ↓
Fingerprinting
    ↓
Deployment
    ↓
Runtime

This module answers a critical architectural
requirement: logically identical workflows
must produce identical deployment artifacts.
"""

from __future__ import annotations  
  
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Set  
  
from SNAP.snap_1a_workflow_capture import ALLOWED_WORKFLOW_ACTIONS  
  
__all__ = [  
    "normalize_workflow_steps",  
    "normalize_workflow_dict",  
    "normalize_capture_bundle_workflow",  
    "dev_smoke",  
]  
  
  
_PREFERRED_KEY_ORDER: Mapping[str, Sequence[str]] = {  
    "open": ("action", "url"),  
    "click_selector": ("action", "selector_ref", "selector"),  
    "wait_for_selector": ("action", "selector_ref", "selector"),  
    "type_selector_secret": (  
        "action",  
        "selector_ref",  
        "selector",  
        "secret_ref",  
        "text_secret_ref",  
        "value_secret_ref",  
    ),  
    "exec_js": ("action", "script", "args"),  
    "exec_js_file": ("action", "path", "file", "args"),  
    "repeat": ("action", "times", "count", "steps"),  
    "log": ("action", "message", "level"),  
    "switch_back_to_main_tab": ("action",),  
}  
  
  
def _strip_string(v: Any) -> Any:  
    if isinstance(v, str):  
        return v.strip()  
    return v  
  
  
def _drop_none_fields(d: Mapping[str, Any]) -> Dict[str, Any]:  
    return {k: v for k, v in d.items() if v is not None}  
  
  
def _coerce_repeat_count(step: MutableMapping[str, Any]) -> None:  
    for k in ("times", "count"):  
        v = step.get(k)  
        if isinstance(v, str):  
            s = v.strip()  
            if s.isdigit():  
                step[k] = int(s)  
  
  
def _ordered_step_dict(step: Mapping[str, Any]) -> Dict[str, Any]:  
    action = step.get("action")  
    preferred = _PREFERRED_KEY_ORDER.get(action, ("action",))  
  
    out: Dict[str, Any] = {}  
  
    # Add preferred keys in order (if present)  
    for k in preferred:  
        if k in step:  
            out[k] = step[k]  
  
    # Add remaining keys sorted for determinism  
    remaining = [k for k in step.keys() if k not in out]  
    for k in sorted(remaining):  
        out[k] = step[k]  
  
    return out  
  
  
def _normalize_step(step: Mapping[str, Any], *, strict: bool, allowed_actions: Set[str]) -> Dict[str, Any]:  
    if not isinstance(step, Mapping):  
        raise ValueError("Step must be a mapping")  
  
    # 1) copy + drop None  
    new_step: Dict[str, Any] = _drop_none_fields(step)  
  
    # 2) strip strings (shallow) + common nested handling for repeat.steps  
    for k, v in list(new_step.items()):  
        if k == "steps" and isinstance(v, list) and new_step.get("action") == "repeat":  
            # normalize nested steps  
            new_step[k] = normalize_workflow_steps(v, strict=strict, allowed_actions=allowed_actions)  
        else:  
            new_step[k] = _strip_string(v)  
  
    # 3) normalize action  
    action = new_step.get("action")  
    if isinstance(action, str):  
        action = action.strip()  
        new_step["action"] = action  
  
    if strict:  
        if not isinstance(action, str) or not action:  
            raise ValueError("Step.action must be a non-empty string")  
  
        if action not in allowed_actions:  
            raise ValueError(f"Unsupported action: {action}")  
  
        # Minimal required-field checks for selector-based steps and open  
        if action in {"click_selector", "wait_for_selector", "type_selector_secret"}:  
            sel_ref = new_step.get("selector_ref")  
            sel = new_step.get("selector")  
            has_ref = isinstance(sel_ref, str) and sel_ref.strip() != ""  
            has_sel = isinstance(sel, str) and sel.strip() != ""  
            if not (has_ref or has_sel):  
                raise ValueError(f"{action} requires selector_ref or selector")  
  
        if action == "open":  
            url = new_step.get("url")  
            if not (isinstance(url, str) and url.strip()):  
                raise ValueError("open requires url")  
  
    # 4) action-specific normalization  
    if new_step.get("action") == "repeat":  
        _coerce_repeat_count(new_step)  
  
    # 5) deterministic key ordering  
    return _ordered_step_dict(new_step)  
  
  
def normalize_workflow_steps(  
    steps: Sequence[Mapping[str, Any]],  
    *,  
    strict: bool = False,  
    allowed_actions: Optional[Set[str]] = None,  
) -> List[Dict[str, Any]]:  
    """  
    Normalize steps for review/diff stability:  
    - drops None fields  
    - strips surrounding whitespace from strings  
    - normalizes repeat nested steps + coerces repeat count strings to int  
    - deterministic key ordering per step  
    - (optional strict) validates action in allowed set and checks minimal required fields  
    """  
    if not isinstance(steps, Sequence):  
        raise ValueError("steps must be a sequence")  
  
    allowed = set(ALLOWED_WORKFLOW_ACTIONS) if allowed_actions is None else set(allowed_actions)  
  
    out: List[Dict[str, Any]] = []  
    for s in steps:  
        out.append(_normalize_step(s, strict=strict, allowed_actions=allowed))  
    return out  
  
  
def normalize_workflow_dict(  
    workflow: Mapping[str, Any],  
    *,  
    strict: bool = False,  
    allowed_actions: Optional[Set[str]] = None,  
) -> Dict[str, Any]:  
    """  
    Normalize a workflow payload shaped like {"steps": [...]}.  
    Preserves other top-level workflow keys but normalizes "steps" if present.  
    """  
    if not isinstance(workflow, Mapping):  
        raise ValueError("workflow must be a mapping")  
  
    out = dict(workflow)  
    steps = out.get("steps")  
    if isinstance(steps, list):  
        out["steps"] = normalize_workflow_steps(steps, strict=strict, allowed_actions=allowed_actions)  
    return out  
  
  
def normalize_capture_bundle_workflow(  
    bundle: Mapping[str, Any],  
    *,  
    strict: bool = False,  
    allowed_actions: Optional[Set[str]] = None,  
) -> Dict[str, Any]:  
    """  
    Normalize bundle["workflow"]["steps"] (without changing selector_ref vs selector policy).  
    Returns a new bundle dict.  
    """  
    if not isinstance(bundle, Mapping):  
        raise ValueError("bundle must be a mapping")  
  
    wf = bundle.get("workflow")  
    if not isinstance(wf, Mapping):  
        raise ValueError("bundle.workflow must be a mapping")  
  
    new_bundle = dict(bundle)  
    new_bundle["workflow"] = normalize_workflow_dict(wf, strict=strict, allowed_actions=allowed_actions)  
    return new_bundle  
  
  
def dev_smoke() -> None:  
    steps = [  
        {"action": " open ", "url": " https://example.test/app "},  
        {"action": "click_selector", "selector_ref": " cap_001 ", "unused": None},  
        {  
            "action": "repeat",  
            "times": " 2 ",  
            "steps": [{"action": "wait_for_selector", "selector": "  #login  "}],  
        },  
    ]  
    norm = normalize_workflow_steps(steps, strict=True)  
    assert norm[0]["action"] == "open"  
    assert norm[0]["url"] == "https://example.test/app"  
    assert norm[1]["selector_ref"] == "cap_001"  
    assert "unused" not in norm[1]  
    assert norm[2]["times"] == 2  
    assert norm[2]["steps"][0]["selector"] == "#login"  