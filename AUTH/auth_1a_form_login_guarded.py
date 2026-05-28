"""  
AUTH-1A — Standard username/password form login with guarded "already logged in" check.  
  
Public API  
----------  
ensure_logged_in(driver, cfg: dict) -> dict  
login(driver, cfg: dict) -> dict  
    Returns:  
        {  
          "ok": bool,  
          "already_logged_in": bool,  
          "result": dict | None,  
          "error": str | None  
        }  
  
Config (env-friendly)  
---------------------  
LOGIN_URL  
USERNAME / PASSWORD  
USERNAME_SELECTOR / PASSWORD_SELECTOR / SUBMIT_SELECTOR  
USERNAME_BY / PASSWORD_BY / SUBMIT_BY  (css|xpath|id|name; default css)  
  
LOGGED_IN_SELECTOR (preferred guard + post-login success indicator)  
LOGGED_IN_BY (default css)  
POST_LOGIN_SELECTOR / POST_LOGIN_BY (fallback success indicator)  
  
EXPLICIT_WAIT / EXPLICIT_WAIT_SEC / WAIT_EXPLICIT_SEC (default 10)  
STOP_ON_ERROR (unused here; consumed by higher layers)  
"""  
  
from __future__ import annotations  
  
from typing import Any, Dict, Optional, Tuple  
  
from selenium.webdriver.common.by import By  # type: ignore  
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore  
from selenium.webdriver.support import expected_conditions as EC  # type: ignore  
  
__all__ = ["ensure_logged_in", "login"]  
  
  
_BY_MAP = {  
    "css": By.CSS_SELECTOR,  
    "css_selector": By.CSS_SELECTOR,  
    "xpath": By.XPATH,  
    "id": By.ID,  
    "name": By.NAME,  
}  
  
  
def _get_wait(cfg: Dict[str, Any], default: float = 10.0) -> float:  
    for k in ("EXPLICIT_WAIT", "EXPLICIT_WAIT_SEC", "WAIT_EXPLICIT_SEC"):  
        v = cfg.get(k)  
        if v is None:  
            continue  
        try:  
            return float(v)  
        except Exception:  
            pass  
    return default  
  
  
def _get_str(cfg: Dict[str, Any], *keys: str) -> Optional[str]:  
    for k in keys:  
        v = cfg.get(k)  
        if isinstance(v, str) and v.strip():  
            return v.strip()  
    return None  
  
  
def _get_by(cfg: Dict[str, Any], key: str, default: str = "css") -> str:  
    v = cfg.get(key, default)  
    if isinstance(v, str) and v.strip():  
        return v.strip().lower()  
    return default  
  
  
def _as_by(by: str) -> str:  
    b = (by or "css").strip().lower()  
    return b if b in _BY_MAP else "css"  
  
  
def _wait_present(driver: Any, by: str, selector: str, timeout: float):  
    b = _BY_MAP[_as_by(by)]  
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((b, selector)))  
  
  
def _wait_visible(driver: Any, by: str, selector: str, timeout: float):  
    b = _BY_MAP[_as_by(by)]  
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((b, selector)))  
  
  
def _is_logged_in(driver: Any, cfg: Dict[str, Any]) -> bool:  
    sel = _get_str(cfg, "LOGGED_IN_SELECTOR")  
    if not sel:  
        return False  
    by = _get_by(cfg, "LOGGED_IN_BY", "css")  
    try:  
        # short poll: presence is enough for a guard signal  
        _wait_present(driver, by, sel, timeout=0.5)  
        return True  
    except Exception:  
        return False  
  
  
def ensure_logged_in(driver: Any, cfg: Dict[str, Any]) -> Dict[str, Any]:  
    try:  
        wait_sec = _get_wait(cfg, default=10.0)  
  
        # Guard: if already logged in on the current page, do nothing.  
        if _is_logged_in(driver, cfg):  
            return {"ok": True, "already_logged_in": True, "result": {"guard": "logged_in_selector_present"}, "error": None}  
  
        login_url = _get_str(cfg, "LOGIN_URL", "login_url", "URL_LOGIN")  
        if login_url:  
            driver.get(login_url)  
  
        # Guard again after navigation.  
        if _is_logged_in(driver, cfg):  
            return {"ok": True, "already_logged_in": True, "result": {"guard": "logged_in_selector_present_after_nav"}, "error": None}  
  
        username = _get_str(cfg, "USERNAME", "user", "USER")  
        password = _get_str(cfg, "PASSWORD", "pass", "PASS")  
        if username is None or password is None:  
            raise ValueError("Missing USERNAME/PASSWORD in cfg.")  
  
        user_sel = _get_str(cfg, "USERNAME_SELECTOR", "USER_SELECTOR")  
        pass_sel = _get_str(cfg, "PASSWORD_SELECTOR", "PASS_SELECTOR")  
        submit_sel = _get_str(cfg, "SUBMIT_SELECTOR", "LOGIN_BUTTON_SELECTOR", "SUBMIT_BTN_SELECTOR")  
  
        if not user_sel or not pass_sel or not submit_sel:  
            raise ValueError("Missing required selectors: USERNAME_SELECTOR, PASSWORD_SELECTOR, SUBMIT_SELECTOR.")  
  
        user_by = _get_by(cfg, "USERNAME_BY", "css")  
        pass_by = _get_by(cfg, "PASSWORD_BY", "css")  
        submit_by = _get_by(cfg, "SUBMIT_BY", "css")  
  
        user_el = _wait_visible(driver, user_by, user_sel, timeout=wait_sec)  
        pass_el = _wait_visible(driver, pass_by, pass_sel, timeout=wait_sec)  
  
        try:  
            user_el.clear()  
        except Exception:  
            pass  
        user_el.send_keys(username)  
  
        try:  
            pass_el.clear()  
        except Exception:  
            pass  
        pass_el.send_keys(password)  
  
        submit_el = _wait_present(driver, submit_by, submit_sel, timeout=wait_sec)  
        submit_el.click()  
  
        # Success criteria: LOGGED_IN_SELECTOR preferred; otherwise POST_LOGIN_SELECTOR.  
        ok_sel = _get_str(cfg, "LOGGED_IN_SELECTOR") or _get_str(cfg, "POST_LOGIN_SELECTOR")  
        ok_by = _get_by(cfg, "LOGGED_IN_BY", "css") if _get_str(cfg, "LOGGED_IN_SELECTOR") else _get_by(cfg, "POST_LOGIN_BY", "css")  
  
        if ok_sel:  
            _wait_present(driver, ok_by, ok_sel, timeout=wait_sec)  
            return {"ok": True, "already_logged_in": False, "result": {"success_selector": ok_sel}, "error": None}  
  
        # If no success selector configured, consider the click as success (caller can validate later).  
        return {"ok": True, "already_logged_in": False, "result": {"success_selector": None}, "error": None}  
  
    except Exception as e:  
        return {"ok": False, "already_logged_in": False, "result": None, "error": f"{type(e).__name__}: {e}"}  
  
  
def login(driver: Any, cfg: Dict[str, Any]) -> Dict[str, Any]:  
    # Alias for callers that expect "login(...)"  
    return ensure_logged_in(driver, cfg)  