"""  
HISTORY-1C — Error normalization (10.2.3)  
  
Single responsibility:  
- Normalize Python exceptions into a deterministic, JSON-serializable structure  
  suitable for history logs and reports.  
  
Design notes:  
- Avoid repr() (can include memory addresses).  
- Traceback filenames are normalized (default: basename only) for cross-machine stability.  
- Supports __cause__ and __context__ chaining with bounded depth.  
"""  
  
from __future__ import annotations  
  
from pathlib import Path  
import traceback  
from typing import Any  
  
__all__ = [  
    "normalize_exception",  
    "dev_smoke",  
]  
  
  
def _norm_filename(filename: str | None, *, mode: str) -> str | None:  
    if filename is None:  
        return None  
    try:  
        p = Path(filename)  
        if mode == "basename":  
            return p.name  
        if mode == "posix":  
            return p.as_posix()  
        # fallback: raw string  
        return str(filename)  
    except Exception:  
        return str(filename)  
  
  
def _extract_frames(  
    tb: Any,  
    *,  
    max_frames: int,  
    filename_mode: str,  
) -> tuple[list[dict[str, Any]], bool]:  
    """  
    Return (frames, truncated).  
    Each frame: {filename, lineno, function}  
    """  
    if tb is None:  
        return [], False  
  
    extracted = traceback.extract_tb(tb)  
    truncated = False  
    if len(extracted) > max_frames:  
        extracted = extracted[-max_frames:]  
        truncated = True  
  
    frames: list[dict[str, Any]] = []  
    for fr in extracted:  
        frames.append(  
            {  
                "filename": _norm_filename(fr.filename, mode=filename_mode),  
                "lineno": int(fr.lineno) if fr.lineno is not None else None,  
                "function": str(fr.name) if fr.name is not None else None,  
            }  
        )  
    return frames, truncated  
  
  
def normalize_exception(  
    error: BaseException,  
    *,  
    include_traceback: bool = True,  
    max_frames: int = 50,  
    filename_mode: str = "basename",  
    include_chain: bool = True,  
    max_chain_depth: int = 5,  
) -> dict[str, Any]:  
    """  
    Normalize an exception into a stable JSON-serializable dict.  
  
    filename_mode:  
      - 'basename' (default): only keep the file name (most stable)  
      - 'posix': keep a posix path  
      - other: keep raw string  
  
    include_chain:  
      - include __cause__ and __context__ (bounded by max_chain_depth)  
    """  
    if not isinstance(error, BaseException):  
        raise TypeError("error must be an exception instance")  
  
    def norm_one(e: BaseException, depth: int) -> dict[str, Any]:  
        frames: list[dict[str, Any]] = []  
        tb_truncated = False  
        if include_traceback:  
            frames, tb_truncated = _extract_frames(  
                getattr(e, "__traceback__", None),  
                max_frames=max_frames,  
                filename_mode=filename_mode,  
            )  
  
        obj: dict[str, Any] = {  
            "schema": "HISTORY-1C-ERROR",  
            "class": e.__class__.__name__,  
            "module": e.__class__.__module__,  
            "message": str(e),  
            "traceback": frames if include_traceback else None,  
            "traceback_truncated": tb_truncated if include_traceback else None,  
        }  
  
        if include_chain and depth < max_chain_depth:  
            cause = getattr(e, "__cause__", None)  
            context = getattr(e, "__context__", None)  
            suppress_context = bool(getattr(e, "__suppress_context__", False))  
  
            obj["cause"] = norm_one(cause, depth + 1) if isinstance(cause, BaseException) else None  
            # Only include context when it is not suppressed and not identical to cause  
            if (not suppress_context) and isinstance(context, BaseException) and context is not cause:  
                obj["context"] = norm_one(context, depth + 1)  
            else:  
                obj["context"] = None  
            obj["suppress_context"] = suppress_context  
            obj["chain_truncated"] = False  
        else:  
            obj["cause"] = None  
            obj["context"] = None  
            obj["suppress_context"] = None  
            obj["chain_truncated"] = bool(include_chain)  
  
        return obj  
  
    return norm_one(error, 0)  
  
  
def dev_smoke() -> None:  
    def inner() -> None:  
        raise ValueError("bad input")  
  
    def outer() -> None:  
        try:  
            inner()  
        except Exception as e:  
            raise RuntimeError("outer failed") from e  
  
    try:  
        outer()  
        raise AssertionError("expected exception")  
    except Exception as e:  
        norm = normalize_exception(  
            e,  
            include_traceback=True,  
            max_frames=50,  
            filename_mode="basename",  
            include_chain=True,  
            max_chain_depth=5,  
        )  
  
    assert norm["schema"] == "HISTORY-1C-ERROR"  
    assert norm["class"] == "RuntimeError"  
    assert norm["message"] == "outer failed"  
    assert isinstance(norm["traceback"], list)  
    assert norm["cause"] is not None  
    assert norm["cause"]["class"] == "ValueError"  
    assert norm["cause"]["message"] == "bad input"  
  
    # filename_mode='basename' should not include directory separators  
    for fr in norm["traceback"]:  
        fn = fr.get("filename")  
        if isinstance(fn, str):  
            assert ("/" not in fn) and ("\\" not in fn)  
  
    # Cause traceback should include inner() somewhere (function name).  
    cause_frames = norm["cause"]["traceback"]  
    assert isinstance(cause_frames, list)  
    assert any(fr.get("function") == "inner" for fr in cause_frames)  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: HISTORY.history_1c_error_normalization")  