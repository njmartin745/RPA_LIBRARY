"""  
VAL-1A — UI state validation via selector presence + text checks.  
  
Purpose  
-------  
Reusable validation layer to decide success/failure based on DOM state:  
- element present / visible  
- text equals / contains  
- attribute equals / contains  
  
Public API  
----------  
validate_ui_state(driver, checks, cfg=None) -> dict  
  
`checks` can be:  
- a single dict  
- a list[dict]  
  
Each check supports:  
  - by: "css"|"xpath"|"id"|"name"  (default "css")  
  - value: selector string (required)  
  - expect: "present"|"visible" (default "present")  
  - text_equals: str  
  - text_contains: str  
  - attr: str (attribute name)  
  - attr_equals: str  
  - attr_contains: str  
  - timeout_sec: float (optional; default from cfg EXPLICIT_WAIT/EXPLICIT_WAIT_SEC/WAIT_EXPLICIT_SEC, else 10)  
  
Return contract  
---------------  
{  
  "ok": bool,  
  "passed": int,  
  "failed": int,  
  "details": [ { "ok": bool, "check": {...}, "observed": {...}, "error": str|None } ]  
}  
  
Note on text_contains robustness  
-------------------------------  
Some pages (or network appliances) can rewrite visible copy. To reduce brittleness  
for smoke tests and lightweight validations, `text_contains` uses:  
  1) strict substring match on normalized text  
  2) fallback "partial token match" requiring >= half of the significant tokens  
     (tokens length >= 4) from the expected string to appear in the observed text  
"""  
  
from __future__ import annotations  
  
import re  
from typing import Any, Dict, Iterable, List, Mapping, Optional, Union  
  
from selenium.webdriver.common.by import By  # type: ignore  
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore  
from selenium.webdriver.support import expected_conditions as EC  # type: ignore  
  
__all__ = ["validate_ui_state"]  
  
  
_BY_MAP = {  
    "css": By.CSS_SELECTOR,  
    "css_selector": By.CSS_SELECTOR,  
    "xpath": By.XPATH,  
    "id": By.ID,  
    "name": By.NAME,  
}  
  
  
_WORD_RE = re.compile(r"[A-Za-z0-9]+")  
  
  
def _get_wait(cfg: Optional[Mapping[str, Any]], default: float = 10.0) -> float:  
    if not cfg:  
        return default  
    for k in ("EXPLICIT_WAIT", "EXPLICIT_WAIT_SEC", "WAIT_EXPLICIT_SEC"):  
        v = cfg.get(k)  
        if v is None:  
            continue  
        try:  
            return float(v)  
        except Exception:  
            pass  
    return default  
  
  
def _norm_by(v: Any) -> str:  
    if isinstance(v, str) and v.strip():  
        s = v.strip().lower()  
        return s if s in _BY_MAP else "css"  
    return "css"  
  
  
def _as_checks(checks: Union[Mapping[str, Any], Iterable[Mapping[str, Any]]]) -> List[Dict[str, Any]]:  
    if isinstance(checks, Mapping):  
        return [dict(checks)]  
    return [dict(c) for c in checks]  
  
  
def _wait_for(driver: Any, by: str, value: str, expect: str, timeout: float) -> Any:  
    b = _BY_MAP[_norm_by(by)]  
    if expect == "visible":  
        return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((b, value)))  
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((b, value)))  
  
  
def _norm_text(s: Optional[str]) -> str:  
    if not s:  
        return ""  
    # collapse whitespace + lowercase for stable matching  
    return " ".join(s.split()).strip().lower()  
  
  
def _significant_tokens(s: str) -> List[str]:  
    # keep tokens length >= 4 to avoid matching on "in", "for", etc.  
    toks = [t.lower() for t in _WORD_RE.findall(s or "")]  
    return [t for t in toks if len(t) >= 4]  
  
  
