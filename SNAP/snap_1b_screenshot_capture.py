"""  
SNAP-1B — Screenshot capture (10.1.2)  
  
Single responsibility:  
- Capture a screenshot from a selenium-like driver (best-effort).  
- Return either PNG bytes, base64 PNG, or a small JSON-serializable payload.  
  
This module does NOT persist artifacts to disk (10.1.3) and does NOT attempt  
to capture DOM/URL context (10.1.1).  
"""  
  
from __future__ import annotations  
  
import base64  
import datetime as _dt  
from typing import Any  
  
__all__ = [  
    "capture_screenshot_png_bytes",  
    "capture_screenshot_b64",  
    "capture_screenshot_payload",  
    "dev_smoke",  
]  
  
  
def _utc_now_iso() -> str:  
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()  
  
  
def capture_screenshot_png_bytes(driver: Any) -> bytes | None:  
    """  
    Best-effort capture of screenshot as PNG bytes.  
  
    Tries (in order):  
    - driver.get_screenshot_as_png()  -> bytes  
    - driver.get_screenshot_as_base64() -> decode to bytes  
    Returns None if not available or fails.  
    """  
    try:  
        fn = getattr(driver, "get_screenshot_as_png", None)  
        if callable(fn):  
            data = fn()  
            if isinstance(data, (bytes, bytearray)):  
                return bytes(data)  
            return None  
    except Exception:  
        # Fall through to base64 attempt  
        pass  
  
    try:  
        fn = getattr(driver, "get_screenshot_as_base64", None)  
        if callable(fn):  
            b64 = fn()  
            if isinstance(b64, str) and b64:  
                return base64.b64decode(b64.encode("ascii"))  
            return None  
    except Exception:  
        return None  
  
    return None  
  
  
def capture_screenshot_b64(driver: Any) -> str | None:  
    """  
    Best-effort capture of screenshot as base64-encoded PNG (ASCII str).  
  
    Tries (in order):  
    - driver.get_screenshot_as_base64() -> str  
    - driver.get_screenshot_as_png() -> bytes -> base64  
    Returns None if not available or fails.  
    """  
    try:  
        fn = getattr(driver, "get_screenshot_as_base64", None)  
        if callable(fn):  
            b64 = fn()  
            if isinstance(b64, str) and b64:  
                # Normalize to ASCII-only string  
                b64.encode("ascii")  
                return b64  
            return None  
    except Exception:  
        # Fall back to PNG attempt  
        pass  
  
    png = capture_screenshot_png_bytes(driver)  
    if not png:  
        return None  
    return base64.b64encode(png).decode("ascii")  
  
  
def capture_screenshot_payload(  
    *,  
    driver: Any,  
    captured_at_utc: str | None = None,  
    label: str | None = None,  
) -> dict[str, Any]:  
    """  
    Return a JSON-serializable payload describing a screenshot capture attempt.  
  
    Does not write to disk; intended to be embedded in a broader failure snapshot.  
    """  
    if captured_at_utc is None:  
        captured_at_utc = _utc_now_iso()  
  
    b64 = capture_screenshot_b64(driver)  
    if b64 is None:  
        return {  
            "schema": "SNAP-1B",  
            "captured_at_utc": captured_at_utc,  
            "label": label,  
            "ok": False,  
            "content_type": "image/png",  
            "screenshot_b64": None,  
            "error": {"class": "ScreenshotUnavailable", "message": "Driver did not provide screenshot data."},  
        }  
  
    # length info helps consumers without needing to decode  
    return {  
        "schema": "SNAP-1B",  
        "captured_at_utc": captured_at_utc,  
        "label": label,  
        "ok": True,  
        "content_type": "image/png",  
        "screenshot_b64": b64,  
        "bytes_len": len(base64.b64decode(b64.encode("ascii"))),  
    }  
  
  
def dev_smoke() -> None:  
    # Case 1: PNG primary  
    class _DriverPng:  
        def get_screenshot_as_png(self) -> bytes:  
            return b"\x89PNG\r\n\x1a\nFAKEPNG"  
  
    d1 = _DriverPng()  
    png = capture_screenshot_png_bytes(d1)  
    assert png == b"\x89PNG\r\n\x1a\nFAKEPNG"  
    b64 = capture_screenshot_b64(d1)  
    assert b64 == base64.b64encode(b"\x89PNG\r\n\x1a\nFAKEPNG").decode("ascii")  
  
    payload = capture_screenshot_payload(  
        driver=d1,  
        captured_at_utc="2026-01-01T00:00:00+00:00",  
        label="failure",  
    )  
    assert payload["schema"] == "SNAP-1B"  
    assert payload["ok"] is True  
    assert payload["content_type"] == "image/png"  
    assert payload["screenshot_b64"] == b64  
    assert payload["bytes_len"] == len(b"\x89PNG\r\n\x1a\nFAKEPNG")  
  
    # Case 2: base64 primary (no png method)  
    class _DriverB64:  
        def get_screenshot_as_base64(self) -> str:  
            return base64.b64encode(b"\x89PNG\r\n\x1a\nB64ONLY").decode("ascii")  
  
    d2 = _DriverB64()  
    assert capture_screenshot_png_bytes(d2) == b"\x89PNG\r\n\x1a\nB64ONLY"  
    assert capture_screenshot_b64(d2) == base64.b64encode(b"\x89PNG\r\n\x1a\nB64ONLY").decode("ascii")  
  
    # Case 3: unavailable / error  
    class _DriverNone:  
        def get_screenshot_as_base64(self) -> str:  
            raise RuntimeError("no screenshot")  
  
    d3 = _DriverNone()  
    payload3 = capture_screenshot_payload(  
        driver=d3,  
        captured_at_utc="2026-01-01T00:00:00+00:00",  
        label="on_demand",  
    )  
    assert payload3["ok"] is False  
    assert payload3["screenshot_b64"] is None  
    assert payload3["error"]["class"] == "ScreenshotUnavailable"  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: SNAP.snap_1b_screenshot_capture")  