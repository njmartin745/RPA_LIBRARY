"""  
PIPE-1F: Environment overrides applied to cfg.  
  
Purpose  
-------  
Ensure env vars (notably DRY_RUN) can deterministically override any cfg defaults  
coming from higher layers (CLI/RUN/etc).  
  
Design  
------  
- Additive: does not change behavior unless corresponding env var is present.  
- Writes both canonical + alias keys (e.g., DRY_RUN and dry_run) for compatibility.  
"""  
  
from __future__ import annotations  
  
from typing import Any, Mapping, MutableMapping, Optional  
  
__all__ = ["apply_env_overrides", "dev_smoke"]  
  
  
_FALSE = {"0", "false", "no", "off"}  
_TRUE = {"1", "true", "yes", "on"}  
  
  
def _parse_env_bool(v: Optional[str]) -> Optional[bool]:  
    if v is None:  
        return None  
    s = str(v).strip().lower()  
    if s == "":  
        return None  
    if s in _FALSE:  
        return False  
    if s in _TRUE:  
        return True  
    # Deterministic fallback: any other non-empty value => True  
    return True  
  
  
def apply_env_overrides(cfg: MutableMapping[str, Any], *, environ: Mapping[str, str]) -> None:  
    """  
    Apply supported env overrides onto cfg (in-place).  
  
    Supported env vars:  
      - DRY_RUN: 0/1/true/false...  
      - HEADLESS: 0/1/true/false...  
  
    Notes:  
      - Overrides only when env var is present and non-empty.  
      - Sets both canonical and alias keys: DRY_RUN + dry_run, HEADLESS + headless.  
    """  
    dry = _parse_env_bool(environ.get("DRY_RUN"))  
    if dry is not None:  
        cfg["DRY_RUN"] = bool(dry)  
        cfg["dry_run"] = bool(dry)  
  
    headless = _parse_env_bool(environ.get("HEADLESS"))  
    if headless is not None:  
        cfg["HEADLESS"] = bool(headless)  
        cfg["headless"] = bool(headless)  
  
  
def dev_smoke() -> None:  
    cfg: dict[str, Any] = {}  
  
    apply_env_overrides(cfg, environ={"DRY_RUN": "0"})  
    assert cfg["DRY_RUN"] is False and cfg["dry_run"] is False  
  
    cfg2: dict[str, Any] = {}  
    apply_env_overrides(cfg2, environ={"DRY_RUN": "1"})  
    assert cfg2["DRY_RUN"] is True and cfg2["dry_run"] is True  
  
    cfg3: dict[str, Any] = {}  
    apply_env_overrides(cfg3, environ={"HEADLESS": "true"})  
    assert cfg3["HEADLESS"] is True and cfg3["headless"] is True  