def _contains_with_fallback(expected: str, observed: str) -> bool:  
    """  
    Strict substring contains, then fallback to partial token match:  
    require >= half of significant tokens from expected to appear in observed.  
    """  
    exp_n = _norm_text(expected)  
    obs_n = _norm_text(observed)  
    if not exp_n:  
        return True  
  
    if exp_n in obs_n:  
        return True  
  
    toks = _significant_tokens(expected)  
    if not toks:  
        # if expected only had tiny tokens, fallback is strict failure  
        return False  
  
    obs_tokens = set(_significant_tokens(observed))  
    hits = sum(1 for t in toks if t in obs_tokens)  
    required = max(1, (len(toks) + 1) // 2)  # ceil(half)  
    return hits >= required  
  
  
def validate_ui_state(  
    driver: Any,  
    checks: Union[Mapping[str, Any], Iterable[Mapping[str, Any]]],  
    cfg: Optional[Mapping[str, Any]] = None,  
) -> Dict[str, Any]:  
    check_list = _as_checks(checks)  
    default_wait = _get_wait(cfg, default=10.0)  
  
    details: List[Dict[str, Any]] = []  
    passed = 0  
    failed = 0  
  
    for raw in check_list:  
        check = dict(raw)  
        by = _norm_by(check.get("by", "css"))  
        value = check.get("value") or check.get("selector")  
        expect = (check.get("expect") or "present").strip().lower() if isinstance(check.get("expect"), str) else "present"  
        timeout = default_wait  
        if check.get("timeout_sec") is not None:  
            try:  
                timeout = float(check["timeout_sec"])  
            except Exception:  
                timeout = default_wait  
  
        if not isinstance(value, str) or not value.strip():  
            failed += 1  
            details.append(  
                {  
                    "ok": False,  
                    "check": check,  
                    "observed": {},  
                    "error": "ValueError: check missing required 'value' (selector)",  
                }  
            )  
            continue  
  
        try:  
            el = _wait_for(driver, by, value.strip(), expect, timeout)  
  
            observed: Dict[str, Any] = {}  
            try:  
                observed["text"] = (el.text or "")  
            except Exception:  
                observed["text"] = None  
  
            # Text assertions  
            te = check.get("text_equals")  
            if isinstance(te, str):  
                if _norm_text(observed.get("text") or "") != _norm_text(te):  
                    raise AssertionError(  
                        f"text_equals mismatch (expected={te!r}, got={(observed.get('text') or '')!r})"  
                    )  
  
            tc = check.get("text_contains")  
            if isinstance(tc, str):  
                if not _contains_with_fallback(tc, observed.get("text") or ""):  
                    raise AssertionError(  
                        f"text_contains mismatch (expected substring={tc!r}, got={(observed.get('text') or '')!r})"  
                    )  
  
            # Attribute assertions  
            attr = check.get("attr")  
            if isinstance(attr, str) and attr.strip():  
                try:  
                    observed["attr"] = {attr: el.get_attribute(attr)}  
                except Exception:  
                    observed["attr"] = {attr: None}  
  
                ae = check.get("attr_equals")  
                if isinstance(ae, str):  
                    got = (observed.get("attr") or {}).get(attr)  
                    if got != ae:  
                        raise AssertionError(f"attr_equals mismatch ({attr}) (expected={ae!r}, got={got!r})")  
  
                ac = check.get("attr_contains")  
                if isinstance(ac, str):  
                    got = (observed.get("attr") or {}).get(attr) or ""  
                    if ac not in got:  
                        raise AssertionError(f"attr_contains mismatch ({attr}) (expected substring={ac!r}, got={got!r})")  
  
            passed += 1  
            details.append({"ok": True, "check": check, "observed": observed, "error": None})  
  
        except Exception as e:  
            failed += 1  
            details.append({"ok": False, "check": check, "observed": {}, "error": f"{type(e).__name__}: {e}"})  
  
    return {"ok": failed == 0, "passed": passed, "failed": failed, "details": details}  