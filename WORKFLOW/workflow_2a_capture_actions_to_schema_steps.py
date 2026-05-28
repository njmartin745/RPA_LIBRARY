from __future__ import annotations  
  
import json  
import os  
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple  
  
__all__ = [  
    "ALLOWED_CAPTURE_ACTIONS_1A",  
    "load_steps_schema_1a",  
    "find_step_variant_schema_by_action_1a",  
    "infer_discriminator_key_for_action_1a",  
    "make_step_open_1a",  
    "make_step_click_selector_1a",  
    "make_step_wait_for_selector_1a",  
    "make_step_type_selector_secret_1a",  
    "make_step_by_action_1a",  
    "make_steps_by_actions_1a",  
    "dev_smoke",  
]  
  
ALLOWED_CAPTURE_ACTIONS_1A: Tuple[str, ...] = (  
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
  
  
def load_steps_schema_1a(*, repo_root: str = ".") -> Dict[str, Any]:  
    """  
    Load the canonical steps schema JSON from SCHEMA/.  
  
    Deterministic preference order:  
      1) SCHEMA/schema_1a_steps.json  
      2) SCHEMA/steps_schema.json  
  
    Raises FileNotFoundError if neither exists.  
    """  
    candidates = [  
        os.path.join(repo_root, "SCHEMA", "schema_1a_steps.json"),  
        os.path.join(repo_root, "SCHEMA", "steps_schema.json"),  
    ]  
    for p in candidates:  
        if os.path.isfile(p):  
            with open(p, "r", encoding="utf-8") as f:  
                obj = json.load(f)  
            if not isinstance(obj, dict):  
                raise TypeError(f"steps schema must be a JSON object: {p}")  
            return obj  
    raise FileNotFoundError("No steps schema found (expected SCHEMA/schema_1a_steps.json or SCHEMA/steps_schema.json).")  
  
  
def _walk_json(obj: Any) -> Iterable[Any]:  
    stack = [obj]  
    while stack:  
        cur = stack.pop()  
        yield cur  
        if isinstance(cur, dict):  
            # deterministic: push values in key order  
            for k in sorted(cur.keys(), reverse=True):  
                stack.append(cur[k])  
        elif isinstance(cur, list):  
            for v in reversed(cur):  
                stack.append(v)  
  
  
def find_step_variant_schema_by_action_1a(schema: Mapping[str, Any], action: str) -> Optional[Dict[str, Any]]:  
    """  
    Best-effort: locate the schema fragment that corresponds to a particular step action.  
  
    This searches for any dict like:  
      {"properties": {"action": {"const": "<action>"}, ...}, ...}  
    or similar discriminator keys.  
  
    Returns the *containing* dict for the object schema variant, else None.  
    """  
    for node in _walk_json(schema):  
        if not isinstance(node, dict):  
            continue  
        props = node.get("properties")  
        if not isinstance(props, dict):  
            continue  
        for prop_name, prop_schema in props.items():  
            if isinstance(prop_schema, dict) and prop_schema.get("const") == action:  
                return node  
    return None  
  
  
def infer_discriminator_key_for_action_1a(schema: Mapping[str, Any], action: str) -> Optional[str]:  
    """  
    Infer which property name is used to discriminate a step variant (typically 'action').  
  
    Returns None if it cannot be inferred.  
    """  
    variant = find_step_variant_schema_by_action_1a(schema, action)  
    if not isinstance(variant, dict):  
        return None  
    props = variant.get("properties")  
    if not isinstance(props, dict):  
        return None  
    for prop_name, prop_schema in props.items():  
        if isinstance(prop_schema, dict) and prop_schema.get("const") == action:  
            return prop_name  
    return None  
  
  
def _choose_first_present(props: Mapping[str, Any], candidates: Sequence[str]) -> Optional[str]:  
    for c in candidates:  
        if c in props:  
            return c  
    return None  
  
  
def make_step_open_1a(  
    url: str,  
    *,  
    steps_schema: Optional[Mapping[str, Any]] = None,  
    repo_root: str = ".",  
) -> Dict[str, Any]:  
    schema = steps_schema if steps_schema is not None else load_steps_schema_1a(repo_root=repo_root)  
    action = "open"  
  
    variant = find_step_variant_schema_by_action_1a(schema, action) or {}  
    props = variant.get("properties") if isinstance(variant, dict) else {}  
    props = props if isinstance(props, dict) else {}  
  
    disc_key = infer_discriminator_key_for_action_1a(schema, action) or "action"  
    url_key = _choose_first_present(props, ("url", "href", "target_url", "navigate_url")) or "url"  
  
    return {  
        disc_key: action,  
        url_key: url,  
    }  
  
  
def make_step_click_selector_1a(  
    *,  
    selector: Optional[str] = None,  
    selector_ref: Optional[str] = None,  
    steps_schema: Optional[Mapping[str, Any]] = None,  
    repo_root: str = ".",  
) -> Dict[str, Any]:  
    schema = steps_schema if steps_schema is not None else load_steps_schema_1a(repo_root=repo_root)  
    action = "click_selector"  
  
    if (selector is None) == (selector_ref is None):  
        raise ValueError("click_selector requires exactly one of selector or selector_ref")  
  
    variant = find_step_variant_schema_by_action_1a(schema, action) or {}  
    props = variant.get("properties") if isinstance(variant, dict) else {}  
    props = props if isinstance(props, dict) else {}  
  
    disc_key = infer_discriminator_key_for_action_1a(schema, action) or "action"  
    selector_ref_key = _choose_first_present(props, ("selector_ref", "selectorRef", "ref"))  
    selector_key = _choose_first_present(props, ("selector", "css", "xpath"))  
  
    out: Dict[str, Any] = {disc_key: action}  
    if selector_ref is not None:  
        out[selector_ref_key or "selector_ref"] = selector_ref  
    else:  
        out[selector_key or "selector"] = selector  
    return out  
  
  
def make_step_wait_for_selector_1a(  
    *,  
    selector: Optional[str] = None,  
    selector_ref: Optional[str] = None,  
    steps_schema: Optional[Mapping[str, Any]] = None,  
    repo_root: str = ".",  
) -> Dict[str, Any]:  
    schema = steps_schema if steps_schema is not None else load_steps_schema_1a(repo_root=repo_root)  
    action = "wait_for_selector"  
  
    if (selector is None) == (selector_ref is None):  
        raise ValueError("wait_for_selector requires exactly one of selector or selector_ref")  
  
    variant = find_step_variant_schema_by_action_1a(schema, action) or {}  
    props = variant.get("properties") if isinstance(variant, dict) else {}  
    props = props if isinstance(props, dict) else {}  
  
    disc_key = infer_discriminator_key_for_action_1a(schema, action) or "action"  
    selector_ref_key = _choose_first_present(props, ("selector_ref", "selectorRef", "ref"))  
    selector_key = _choose_first_present(props, ("selector", "css", "xpath"))  
  
    out: Dict[str, Any] = {disc_key: action}  
    if selector_ref is not None:  
        out[selector_ref_key or "selector_ref"] = selector_ref  
    else:  
        out[selector_key or "selector"] = selector  
    return out  
  
  
def make_step_type_selector_secret_1a(  
    *,  
    selector: Optional[str] = None,  
    selector_ref: Optional[str] = None,  
    secret_ref: str,  
    steps_schema: Optional[Mapping[str, Any]] = None,  
    repo_root: str = ".",  
) -> Dict[str, Any]:  
    """  
    Produces a type_selector_secret step. Field names are inferred from the schema when possible.  
  
    Note: this does not create/provision the secret; it only records a secret reference.  
    """  
    schema = steps_schema if steps_schema is not None else load_steps_schema_1a(repo_root=repo_root)  
    action = "type_selector_secret"  
  
    if (selector is None) == (selector_ref is None):  
        raise ValueError("type_selector_secret requires exactly one of selector or selector_ref")  
  
    variant = find_step_variant_schema_by_action_1a(schema, action) or {}  
    props = variant.get("properties") if isinstance(variant, dict) else {}  
    props = props if isinstance(props, dict) else {}  
  
    disc_key = infer_discriminator_key_for_action_1a(schema, action) or "action"  
    selector_ref_key = _choose_first_present(props, ("selector_ref", "selectorRef", "ref"))  
    selector_key = _choose_first_present(props, ("selector", "css", "xpath"))  
    secret_key = _choose_first_present(props, ("secret_ref", "value_secret_ref", "secret", "secret_key", "secret_name")) or "secret_ref"  
  
    out: Dict[str, Any] = {disc_key: action, secret_key: secret_ref}  
    if selector_ref is not None:  
        out[selector_ref_key or "selector_ref"] = selector_ref  
    else:  
        out[selector_key or "selector"] = selector  
    return out  
  
  
def make_step_by_action_1a(action: str, payload: Mapping[str, Any], *, repo_root: str = ".") -> Dict[str, Any]:  
    """  
    Generic helper for capture pipelines that already chose an action name.  
    """  
    if action not in ALLOWED_CAPTURE_ACTIONS_1A:  
        raise ValueError(f"Unsupported capture action: {action}")  
  
    schema = load_steps_schema_1a(repo_root=repo_root)  
  
    if action == "open":  
        return make_step_open_1a(str(payload["url"]), steps_schema=schema, repo_root=repo_root)  
  
    if action == "click_selector":  
        return make_step_click_selector_1a(  
            selector=payload.get("selector"),  
            selector_ref=payload.get("selector_ref"),  
            steps_schema=schema,  
            repo_root=repo_root,  
        )  
  
    if action == "wait_for_selector":  
        return make_step_wait_for_selector_1a(  
            selector=payload.get("selector"),  
            selector_ref=payload.get("selector_ref"),  
            steps_schema=schema,  
            repo_root=repo_root,  
        )  
  
    if action == "type_selector_secret":  
        return make_step_type_selector_secret_1a(  
            selector=payload.get("selector"),  
            selector_ref=payload.get("selector_ref"),  
            secret_ref=str(payload["secret_ref"]),  
            steps_schema=schema,  
            repo_root=repo_root,  
        )  
  
    # For remaining allowed actions, the schema shape varies; keep capture minimal:  
    # pass through with discriminator set to 'action' by default.  
    disc_key = infer_discriminator_key_for_action_1a(schema, action) or "action"  
    out = {disc_key: action}  
    out.update(dict(payload))  
    return out  
  
  
def make_steps_by_actions_1a(items: Sequence[Tuple[str, Mapping[str, Any]]], *, repo_root: str = ".") -> List[Dict[str, Any]]:  
    return [make_step_by_action_1a(a, p, repo_root=repo_root) for (a, p) in items]  
  
  
def dev_smoke() -> None:  
    schema = load_steps_schema_1a(repo_root=".")  
  
    s1 = make_step_open_1a("about:blank", steps_schema=schema)  
    assert isinstance(s1, dict)  
  
    s2 = make_step_wait_for_selector_1a(selector="body", steps_schema=schema)  
    assert isinstance(s2, dict)  
  
    s3 = make_step_click_selector_1a(selector="body", steps_schema=schema)  
    assert isinstance(s3, dict)  
  
    # This should work even if schema uses different secret field names (we infer where possible).  
    s4 = make_step_type_selector_secret_1a(selector="body", secret_ref="DEV_SECRET_REF", steps_schema=schema)  
    assert isinstance(s4, dict)  
  
    # Sanity: discriminator inferred (or default) produces correct action string somewhere in the dict.  
    assert any(v == "open" for v in s1.values())  
    assert any(v == "wait_for_selector" for v in s2.values())  
    assert any(v == "click_selector" for v in s3.values())  
    assert any(v == "type_selector_secret" for v in s4.values())  