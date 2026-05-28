"""  
AUTH-1B — Session Restore (cookies/local storage) + guarded fallback to AUTH-1A.  
  
Goal  
----  
Speed up runs and reduce auth flakiness by restoring a prior session when possible.  
  
Notes  
-----  
- Filesystem-only for session artifacts.  
- Headless-first; no OS dialogs; no coordinate clicking.  
- Never logs secrets or cookie values.  
- Does NOT duplicate AUTH-1A logic; attempts to call AUTH-1A as fallback.  
  
Config keys  
-----------  
SESSION_RESTORE: bool  
SESSION_COOKIE_PATH: optional explicit cookies.json  
LOGIN_URL / DOMAIN_URL (DOMAIN_URL required for cookie injection)  
POST_LOGIN_SELECTOR: CSS/XPath selector indicating logged-in state  
POST_LOGIN_BY: "css"|"xpath"|... (default "css")  
SESSION_SAVE_ON_SUCCESS: bool (default True)  
SESSION_DIR: optional base directory for sessions (default "./sessions")  
PORTAL: optional portal name (otherwise derived from DOMAIN_URL hostname)  
USER / USERNAME / EMAIL: optional user id for per-user folder  
"""  
  
from __future__ import annotations  
  
import json  
import re  
from pathlib import Path  
from typing import Any, Callable, Dict, Optional  
from urllib.parse import urlparse  
  
from ACT.act_1c_conditional_guards import element_exists  
  
__all__ = [  
    "session_paths",  
    "save_cookies",  
    "load_cookies",  
    "restore_or_login",  
]  
  
  
def _safe_slug(s: str) -> str:  
    s = (s or "").strip().lower()  
    s = re.sub(r"\s+", "-", s)  
    s = re.sub(r"[^a-z0-9._-]+", "", s)  
    s = s.strip("._-")  
    return s or "default"  
  
  
def _hostname(url: str) -> str:  
    try:  
        return urlparse(url).hostname or "unknown"  
    except Exception:  
        return "unknown"  
  
  
def session_paths(cfg: Dict[str, Any]) -> Dict[str, Path]:  
    """  
    Determine where to read/write session artifacts.  
    Returns dict with at least:  
      - cookie_path: Path  
      - root_dir: Path  
      - portal_dir: Path  
      - user_dir: Path  
    """  
    if not isinstance(cfg, dict):  
        raise TypeError(f"cfg must be dict, got {type(cfg).__name__}")  
  
    explicit = cfg.get("SESSION_COOKIE_PATH")  
    if explicit:  
        p = Path(str(explicit))  
        return {  
            "cookie_path": p,  
            "root_dir": p.parent,  
            "portal_dir": p.parent,  
            "user_dir": p.parent,  
        }  
  
    base_dir = Path(str(cfg.get("SESSION_DIR", "./sessions")))  
    domain_url = str(cfg.get("DOMAIN_URL") or cfg.get("LOGIN_URL") or "")  
    portal = _safe_slug(str(cfg.get("PORTAL") or _hostname(domain_url)))  
  
    user = (  
        cfg.get("USER")  
        or cfg.get("USERNAME")  
        or cfg.get("EMAIL")  
        or "default"  
    )  
    user = _safe_slug(str(user))  
  
    portal_dir = base_dir / portal  
    user_dir = portal_dir / user  
    cookie_path = user_dir / "cookies.json"  
  
    return {  
        "cookie_path": cookie_path,  
        "root_dir": base_dir,  
        "portal_dir": portal_dir,  
        "user_dir": user_dir,  
    }  
  
  
def save_cookies(driver: Any, path: Path) -> Path:  
    """  
    Serialize driver.get_cookies() to JSON.  
    Does not print/log cookie values.  
    """  
    p = Path(path)  
    p.parent.mkdir(parents=True, exist_ok=True)  
  
    cookies = []  
    try:  
        cookies = driver.get_cookies() or []  
    except Exception:  
        cookies = []  
  
    # Persist as-is (cookie values are secrets, but file storage is the point).  
    # We simply never log them.  
    p.write_text(json.dumps(cookies, indent=2, sort_keys=True), encoding="utf-8")  
    return p  
  
  
def load_cookies(driver: Any, path: Path, *, domain_url: str) -> bool:  
    """  
    Load cookies from JSON into the driver.  
  
    Required behavior:  
    - navigate to domain_url first (needed for cookie injection)  
    - add cookies one-by-one; ignore incompatible cookies  
    - refresh and return True if any cookies applied  
    """  
    p = Path(path)  
    if not p.exists() or not p.is_file():  
        return False  
  
    if not domain_url or not str(domain_url).strip():  
        raise ValueError("domain_url is required for cookie injection")  
  
    try:  
        driver.get(str(domain_url))  
    except Exception:  
        # If we can't navigate, cookie injection won't work reliably.  
        return False  
  
    try:  
        raw = p.read_text(encoding="utf-8")  
        cookies = json.loads(raw)  
        if not isinstance(cookies, list):  
            return False  
    except Exception:  
        return False  
  
    applied = 0  
    for c in cookies:  
        if not isinstance(c, dict):  
            continue  
        try:  
            # Selenium requires at least name/value.  
            if "name" not in c or "value" not in c:  
                continue  
            driver.add_cookie(c)  
            applied += 1  
        except Exception:  
            # ignore incompatible cookies (domain mismatch, invalid fields, etc.)  
            continue  
  
    if applied > 0:  
        try:  
            driver.refresh()  
        except Exception:  
            pass  
        return True  
  
    return False  
  
  
