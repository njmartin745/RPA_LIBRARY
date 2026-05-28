"""  
LOG-1B — Error Taxonomy + Exception Normalization.  
  
Provides a single place to:  
- define error codes  
- classify exceptions into safe, structured payloads  
- produce minimal manifest-friendly fields  
  
Constraints  
-----------  
- Does not modify/integrate with existing modules yet.  
- Must not leak secrets (best-effort redaction).  
"""  
  
from __future__ import annotations  
  
import re  
from typing import Any, Dict  
  
__all__ = [  
    # error codes  
    "AUTH_ERROR",  
    "TIMEOUT",  
    "SELECTOR_NOT_FOUND",  
    "STALE_ELEMENT",  
    "CLICK_INTERCEPTED",  
    "JS_ERROR",  
    "DOWNLOAD_TIMEOUT",  
    "FILESYSTEM_ERROR",  
    "CONFIG_ERROR",  
    "UNKNOWN_ERROR",  
    # api  
    "classify_exception",  
    "format_error_for_manifest",  
]  
  
AUTH_ERROR = "AUTH_ERROR"  
TIMEOUT = "TIMEOUT"  
SELECTOR_NOT_FOUND = "SELECTOR_NOT_FOUND"  
STALE_ELEMENT = "STALE_ELEMENT"  
CLICK_INTERCEPTED = "CLICK_INTERCEPTED"  
JS_ERROR = "JS_ERROR"  
DOWNLOAD_TIMEOUT = "DOWNLOAD_TIMEOUT"  
FILESYSTEM_ERROR = "FILESYSTEM_ERROR"  
CONFIG_ERROR = "CONFIG_ERROR"  
UNKNOWN_ERROR = "UNKNOWN_ERROR"  
  
  
# Optional Selenium exception imports (module must still work without Selenium installed)  
try:  # pragma: no cover  
    from selenium.common.exceptions import (  # type: ignore  
        TimeoutException,  
        NoSuchElementException,  
        StaleElementReferenceException,  
        ElementClickInterceptedException,  
        JavascriptException,  
        WebDriverException,  
    )  
except Exception:  # pragma: no cover  
    TimeoutException = None  
    NoSuchElementException = None  
    StaleElementReferenceException = None  
    ElementClickInterceptedException = None  
    JavascriptException = None  
    WebDriverException = None  
  
  
_RE_KV_SECRET = re.compile(  
    r"(?i)\b(password|passwd|pwd|token|secret|api[_-]?key|auth|authorization)\b\s*[:=]\s*([^\s,;]+)"  
)  
_RE_BEARER = re.compile(r"(?i)\bbearer\s+([A-Za-z0-9\-\._~\+\/]+=*)")  
_RE_COOKIE = re.compile(r"(?i)\bcookie\s*[:=]\s*([^\n\r]+)")  
_RE_LONG_HEX = re.compile(r"\b[0-9a-fA-F]{32,}\b")  
  
  
def _redact_secrets(text: str) -> str:  
    if not text:  
        return text  
  
    t = str(text)  
  
    # key=value style secrets  
    t = _RE_KV_SECRET.sub(lambda m: f"{m.group(1)}=<REDACTED>", t)  
  
    # Authorization: Bearer ...  
    t = _RE_BEARER.sub("Bearer <REDACTED>", t)  
  
    # Cookie headers  
    t = _RE_COOKIE.sub("cookie=<REDACTED>", t)  
  
    # Long hex strings (often tokens)  
    t = _RE_LONG_HEX.sub("<REDACTED>", t)  
  
    # Keep messages reasonably small for logs/manifests  
    if len(t) > 500:  
        t = t[:500] + "…"  
    return t  
  
  
def _exc_name(exc: Exception) -> str:  
    return exc.__class__.__name__ if exc is not None else "Exception"  
  
  
def _msg(exc: Exception) -> str:  
    try:  
        s = str(exc)  
    except Exception:  
        s = ""  
    s = _redact_secrets(s)  
    return s or _exc_name(exc)  
  
  
