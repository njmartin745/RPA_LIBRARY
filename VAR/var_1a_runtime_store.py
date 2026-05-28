"""  
VAR-1A — Runtime Variable Store.  
  
Goal  
----  
Allow steps/modules to store and retrieve runtime variables during execution,  
without side effects outside the provided cfg mapping.  
  
Design  
------  
- Variables live under cfg["_vars"] (a dict).  
- get_var / set_var access that store.  
- render_vars recursively renders strings/dicts/lists/tuples.  
- String interpolation supports ${var_name} patterns anywhere in a string.  
  
Errors  
------  
- Missing variable in render_vars raises KeyError with a clear message.  
"""  
  
from __future__ import annotations  
  
import re  
from typing import Any, Dict, Mapping, MutableMapping, Sequence  
  
__all__ = ["get_var", "set_var", "render_vars"]  
  
_VAR_STORE_KEY = "_vars"  
_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")  
  
  
def _ensure_store(cfg: MutableMapping[str, Any]) -> Dict[str, Any]:  
    store = cfg.get(_VAR_STORE_KEY)  
    if store is None:  
        store = {}  
        cfg[_VAR_STORE_KEY] = store  
    if not isinstance(store, dict):  
        raise TypeError(f"cfg[{_VAR_STORE_KEY!r}] must be a dict, got {type(store).__name__}")  
    return store  
  
  
def set_var(cfg: MutableMapping[str, Any], key: str, value: Any) -> Any:  
    """  
    Set a runtime variable into cfg-backed store. Returns the value.  
    """  
    if not isinstance(cfg, MutableMapping):  
        raise TypeError(f"cfg must be a mutable mapping, got {type(cfg).__name__}")  
    if not isinstance(key, str) or not key.strip():  
        raise ValueError("key must be a non-empty string")  
    store = _ensure_store(cfg)  
    store[key] = value  
    return value  
  
  
def get_var(cfg: Mapping[str, Any], key: str, default: Any = None) -> Any:  
    """  
    Get a runtime variable from cfg-backed store. If missing, returns default.  
    """  
    if not isinstance(cfg, Mapping):  
        raise TypeError(f"cfg must be a mapping, got {type(cfg).__name__}")  
    if not isinstance(key, str) or not key.strip():  
        raise ValueError("key must be a non-empty string")  
    store = cfg.get(_VAR_STORE_KEY, {})  
    if not isinstance(store, dict):  
        raise TypeError(f"cfg[{_VAR_STORE_KEY!r}] must be a dict, got {type(store).__name__}")  
    return store.get(key, default)  
  
  
def _render_str(s: str, cfg: Mapping[str, Any]) -> str:  
    store = cfg.get(_VAR_STORE_KEY, {})  
    if not isinstance(store, dict):  
        raise TypeError(f"cfg[{_VAR_STORE_KEY!r}] must be a dict, got {type(store).__name__}")  
  
    def repl(m: re.Match) -> str:  
        name = m.group(1)  
        if name in store:  
            v = store[name]  
            return "" if v is None else str(v)  
        raise KeyError(f"Missing runtime variable: {name!r} (set via set_var(cfg, {name!r}, value))")  
  
    return _VAR_PATTERN.sub(repl, s)  
  
  
def render_vars(value: Any, cfg: Mapping[str, Any]) -> Any:  
    """  
    Render variables in strings using ${var_name}.  
  
    - str: interpolate variables  
    - dict: render values (and keys if they are strings)  
    - list/tuple: render elements (tuple preserved)  
    - other types: returned unchanged  
    """  
    if isinstance(value, str):  
        return _render_str(value, cfg)  
  
    if isinstance(value, dict):  
        out: Dict[Any, Any] = {}  
        for k, v in value.items():  
            rk = _render_str(k, cfg) if isinstance(k, str) else k  
            out[rk] = render_vars(v, cfg)  
        return out  
  
    if isinstance(value, list):  
        return [render_vars(v, cfg) for v in value]  
  
    if isinstance(value, tuple):  
        return tuple(render_vars(v, cfg) for v in value)  
  
    # Leave other objects untouched (numbers, None, webdriver, etc.)  
    return value  