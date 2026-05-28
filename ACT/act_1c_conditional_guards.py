# ACT/act_1c_conditional_guards.py
"""  
ACT-1C — Conditional Step Guards.  
  
Goal  
----  
Allow step execution to branch safely based on UI state without failing the run.  
  
All helpers:  
- Fail safe: return False instead of throwing  
- Never break pipeline (no exceptions propagate)  
  
Primary helpers (required)  
--------------------------  
element_exists(driver, by, selector) -> bool  
text_equals(driver, by, selector, expected) -> bool  
text_contains(driver, by, selector, substring) -> bool  
attribute_equals(driver, by, selector, attr, expected) -> bool  
  
Optional adapter (additive, for ACT engine integration)  
-------------------------------------------------------  
should_run_step(driver, step: Mapping[str, Any]) -> bool  
  
This evaluates guard fields like:  
  - if_exists: ".submit"  (defaults to by="css")  
  - if_text_contains: {"selector": ".dialog-title", "text": "Confirm", "by": "css"}  
"""  
  
from __future__ import annotations  
  
from typing import Any, Mapping, Optional, Tuple  
  
from selenium.webdriver.common.by import By  # type: ignore  
  
__all__ = [  
    "element_exists",  
    "text_equals",  
    "text_contains",  
    "attribute_equals",  
    "should_run_step",  
]  
  
_BY_MAP = {  
    "css": By.CSS_SELECTOR,  
    "css_selector": By.CSS_SELECTOR,  
    "xpath": By.XPATH,  
    "id": By.ID,  
    "name": By.NAME,  
}  
  
  
def _norm_by(by: Any) -> str:  
    if isinstance(by, str) and by.strip():  
        s = by.strip().lower()  
        return s if s in _BY_MAP else "css"  
    return "css"  
  
  
def _norm_text(s: Optional[str]) -> str:  
    if not s:  
        return ""  
    return " ".join(str(s).split()).strip()  
  
  
def _find_first(driver: Any, by: Any, selector: Any):  
    """  
    Fail-safe: returns element or None.  
    """  
    try:  
        sel = str(selector).strip()  
        if not sel:  
            return None  
        b = _BY_MAP[_norm_by(by)]  
        els = driver.find_elements(b, sel)  
        return els[0] if els else None  
    except Exception:  
        return None  
  
  
def element_exists(driver: Any, by: Any, selector: Any) -> bool:  
    try:  
        return _find_first(driver, by, selector) is not None  
    except Exception:  
        return False  
  
  
def text_equals(driver: Any, by: Any, selector: Any, expected: Any) -> bool:  
    try:  
        el = _find_first(driver, by, selector)  
        if el is None:  
            return False  
        got = _norm_text(getattr(el, "text", ""))  
        exp = _norm_text(expected)  
        return got == exp  
    except Exception:  
        return False  
  
  
def text_contains(driver: Any, by: Any, selector: Any, substring: Any) -> bool:  
    try:  
        el = _find_first(driver, by, selector)  
        if el is None:  
            return False  
        got = _norm_text(getattr(el, "text", ""))  
        sub = _norm_text(substring)  
        if not sub:  
            return False  
        return sub in got  
    except Exception:  
        return False  
  
  
def attribute_equals(driver: Any, by: Any, selector: Any, attr: Any, expected: Any) -> bool:  
    try:  
        el = _find_first(driver, by, selector)  
        if el is None:  
            return False  
        a = str(attr).strip()  
        if not a:  
            return False  
        got = el.get_attribute(a)  
        return got == expected  
    except Exception:  
        return False  
  
  
def _parse_guard_target(v: Any) -> Tuple[str, str]:  
    """  
    Returns (by, selector). Defaults to ("css", <string>) when v is a string.  
    Accepts dicts with keys: by, value, selector.  
    """  
    if isinstance(v, str):  
        s = v.strip()  
        return ("css", s)  
  
    if isinstance(v, Mapping):  
        by = v.get("by", "css")  
        sel = v.get("value", None) or v.get("selector", None)  
        return (_norm_by(by), str(sel).strip() if sel is not None else "")  
  
    return ("css", "")  
  
  
def should_run_step(driver: Any, step: Mapping[str, Any]) -> bool:  
    """  
    Evaluate optional guard fields on a step. If guard evaluates False -> skip step.  
  
    Supported guards:  
      - if_exists: str|dict  
      - if_text_equals: {"selector": "...", "text": "...", "by": "css"}  
      - if_text_contains: {"selector": "...", "text": "...", "by": "css"}  
      - if_attr_equals: {"selector": "...", "attr": "...", "value": "...", "by": "css"}  
    """  
    try:  
        if not isinstance(step, Mapping):  
            return True  
  
        # if_exists  
        if "if_exists" in step:  
            by, sel = _parse_guard_target(step.get("if_exists"))  
            return bool(sel) and element_exists(driver, by, sel)  
  
        # if_text_equals  
        if "if_text_equals" in step:  
            g = step.get("if_text_equals")  
            by, sel = _parse_guard_target(g)  
            expected = g.get("text") if isinstance(g, Mapping) else None  
            return bool(sel) and text_equals(driver, by, sel, expected)  
  
        # if_text_contains  
        if "if_text_contains" in step:  
            g = step.get("if_text_contains")  
            by, sel = _parse_guard_target(g)  
            expected = g.get("text") if isinstance(g, Mapping) else None  
            return bool(sel) and text_contains(driver, by, sel, expected)  
  
        # if_attr_equals  
        if "if_attr_equals" in step:  
            g = step.get("if_attr_equals")  
            by, sel = _parse_guard_target(g)  
            if not isinstance(g, Mapping):  
                return True  
            attr = g.get("attr")  
            expected = g.get("value")  
            return bool(sel) and attribute_equals(driver, by, sel, attr, expected)  
  
        return True  
    except Exception:  
        return False  