from __future__ import annotations  
  
import importlib  
import inspect  
import json  
import os  
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from SNAP.snap_1a_workflow_capture import CapturedEvent, captured_events_to_steps  
from SNAP.snap_1b_selector_pack import selector_pack_from_captured_events  
  
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
  
  
def _collect_action_values(obj: Any) -> List[str]:  
    """  
    Recursively collect values for keys named 'action' anywhere in the bundle.  
    """  
    out: List[str] = []  
    if isinstance(obj, dict):  
        for k, v in obj.items():  
            if k == "action" and isinstance(v, str):  
                out.append(v)  
            out.extend(_collect_action_values(v))  
    elif isinstance(obj, list):  
        for v in obj:  
            out.extend(_collect_action_values(v))  
    return out  
  
  
def _canonical_json(obj: Any) -> str:  
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)  
  
  
def _load_json(path: str) -> Dict[str, Any]:  
    with open(path, "r", encoding="utf-8") as f:  
        o = json.load(f)  
    if not isinstance(o, dict):  
        raise TypeError(f"Expected object JSON at {path}")  
    return o  
  
  
def _resolve_bundle_builder(mod: Any) -> Callable[..., Any]:  
    """  
    Resolve a likely capture-bundle builder function from SNAP.snap_1c_capture_bundle  
    without assuming an exact name.  
    """  
    candidates = [  
        # observed in your SNAP/snap_1c_capture_bundle.py  
        "build_capture_bundle_from_events",  
        # fallback common names  
        "capture_bundle_from_captured_events",  
        "capture_bundle_from_events",  
        "build_capture_bundle",  
        "build_capture_bundle_1a",  
        "make_capture_bundle",  
        "make_capture_bundle_1a",  
    ]  
    for name in candidates:  
        fn = getattr(mod, name, None)  
        if callable(fn):  
            return fn  
  
    public_callables = sorted(  
        n for n in dir(mod) if not n.startswith("_") and callable(getattr(mod, n, None))  
    )  
    raise AttributeError(  
        "Could not resolve a capture-bundle builder in SNAP.snap_1c_capture_bundle. "  
        f"Tried {candidates}. Public callables: {public_callables}"  
    )  
  
  
def _call_builder_best_effort(  
    builder: Callable[..., Any],  
    *,  
    events: Sequence[Any],  
    steps: Sequence[Mapping[str, Any]],  
    selector_pack: Mapping[str, Any],  
    selector_ref_map: Optional[Mapping[str, str]],  
    repo_root: str,  
) -> Any:  
    """  
    Call the builder using only kwargs that exist in its signature.  
    Fails deterministically with a helpful message if required params can't be satisfied.  
    """  
    sig = inspect.signature(builder)  
    params = sig.parameters  
  
    kwargs: Dict[str, Any] = {}  
  
    # Events parameter name variations  
    if "events" in params:  
        kwargs["events"] = list(events)  
    if "captured_events" in params:  
        kwargs["captured_events"] = list(events)  
  
    # Inputs often used in bundle builders  
    if "steps" in params:  
        kwargs["steps"] = list(steps)  
    if "selector_pack" in params:  
        kwargs["selector_pack"] = dict(selector_pack)  
    if "selector_ref_map" in params and selector_ref_map is not None:  
        kwargs["selector_ref_map"] = dict(selector_ref_map)  
  
    # Repo root / paths  
    if "repo_root" in params:  
        kwargs["repo_root"] = repo_root  
  
    # Validate we can satisfy required parameters  
    missing_required: List[str] = []  
    for name, p in params.items():  
        if p.default is not inspect._empty:  
            continue  
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):  
            continue  
        if name not in kwargs:  
            missing_required.append(name)  
  
    if missing_required:  
        raise TypeError(  
            f"Cannot call bundle builder {getattr(builder, '__name__', str(builder))} "  
            f"deterministically; missing required params: {missing_required}. "  
            f"Signature: {sig}"  
        )  
  
    return builder(**kwargs)  
  
  
def dev_smoke() -> None:  
    repo_root = "."  
  
    # Deterministic fixture events  
    events = [  
        CapturedEvent(kind="click", seq=1, selector="#login"),  
        CapturedEvent(kind="change", seq=2, selector='input[name="username"]', value="alice"),  
        CapturedEvent(kind="navigate", seq=3, url="https://example.test/app"),  
    ]  
  
    # Build selector pack (also yields selector_ref_map)  
    pack = selector_pack_from_captured_events(  
        events,  
        include_kinds=("click", "change"),  
        ref_prefix="cap",  
        pack_name="captured",  
    )  
    selector_ref_map = pack.get("selector_ref_map")  
    if selector_ref_map is not None and not isinstance(selector_ref_map, dict):  
        raise TypeError("selector_pack_from_captured_events returned non-dict selector_ref_map")  
  
    # Build steps (prefer selector_ref)  
    steps = captured_events_to_steps(  
        events,  
        selector_ref_map=selector_ref_map,  
        include_clicks=True,  
        include_navigation=True,  
        include_changes=False,  
    )  
  
    # Build bundle twice and require deterministic deep equality + canonical JSON equality  
    snap_1c = importlib.import_module("SNAP.snap_1c_capture_bundle")  
    builder = _resolve_bundle_builder(snap_1c)  
  
    bundle1 = _call_builder_best_effort(  
        builder,  
        events=events,  
        steps=steps,  
        selector_pack=pack,  
        selector_ref_map=selector_ref_map,  
        repo_root=repo_root,  
    )  
    bundle2 = _call_builder_best_effort(  
        builder,  
        events=events,  
        steps=steps,  
        selector_pack=pack,  
        selector_ref_map=selector_ref_map,  
        repo_root=repo_root,  
    )  
  
    assert bundle1 == bundle2, "Capture bundle is not deterministic (dict equality mismatch)"  
  
    # Ensure JSON-serializable and stable canonical JSON  
    j1 = _canonical_json(bundle1)  
    j2 = _canonical_json(bundle2)  
    assert j1 == j2, "Capture bundle is not deterministic (canonical JSON mismatch)"  
  
    # Basic bundle sanity: actions remain supported and registry-listed  
    actions = _collect_action_values(bundle1)  
    assert actions, "No 'action' fields found inside capture bundle"  
    assert all(a in _ALLOWED_ACTIONS for a in actions), f"Unsupported actions found in bundle: {actions}"  
  
    reg = _load_json(os.path.join(repo_root, "REGISTRY", "action_registry.json"))  
    registry_strings = set(_walk_strings(reg))  
    for a in actions:  
        assert a in registry_strings, f"Action not found in REGISTRY/action_registry.json (string scan): {a}"  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  