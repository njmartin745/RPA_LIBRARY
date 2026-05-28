from __future__ import annotations  
  
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple  
  
from WORKFLOW.workflow_2a_capture_actions_to_schema_steps import make_steps_by_actions_1a  
from WORKFLOW.workflow_2b_capture_js_event_recorder import drain_capture_events_from_page_1a, normalize_capture_event_1a  
  
__all__ = [  
    "capture_events_to_action_payloads_1a",  
    "encode_capture_events_to_schema_steps_1a",  
    "drain_capture_schema_steps_from_page_1a",  
    "dev_smoke",  
]  
  
  
def _sorted_events_1a(events: Sequence[Mapping[str, Any]]) -> List[Mapping[str, Any]]:  
    """  
    Deterministic ordering:  
    - primarily by seq (if present and int-coercible)  
    - otherwise by original order (stable)  
    """  
    decorated: List[Tuple[Tuple[int, int], Mapping[str, Any]]] = []  
    for i, ev in enumerate(events):  
        seq_raw = ev.get("seq")  
        seq: Optional[int]  
        try:  
            seq = int(seq_raw) if seq_raw is not None else None  
        except Exception:  
            seq = None  
  
        key = (0, seq) if seq is not None else (1, i)  
        decorated.append((key, ev))  
  
    decorated.sort(key=lambda t: t[0])  
    return [ev for _, ev in decorated]  
  
  
def capture_events_to_action_payloads_1a(  
    events: Sequence[Any],  
    *,  
    selector_ref_map: Optional[Mapping[str, str]] = None,  
    default_secret_ref: str = "CAPTURE_SECRET_1A",  
) -> List[Tuple[str, Dict[str, Any]]]:  
    """  
    Convert captured JS events into (action, payload) tuples suitable for WORKFLOW-2A schema encoding.  
  
    Event kinds supported (from WORKFLOW-2B):  
      - open -> action 'open' payload {'url': ...}  
      - click -> action 'click_selector' payload {'selector' or 'selector_ref': ...}  
      - type_password -> action 'type_selector_secret' payload {'selector' or 'selector_ref': ..., 'secret_ref': ...}  
    """  
    normed: List[Mapping[str, Any]] = []  
    for ev in events:  
        ne = normalize_capture_event_1a(ev)  
        if ne is not None:  
            normed.append(ne)  
  
    normed_sorted = _sorted_events_1a(normed)  
  
    out: List[Tuple[str, Dict[str, Any]]] = []  
    for ev in normed_sorted:  
        kind = ev.get("kind")  
  
        if kind == "open":  
            out.append(("open", {"url": ev["url"]}))  
            continue  
  
        if kind == "click":  
            sel = str(ev["selector"])  
            if selector_ref_map is not None and sel in selector_ref_map:  
                out.append(("click_selector", {"selector_ref": selector_ref_map[sel]}))  
            else:  
                out.append(("click_selector", {"selector": sel}))  
            continue  
  
        if kind == "type_password":  
            sel = str(ev["selector"])  
            payload: Dict[str, Any] = {"secret_ref": default_secret_ref}  
            if selector_ref_map is not None and sel in selector_ref_map:  
                payload["selector_ref"] = selector_ref_map[sel]  
            else:  
                payload["selector"] = sel  
            out.append(("type_selector_secret", payload))  
            continue  
  
        # ignore anything else (normalize already filters)  
    return out  
  
  
def encode_capture_events_to_schema_steps_1a(  
    events: Sequence[Any],  
    *,  
    selector_ref_map: Optional[Mapping[str, str]] = None,  
    default_secret_ref: str = "CAPTURE_SECRET_1A",  
    repo_root: str = ".",  
) -> List[Dict[str, Any]]:  
    """  
    Encode capture events into SCHEMA-1A step dicts using WORKFLOW-2A (schema-aware).  
  
    Returns a list of step dicts that should align with SCHEMA/schema_1a_steps.json  
    (or SCHEMA/steps_schema.json fallback).  
    """  
    items = capture_events_to_action_payloads_1a(  
        events,  
        selector_ref_map=selector_ref_map,  
        default_secret_ref=default_secret_ref,  
    )  
    return make_steps_by_actions_1a(items, repo_root=repo_root)  
  
  
def drain_capture_schema_steps_from_page_1a(  
    driver: Any,  
    *,  
    max_events: int = 250,  
    selector_ref_map: Optional[Mapping[str, str]] = None,  
    default_secret_ref: str = "CAPTURE_SECRET_1A",  
    repo_root: str = ".",  
) -> List[Dict[str, Any]]:  
    """  
    Convenience:  
      - drains raw capture events from the page (WORKFLOW-2B)  
      - converts them to SCHEMA-1A steps (this module + WORKFLOW-2A)  
    """  
    events = drain_capture_events_from_page_1a(driver, max_events=max_events)  
    return encode_capture_events_to_schema_steps_1a(  
        events,  
        selector_ref_map=selector_ref_map,  
        default_secret_ref=default_secret_ref,  
        repo_root=repo_root,  
    )  
  
  
def dev_smoke() -> None:  
    # Use a simple fake-driver like WORKFLOW-2B to avoid real browser dependency.  
    class _FakeDriver:  
        def execute_script(self, script: str) -> Any:  
            # emulate drain returning mixed ordering (seq ensures deterministic sort)  
            return [  
                {"kind": "click", "selector": "#login", "seq": 2},  
                {"kind": "open", "url": "https://example.invalid/", "seq": 1},  
                {"kind": "type_password", "selector": "input:nth-of-type(1)", "seq": 3},  
            ]  
  
    d = _FakeDriver()  
    steps = drain_capture_schema_steps_from_page_1a(  
        d,  
        max_events=10,  
        selector_ref_map={"#login": "cap_login"},  
        default_secret_ref="CAPTURE_SECRET_1A",  
        repo_root=".",  
    )  
  
    assert isinstance(steps, list) and len(steps) == 3  
  
    # Order must be open -> click -> type_password due to seq sort.  
    # We don’t assume the exact discriminator field name; just that action strings are present.  
    actions = []  
    for st in steps:  
        assert isinstance(st, dict)  
        actions.append(next((v for v in st.values() if v in ("open", "click_selector", "type_selector_secret")), None))  
    assert actions == ["open", "click_selector", "type_selector_secret"]  
  
    # selector_ref preference for click when provided  
    click_step = steps[1]  
    assert any(k in click_step for k in ("selector_ref", "selectorRef", "ref"))  
  
    # secret_ref (or schema-alias) must exist on type_selector_secret  
    type_step = steps[2]  
    assert any(k in type_step for k in ("secret_ref", "value_secret_ref", "secret", "secret_key", "secret_name"))  