def _isinstance_optional(exc: Exception, cls: Any) -> bool:  
    return bool(cls is not None and isinstance(exc, cls))  
  
  
def classify_exception(exc: Exception) -> Dict[str, Any]:  
    """  
    Normalize an exception into a safe, structured error payload:  
  
      {  
        "code": "<ERROR_CODE>",  
        "type": "<ExceptionClassName>",  
        "message": "<safe message>",  
        "details": { ... }   # optional, safe  
      }  
  
    Notes:  
    - Uses Selenium exception classes when available; otherwise falls back to class-name matching.  
    - Performs best-effort secret redaction.  
    """  
    etype = _exc_name(exc)  
    message = _msg(exc)  
    name_l = etype.lower()  
    msg_l = message.lower()  
  
    code = UNKNOWN_ERROR  
  
    # --- timeouts ---  
    if isinstance(exc, TimeoutError) or _isinstance_optional(exc, TimeoutException) or "timeout" in name_l:  
        code = DOWNLOAD_TIMEOUT if ("download" in msg_l or "download" in name_l) else TIMEOUT  
  
    # --- filesystem ---  
    elif isinstance(exc, (FileNotFoundError, PermissionError, IsADirectoryError, NotADirectoryError, OSError)):  
        code = FILESYSTEM_ERROR  
  
    # --- config ---  
    elif isinstance(exc, (ValueError, KeyError, TypeError)):  
        # Heuristic: treat these as CONFIG_ERROR unless clearly something else.  
        code = CONFIG_ERROR  
  
    # --- selenium: selector not found ---  
    if code == UNKNOWN_ERROR:  
        if _isinstance_optional(exc, NoSuchElementException) or etype in {"NoSuchElementException"}:  
            code = SELECTOR_NOT_FOUND  
  
    # --- selenium: stale element ---  
    if code == UNKNOWN_ERROR:  
        if _isinstance_optional(exc, StaleElementReferenceException) or etype in {"StaleElementReferenceException"}:  
            code = STALE_ELEMENT  
  
    # --- selenium: click intercepted ---  
    if code == UNKNOWN_ERROR:  
        if _isinstance_optional(exc, ElementClickInterceptedException) or etype in {"ElementClickInterceptedException"}:  
            code = CLICK_INTERCEPTED  
  
    # --- selenium: JS ---  
    if code == UNKNOWN_ERROR:  
        if _isinstance_optional(exc, JavascriptException) or etype in {"JavascriptException"}:  
            code = JS_ERROR  
  
    # --- auth-ish (best-effort) ---  
    if code == UNKNOWN_ERROR:  
        if any(k in msg_l for k in ("unauthorized", "forbidden", "login", "log in", "authentication", "auth failed")):  
            code = AUTH_ERROR  
  
    details: Dict[str, Any] = {}  
    # Keep details minimal and safe.  
    try:  
        if getattr(exc, "args", None):  
            details["args"] = [_redact_secrets(str(a)) for a in exc.args[:3]]  
    except Exception:  
        pass  
  
    # For Selenium WebDriverException, keep a generic marker (no raw stack dumps here).  
    if _isinstance_optional(exc, WebDriverException) or etype.endswith("WebDriverException"):  
        details["selenium"] = True  
  
    out: Dict[str, Any] = {"code": code, "type": etype, "message": message}  
    if details:  
        out["details"] = details  
    return out  
  
  
def format_error_for_manifest(error_dict: Dict[str, Any]) -> Dict[str, Any]:  
    """  
    Return minimal safe fields for manifest row storage.  
    """  
    if not isinstance(error_dict, dict):  
        return {"error_code": UNKNOWN_ERROR, "error_type": "InvalidError", "error_message": "Invalid error payload"}  
  
    code = str(error_dict.get("code") or UNKNOWN_ERROR)  
    etype = str(error_dict.get("type") or "Exception")  
    msg = _redact_secrets(str(error_dict.get("message") or "")) or etype  
  
    return {  
        "error_code": code,  
        "error_type": etype,  
        "error_message": msg,  
    }  