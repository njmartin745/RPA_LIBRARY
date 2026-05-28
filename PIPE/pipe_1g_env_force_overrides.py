from __future__ import annotations  
  
from typing import Any, Mapping, MutableMapping, Optional  
  
__all__ = ["apply_env_force_overrides", "dev_smoke"]  
  
_FALSE = {"0", "false", "no", "n", "off"}  
_TRUE = {"1", "true", "yes", "y", "on"} 
  
  
def _parse_bool(v: Optional[str]) -> Optional[bool]:  
    if v is None:  
        return None  
    s = str(v).strip().lower()  
    if not s:  
        return None  
    if s in _FALSE:  
        return False  
    if s in _TRUE:  
        return True  
    return None  
  
  
def apply_env_force_overrides(cfg: MutableMapping[str, Any], *, environ: Mapping[str, str]) -> None:  
    """  
    Force-override selected cfg keys from env, even if cfg already has values.  
    This is specifically to make shell env-vars win over CLI defaults.  
  
    Supported:  
      - LOG_PATH / LOG_JSONL_PATH -> sets BOTH  
      - MANIFEST_PATH / STATE_MANIFEST_PATH -> sets BOTH  
      - STOP_ON_ERROR -> sets STOP_ON_ERROR + stop_on_error + FAIL_FAST  
      - BROWSER -> sets BROWSER + browser  
    """  
    lp = (environ.get("LOG_JSONL_PATH") or "").strip() or (environ.get("LOG_PATH") or "").strip()  
    if lp:  
        cfg["LOG_PATH"] = lp  
        cfg["LOG_JSONL_PATH"] = lp  
  
    mp = (environ.get("STATE_MANIFEST_PATH") or "").strip() or (environ.get("MANIFEST_PATH") or "").strip()  
    if mp:  
        cfg["MANIFEST_PATH"] = mp  
        cfg["STATE_MANIFEST_PATH"] = mp  
  
    soe = _parse_bool(environ.get("STOP_ON_ERROR"))  
    if soe is not None:  
        cfg["STOP_ON_ERROR"] = bool(soe)  
        cfg["stop_on_error"] = bool(soe)  
        cfg["FAIL_FAST"] = bool(soe)  
  
    b = (environ.get("BROWSER") or "").strip()  
    if b:  
        cfg["BROWSER"] = b  
        cfg["browser"] = b  
  
  
def dev_smoke() -> None:  
    cfg: dict[str, Any] = {"LOG_JSONL_PATH": "old.jsonl", "STOP_ON_ERROR": False}  
    apply_env_force_overrides(  
        cfg,  
        environ={"LOG_PATH": "new.jsonl", "STOP_ON_ERROR": "1", "BROWSER": "chrome"},  
    )  
    assert cfg["LOG_JSONL_PATH"] == "new.jsonl"  
    assert cfg["LOG_PATH"] == "new.jsonl"  
    assert cfg["STOP_ON_ERROR"] is True  
    assert cfg["FAIL_FAST"] is True  
    assert cfg["BROWSER"] == "chrome"  