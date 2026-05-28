from __future__ import annotations  
  
import hashlib  
from dataclasses import asdict, is_dataclass  
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple  
  
__all__ = [  
    "SELECTOR_PACK_SCHEMA_ID",  
    "selectors_from_captured_events",  
    "build_selector_ref_map",  
    "build_selector_pack",  
    "selector_pack_from_captured_events",  
    "dev_smoke",  
]  
  
SELECTOR_PACK_SCHEMA_ID = "SELECTOR_PACK_1A"  
  
  
def _event_to_dict(ev: Any) -> Dict[str, Any]:  
    if ev is None:  
        return {}  
    if isinstance(ev, dict):  
        return ev  
    if is_dataclass(ev):  
        return asdict(ev)  
    # Best-effort: objects with attributes  
    out: Dict[str, Any] = {}  
    for k in ("kind", "selector", "seq", "url", "value", "tag"):  
        if hasattr(ev, k):  
            out[k] = getattr(ev, k)  
    return out  
  
  
def _norm_selector(selector: str) -> str:  
    # Keep normalization intentionally conservative (deterministic, low-risk).  
    return selector.strip()  
  
  
def selectors_from_captured_events(  
    events: Sequence[Any],  
    *,  
    include_kinds: Tuple[str, ...] = ("click", "change"),  
) -> List[str]:  
    """  
    Extract a deterministic, sorted unique list of CSS selectors from captured events.  
    """  
    sels: List[str] = []  
    seen = set()  
  
    for ev in events:  
        d = _event_to_dict(ev)  
        kind = d.get("kind")  
        if kind not in include_kinds:  
            continue  
        sel = d.get("selector")  
        if not isinstance(sel, str):  
            continue  
        sel_n = _norm_selector(sel)  
        if not sel_n:  
            continue  
        if sel_n in seen:  
            continue  
        seen.add(sel_n)  
        sels.append(sel_n)  
  
    # Deterministic across runs regardless of capture ordering  
    sels.sort()  
    return sels  
  
  
def _base_ref_for_selector(selector: str, *, ref_prefix: str) -> str:  
    h = hashlib.sha1(selector.encode("utf-8")).hexdigest()[:10]  
    return f"{ref_prefix}_{h}"  
  
  
def build_selector_ref_map(  
    selectors: Sequence[str],  
    *,  
    ref_prefix: str = "cap",  
) -> Dict[str, str]:  
    """  
    Deterministically build a selector->selector_ref mapping.  
  
    Collision handling is deterministic:  
    - refs are assigned in sorted selector order  
    - collisions append _2, _3, ...  
    """  
    out: Dict[str, str] = {}  
    used_refs: Dict[str, str] = {}  # ref -> selector  
  
    for sel in selectors:  
        sel_n = _norm_selector(sel)  
        base = _base_ref_for_selector(sel_n, ref_prefix=ref_prefix)  
        ref = base  
        i = 2  
        while ref in used_refs and used_refs[ref] != sel_n:  
            ref = f"{base}_{i}"  
            i += 1  
  
        used_refs[ref] = sel_n  
        out[sel_n] = ref  
  
    return out  
  
  
def build_selector_pack(  
    selector_ref_map: Mapping[str, str],  
    *,  
    pack_name: str = "captured",  
    schema_id: str = SELECTOR_PACK_SCHEMA_ID,  
) -> Dict[str, Any]:  
    """  
    Emit a deterministic selector pack dict.  
  
    Format (stable, minimal):  
    {  
      "schema_id": "SELECTOR_PACK_1A",  
      "name": "...",  
      "selectors": {  
        "cap_ab12...": {"selector": "#login", "type": "css"}  
      }  
    }  
    """  
    # Deterministic insertion order: sort by selector_ref, then selector  
    items = sorted(  
        ((ref, sel) for sel, ref in selector_ref_map.items()),  
        key=lambda t: (t[0], t[1]),  
    )  
  
    selectors_obj: Dict[str, Any] = {}  
    for ref, sel in items:  
        selectors_obj[ref] = {"selector": sel, "type": "css"}  
  
    return {  
        "schema_id": schema_id,  
        "name": pack_name,  
        "selectors": selectors_obj,  
    }  
  
  
def selector_pack_from_captured_events(  
    events: Sequence[Any],  
    *,  
    include_kinds: Tuple[str, ...] = ("click", "change"),  
    ref_prefix: str = "cap",  
    pack_name: str = "captured",  
) -> Dict[str, Any]:  
    """  
    Convenience: build a selector pack directly from captured events.  
    Includes `selector_ref_map` for immediate use by step generation.  
    """  
    selectors = selectors_from_captured_events(events, include_kinds=include_kinds)  
    ref_map = build_selector_ref_map(selectors, ref_prefix=ref_prefix)  
    pack = build_selector_pack(ref_map, pack_name=pack_name)  
    # Embed mapping for bundling convenience (still deterministic)  
    pack["selector_ref_map"] = dict(sorted(ref_map.items(), key=lambda kv: kv[0]))  
    return pack  
  
  
def dev_smoke() -> None:  
    events = [  
        {"kind": "click", "seq": 1, "selector": "#login"},  
        {"kind": "change", "seq": 2, "selector": "input[name=\"username\"]", "value": "alice"},  
        {"kind": "click", "seq": 3, "selector": "#login"},  # duplicate selector  
    ]  
  
    selectors = selectors_from_captured_events(events)  
    assert selectors == ["#login", "input[name=\"username\"]"]  
  
    ref_map = build_selector_ref_map(selectors, ref_prefix="cap")  
    assert set(ref_map.keys()) == set(selectors)  
    assert all(isinstance(v, str) and v.startswith("cap_") for v in ref_map.values())  
  
    pack = build_selector_pack(ref_map, pack_name="captured")  
    assert pack["schema_id"] == SELECTOR_PACK_SCHEMA_ID  
    assert pack["name"] == "captured"  
    assert "selectors" in pack and isinstance(pack["selectors"], dict)  
  
    # Determinism  
    selectors2 = selectors_from_captured_events(list(reversed(events)))  
    ref_map2 = build_selector_ref_map(selectors2, ref_prefix="cap")  
    pack2 = build_selector_pack(ref_map2, pack_name="captured")  
    assert selectors == selectors2  
    assert ref_map == ref_map2  
    assert pack == pack2  