def _resolve_auth_1a_login() -> Optional[Callable[..., Any]]:  
    """  
    Best-effort resolver for AUTH-1A login entrypoint.  
    We do not duplicate AUTH-1A; we call it if found.  
    """  
    candidates = [  
        ("AUTH.auth_1a_login", ("login", "run_login", "do_login", "auth_login")),  
        ("AUTH.auth_1a", ("login", "run_login", "do_login", "auth_login")),  
    ]  
  
    for mod_name, fn_names in candidates:  
        try:  
            m = __import__(mod_name, fromlist=["*"])  
        except Exception:  
            continue  
        for fn in fn_names:  
            f = getattr(m, fn, None)  
            if callable(f):  
                return f  
  
    # scan AUTH.* for a plausible function name  
    try:  
        import pkgutil  
        import importlib  
  
        pkg = importlib.import_module("AUTH")  
        if hasattr(pkg, "__path__"):  
            for mi in pkgutil.iter_modules(pkg.__path__, prefix=pkg.__name__ + "."):  
                try:  
                    m = importlib.import_module(mi.name)  
                except Exception:  
                    continue  
                for fn in ("login", "run_login", "do_login", "auth_login"):  
                    f = getattr(m, fn, None)  
                    if callable(f):  
                        return f  
    except Exception:  
        pass  
  
    return None  
  
  
def _is_logged_in(driver: Any, cfg: Dict[str, Any]) -> bool:  
    """  
    Logged-in validation using selector indicator.  
  
    Uses ACT-1C element_exists (safe, deterministic). This avoids duplicating NAV/VAL logic.  
    """  
    sel = cfg.get("POST_LOGIN_SELECTOR")  
    if not sel:  
        # If no indicator is provided, we cannot reliably validate.  
        return False  
    by = cfg.get("POST_LOGIN_BY", "css")  
    return element_exists(driver, by, sel)  
  
  
def restore_or_login(driver: Any, cfg: Dict[str, Any]) -> Dict[str, Any]:  
    """  
    If session restore is enabled and cookies exist:  
      - attempt restore (load cookies)  
      - validate logged-in using POST_LOGIN_SELECTOR  
    If not logged in:  
      - call AUTH-1A login (fallback)  
      - validate again  
      - save cookies if SESSION_SAVE_ON_SUCCESS (default True)  
  
    Returns:  
      { "ok": bool, "restored": bool, "logged_in": bool, "cookie_path": str|None }  
    """  
    session_restore = bool(cfg.get("SESSION_RESTORE", False))  
    save_on_success = cfg.get("SESSION_SAVE_ON_SUCCESS", True)  
    cookie_path = session_paths(cfg)["cookie_path"]  
  
    domain_url = str(cfg.get("DOMAIN_URL") or "").strip()  
    login_url = str(cfg.get("LOGIN_URL") or "").strip()  
  
    if not domain_url:  
        # Required for cookie injection; still allow login-only mode if restore disabled.  
        if session_restore:  
            raise ValueError("DOMAIN_URL is required when SESSION_RESTORE is true")  
  
    restored = False  
    logged_in = False  
  
    if session_restore and cookie_path.exists():  
        restored = load_cookies(driver, cookie_path, domain_url=domain_url)  
  
        # Navigate to login_url (or domain) to allow indicator to appear consistently  
        try:  
            if login_url:  
                driver.get(login_url)  
            elif domain_url:  
                driver.get(domain_url)  
        except Exception:  
            pass  
  
        logged_in = _is_logged_in(driver, cfg)  
  
    if not logged_in:  
        # Fallback to AUTH-1A  
        auth_1a = _resolve_auth_1a_login()  
        if auth_1a is None:  
            return {  
                "ok": False,  
                "restored": bool(restored),  
                "logged_in": False,  
                "cookie_path": str(cookie_path) if cookie_path else None,  
                "error": "AUTH-1A login function could not be resolved for fallback.",  
            }  
  
        # Call AUTH-1A with flexible signatures  
        try:  
            try:  
                auth_1a(driver=driver, cfg=cfg)  
            except TypeError:  
                try:  
                    auth_1a(driver, cfg)  
                except TypeError:  
                    auth_1a(driver)  
        except Exception:  
            return {  
                "ok": False,  
                "restored": bool(restored),  
                "logged_in": False,  
                "cookie_path": str(cookie_path) if cookie_path else None,  
                "error": "AUTH-1A login raised an exception (details suppressed).",  
            }  
  
        logged_in = _is_logged_in(driver, cfg)  
  
        if logged_in and bool(save_on_success):  
            try:  
                save_cookies(driver, cookie_path)  
            except Exception:  
                # non-fatal: do not break pipeline  
                pass  
  
    return {  
        "ok": bool(logged_in),  
        "restored": bool(restored),  
        "logged_in": bool(logged_in),  
        "cookie_path": str(cookie_path) if cookie_path else None,  
    }  