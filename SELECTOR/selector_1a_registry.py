# SELECTOR/selector_1a_registry.py  
"""  
SELECTOR-1A — Selector Registry / Resolver  
  
Centralizes UI selectors so workflows can reference stable selector IDs instead of raw selectors.  
  
Loads selectors from: data/selectors.json  
  
Example structure:  
{  
  "login": {  
    "username_input": {"css": "#username", "xpath": "//input[@name='username']"},  
    "password_input": {"css": "#password"},  
    "submit_button": {"css": "button[type='submit']"}  
  }  
}  
  
Public API:  
- load_selectors(...)  
- get_selector(path, ...)  
- resolve_selector(step_dict, ...)  
  
Rules:  
- Pure / side-effect free: no implicit IO at import time.  
- No modifications to ACT/NAV modules.  
"""  
  
from __future__ import annotations  
  
import json  
from pathlib import Path  
from typing import Any, Dict, Optional, Tuple  
  
__all__ = [  
    "load_selectors",  
    "get_selector",  
    "resolve_selector",  
]  
  
  
def _read_text(p: Path) -> str:  
    return p.read_text(encoding="utf-8", errors="replace")  
  
  
def load_selectors(selectors_path: Optional[Path] = None, *, repo_root: Optional[Path] = None) -> Dict[str, Any]:  
    """  
    Loads and returns the selectors registry dict from data/selectors.json.  
  
    No caching by default to keep this module pure and explicit.  
    Callers can cache the returned dict if desired.  
    """  
    if selectors_path is None:  
        if repo_root is None:  
            # best-effort: resolve repo root relative to this file  
            repo_root = Path(__file__).resolve().parents[1]  
        selectors_path = Path(repo_root) / "data" / "selectors.json"  
  
    if not selectors_path.exists():  
        raise FileNotFoundError(f"selectors.json not found: {selectors_path}")  
  
    obj = json.loads(_read_text(selectors_path))  
    if not isinstance(obj, dict):  
        raise ValueError("selectors.json must contain a JSON object at the top level")  
    return obj  
  
  
def _lookup_path(registry: Dict[str, Any], dotted_path: str) -> Any:  
    cur: Any = registry  
    for part in (dotted_path or "").split("."):  
        if not part:  
            raise KeyError("Empty selector path segment")  
        if not isinstance(cur, dict) or part not in cur:  
            raise KeyError(f"Selector path not found: {dotted_path}")  
        cur = cur[part]  
    return cur  
  
  
def get_selector(  
    dotted_path: str,  
    *,  
    registry: Optional[Dict[str, Any]] = None,  
    selectors_path: Optional[Path] = None,  
    repo_root: Optional[Path] = None,  
    prefer: Tuple[str, ...] = ("css", "xpath", "text"),  
) -> Dict[str, str]:  
    """  
    Returns best selector strategy for the given dotted path.  
  
    Output shape:  
      {"strategy": "css", "selector": "#username"}  
  
    Fallback preference: css -> xpath -> text (customizable via prefer).  
    """  
    if registry is None:  
        registry = load_selectors(selectors_path=selectors_path, repo_root=repo_root)  
  
    node = _lookup_path(registry, dotted_path)  
    if not isinstance(node, dict):  
        raise ValueError(f"Selector leaf must be an object/dict: {dotted_path}")  
  
    for strat in prefer:  
        v = node.get(strat)  
        if isinstance(v, str) and v.strip():  
            return {"strategy": strat, "selector": v}  
  
    raise KeyError(f"No usable selector found at '{dotted_path}' (checked: {list(prefer)})")  
  
  
def resolve_selector(  
    step: Dict[str, Any],  
    *,  
    registry: Optional[Dict[str, Any]] = None,  
    selectors_path: Optional[Path] = None,  
    repo_root: Optional[Path] = None,  
    prefer: Tuple[str, ...] = ("css", "xpath", "text"),  
    inplace: bool = False,  
) -> Dict[str, Any]:  
    """  
    If step contains:  
      {"selector_ref": "login.username_input"}  
    then returns a step with:  
      {"selector": "#username", "selector_strategy": "css"}  
    and removes selector_ref.  
  
    By default returns a copy. Set inplace=True to mutate input.  
    """  
    if not isinstance(step, dict):  
        raise TypeError("step must be a dict")  
  
    out = step if inplace else dict(step)  
  
    ref = out.get("selector_ref")  
    if not isinstance(ref, str) or not ref.strip():  
        return out  # nothing to do  
  
    sel = get_selector(  
        ref,  
        registry=registry,  
        selectors_path=selectors_path,  
        repo_root=repo_root,  
        prefer=prefer,  
    )  
    out["selector"] = sel["selector"]  
    out["selector_strategy"] = sel["strategy"]  
    # remove ref to prevent downstream confusion  
    out.pop("selector_ref", None)  
    return out  