from __future__ import annotations  
  
import difflib  
import json  
from typing import Any, Dict, List, Mapping, Sequence, Tuple  
  
__all__ = [  
    "canonical_json_dumps",  
    "compute_json_changes",  
    "render_unified_json_diff",  
    "diff_capture_edit",  
    "dev_smoke",  
]  
  
  
def canonical_json_dumps(obj: Any, *, indent: int = 2) -> str:  
    """  
    Deterministic JSON serialization for diffing:  
      - sort_keys=True  
      - stable indentation  
      - no trailing spaces  
      - newline-terminated  
    """  
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=indent)  
    if not s.endswith("\n"):  
        s += "\n"  
    return s  
  
  
def _json_pointer_escape(token: str) -> str:  
    return token.replace("~", "~0").replace("/", "~1")  
  
  
def _join_path(path: str, token: str) -> str:  
    if path == "":  
        return "/" + _json_pointer_escape(token)  
    return path + "/" + _json_pointer_escape(token)  
  
  
def _is_scalar(x: Any) -> bool:  
    return x is None or isinstance(x, (str, int, float, bool))  
  
  
def compute_json_changes(before: Any, after: Any) -> List[Dict[str, Any]]:  
    """  
    Compute deterministic, JSON-pointer-addressed changes between two JSON-like objects.  
  
    Output ops:  
      - add:    {"op":"add","path":"/a/b","new":...}  
      - remove: {"op":"remove","path":"/a/b","old":...}  
      - replace:{"op":"replace","path":"/a/b","old":...,"new":...}  
  
    Determinism:  
      - dict keys traversed in sorted order  
      - list indices traversed in increasing order  
    """  
    changes: List[Dict[str, Any]] = []  
  
    def walk(path: str, a: Any, b: Any) -> None:  
        if a is b:  
            return  
  
        # Scalar or type mismatch => replace  
        if _is_scalar(a) and _is_scalar(b):  
            if a != b:  
                changes.append({"op": "replace", "path": path or "/", "old": a, "new": b})  
            return  
  
        if type(a) is not type(b):  
            changes.append({"op": "replace", "path": path or "/", "old": a, "new": b})  
            return  
  
        # dict  
        if isinstance(a, Mapping):  
            a_keys = set(k for k in a.keys() if isinstance(k, str))  
            b_keys = set(k for k in b.keys() if isinstance(k, str))  
  
            for k in sorted(a_keys - b_keys):  
                p = _join_path(path, k)  
                changes.append({"op": "remove", "path": p, "old": a[k]})  
  
            for k in sorted(b_keys - a_keys):  
                p = _join_path(path, k)  
                changes.append({"op": "add", "path": p, "new": b[k]})  
  
            for k in sorted(a_keys & b_keys):  
                walk(_join_path(path, k), a[k], b[k])  
            return  
  
        # list  
        if isinstance(a, list):  
            common = min(len(a), len(b))  
            for i in range(common):  
                walk(_join_path(path, str(i)), a[i], b[i])  
  
            # removals from end (stable)  
            for i in range(len(a) - 1, len(b) - 1, -1):  
                p = _join_path(path, str(i))  
                changes.append({"op": "remove", "path": p, "old": a[i]})  
  
            # additions from end (stable)  
            for i in range(common, len(b)):  
                p = _join_path(path, str(i))  
                changes.append({"op": "add", "path": p, "new": b[i]})  
            return  
  
        # Fallback: replace unknown JSON-ish types deterministically  
        if a != b:  
            changes.append({"op": "replace", "path": path or "/", "old": a, "new": b})  
  
    walk("", before, after)  
    return changes  
  
  
def render_unified_json_diff(  
    before: Any,  
    after: Any,  
    *,  
    fromfile: str = "before.json",  
    tofile: str = "after.json",  
    indent: int = 2,  
) -> str:  
    """  
    Deterministic unified diff of canonical JSON renderings.  
    """  
    a = canonical_json_dumps(before, indent=indent).splitlines(keepends=True)  
    b = canonical_json_dumps(after, indent=indent).splitlines(keepends=True)  
  
    diff_lines = difflib.unified_diff(a, b, fromfile=fromfile, tofile=tofile, lineterm="\n")  
    return "".join(diff_lines)  
  
  
def diff_capture_edit(  
    before_bundle: Mapping[str, Any],  
    after_bundle: Mapping[str, Any],  
    *,  
    include_unified: bool = True,  
) -> Dict[str, Any]:  
    """  
    Convenience wrapper for capture bundle edits.  
    Returns a deterministic diff payload (review-friendly).  
    """  
    changes = compute_json_changes(before_bundle, after_bundle)  
    out: Dict[str, Any] = {  
        "schema_id": "CAPTURE_EDIT_DIFF_1A",  
        "changes": changes,  
        "counts": {  
            "add": sum(1 for c in changes if c.get("op") == "add"),  
            "remove": sum(1 for c in changes if c.get("op") == "remove"),  
            "replace": sum(1 for c in changes if c.get("op") == "replace"),  
            "total": len(changes),  
        },  
    }  
    if include_unified:  
        out["unified_diff"] = render_unified_json_diff(before_bundle, after_bundle)  
    return out  
  
  
def dev_smoke() -> None:  
    before = {  
        "schema_id": "CAPTURE_BUNDLE_1A",  
        "name": "cap",  
        "workflow": {"steps": [{"action": "open", "url": "https://a"}, {"action": "log", "message": "x"}]},  
        "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "cap", "selectors": {"cap_1": {"selector": "#a"}}},  
    }  
    after = {  
        "schema_id": "CAPTURE_BUNDLE_1A",  
        "name": "cap",  
        "workflow": {"steps": [{"action": "open", "url": "https://b"}, {"action": "log", "message": "x"}]},  
        "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "cap", "selectors": {"cap_1": {"selector": "#a"}}},  
    }  
  
    d = diff_capture_edit(before, after, include_unified=True)  
    assert d["schema_id"] == "CAPTURE_EDIT_DIFF_1A"  
    assert d["counts"]["replace"] == 1  
    assert any(c["path"].endswith("/workflow/steps/0/url") for c in d["changes"])  
    assert isinstance(d["unified_diff"], str) and "--- before.json" in d["unified_diff"]  