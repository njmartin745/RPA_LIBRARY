"""  
OUT-1A — Download wait/poll + directory management.  
  
Purpose  
-------  
Provide directory management and a polling-based "wait for download" helper.  
  
This module complements VAL-1B:  
- VAL-1B validates current state (exists, size threshold, name filtering)  
- OUT-1A waits/polls until validation succeeds and (optionally) the file stabilizes  
  
Public API  
----------  
ensure_download_dir(download_dir=None, cfg=None, create=True) -> str  
  
wait_for_download(  
    *,  
    download_dir=None,  
    file_path=None,  
    glob=None,  
    name_contains=None,  
    timeout_sec=60.0,  
    poll_sec=0.5,  
    min_size_bytes=1,  
    stable_sec=1.0,  
    clear_before=False,  
    cfg=None,  
) -> dict  
  
Config (env-friendly)  
---------------------  
DOWNLOAD_DIR  
DOWNLOAD_PATH  
DOWNLOAD_GLOB  
DOWNLOAD_NAME_CONTAINS  
TIMEOUT_SEC  
POLL_SEC  
MIN_SIZE_BYTES  
STABLE_SEC  
CLEAR_BEFORE  
  
Return contract  
---------------  
{  
  "ok": bool,  
  "path": str | None,  
  "size_bytes": int | None,  
  "elapsed_sec": float,  
  "matches": list[str],  
  "error": str | None  
}  
"""  
  
from __future__ import annotations  
  
import fnmatch  
import os  
import time  
from typing import Any, Dict, List, Mapping, Optional  
  
from VAL.val_1b_download_validation import validate_download  
  
__all__ = ["ensure_download_dir", "wait_for_download"]  
  
  
def _get_str(cfg: Optional[Mapping[str, Any]], key: str) -> Optional[str]:  
    if not cfg:  
        return None  
    v = cfg.get(key)  
    if isinstance(v, str) and v.strip():  
        return v.strip()  
    return None  
  
  
def _get_float(cfg: Optional[Mapping[str, Any]], key: str) -> Optional[float]:  
    if not cfg:  
        return None  
    v = cfg.get(key)  
    if v is None:  
        return None  
    try:  
        return float(v)  
    except Exception:  
        return None  
  
  
def _get_int(cfg: Optional[Mapping[str, Any]], key: str) -> Optional[int]:  
    if not cfg:  
        return None  
    v = cfg.get(key)  
    if v is None:  
        return None  
    try:  
        return int(v)  
    except Exception:  
        return None  
  
  
def _get_bool(cfg: Optional[Mapping[str, Any]], key: str) -> Optional[bool]:  
    if not cfg:  
        return None  
    v = cfg.get(key)  
    if isinstance(v, bool):  
        return v  
    if isinstance(v, (int, float)):  
        return bool(v)  
    if isinstance(v, str):  
        s = v.strip().lower()  
        if s in {"1", "true", "yes", "y", "on"}:  
            return True  
        if s in {"0", "false", "no", "n", "off"}:  
            return False  
    return None  
  
  
def ensure_download_dir(download_dir: Optional[str] = None, cfg: Optional[Mapping[str, Any]] = None, create: bool = True) -> str:  
    """  
    Resolve and (optionally) create the download directory.  
    """  
    if download_dir is None:  
        download_dir = _get_str(cfg, "DOWNLOAD_DIR")  
  
    dd = (download_dir or "").strip()  
    if not dd:  
        raise ValueError("Missing download_dir (or cfg['DOWNLOAD_DIR']).")  
  
    if create:  
        os.makedirs(dd, exist_ok=True)  
  
    return dd  
  
  
def _list_matching_files(download_dir: str, glob_pat: Optional[str], name_contains: Optional[str]) -> List[str]:  
    if not download_dir or not os.path.isdir(download_dir):  
        return []  
    gp = glob_pat.strip() if isinstance(glob_pat, str) and glob_pat.strip() else None  
    nc = name_contains.lower() if isinstance(name_contains, str) and name_contains.strip() else None  
  
    out: List[str] = []  
    for name in os.listdir(download_dir):  
        full = os.path.join(download_dir, name)  
        if not os.path.isfile(full):  
            continue  
        if gp and not fnmatch.fnmatch(name, gp):  
            continue  
        if nc and nc not in name.lower():  
            continue  
        out.append(full)  
    return out  
  
  
def _clear_matching(download_dir: str, glob_pat: Optional[str], name_contains: Optional[str]) -> None:  
    for p in _list_matching_files(download_dir, glob_pat, name_contains):  
        try:  
            os.remove(p)  
        except Exception:  
            pass  
  
  
def wait_for_download(  
    *,  
    download_dir: Optional[str] = None,  
    file_path: Optional[str] = None,  
    glob: Optional[str] = None,  
    name_contains: Optional[str] = None,  
    timeout_sec: float = 60.0,  
    poll_sec: float = 0.5,  
    min_size_bytes: int = 1,  
    stable_sec: float = 1.0,  
    clear_before: bool = False,  
    cfg: Optional[Mapping[str, Any]] = None,  
) -> Dict[str, Any]:  
    """  
    Poll until a download appears and validates.  
  
    If `file_path` (or cfg['DOWNLOAD_PATH']) is set:  
        waits for that exact file to exist and reach size threshold.  
    Else:  
        waits for the newest file in `download_dir` matching filters.  
  
    `stable_sec`:  
        If > 0, require the selected file's size to remain unchanged for at least  
        `stable_sec` seconds before returning ok.  
    """  
    # cfg defaults  
    if download_dir is None:  
        download_dir = _get_str(cfg, "DOWNLOAD_DIR")  
    if file_path is None:  
        file_path = _get_str(cfg, "DOWNLOAD_PATH")  
    if glob is None:  
        glob = _get_str(cfg, "DOWNLOAD_GLOB")  
    if name_contains is None:  
        name_contains = _get_str(cfg, "DOWNLOAD_NAME_CONTAINS")  
  
    cfg_timeout = _get_float(cfg, "TIMEOUT_SEC")  
    if cfg_timeout is not None:  
        timeout_sec = cfg_timeout  
    cfg_poll = _get_float(cfg, "POLL_SEC")  
    if cfg_poll is not None:  
        poll_sec = cfg_poll  
    cfg_min = _get_int(cfg, "MIN_SIZE_BYTES")  
    if cfg_min is not None:  
        min_size_bytes = cfg_min  
    cfg_stable = _get_float(cfg, "STABLE_SEC")  
    if cfg_stable is not None:  
        stable_sec = cfg_stable  
    cfg_clear = _get_bool(cfg, "CLEAR_BEFORE")  
    if cfg_clear is not None:  
        clear_before = cfg_clear  
  
    start = time.monotonic()  
  
    # Resolve / create directory when using directory matching.  
    if not (isinstance(file_path, str) and file_path.strip()):  
        if not (isinstance(download_dir, str) and download_dir.strip()):  
            return {  
                "ok": False,  
                "path": None,  
                "size_bytes": None,  
                "elapsed_sec": 0.0,  
                "matches": [],  
                "error": "ValueError: missing download_dir (DOWNLOAD_DIR) and no file_path provided",  
            }  
        download_dir = ensure_download_dir(download_dir, cfg=cfg, create=True)  
        if clear_before:  
            _clear_matching(download_dir, glob, name_contains)  
  
    last_size: Optional[int] = None  
    stable_since: Optional[float] = None  
  
    while True:  
        now = time.monotonic()  
        elapsed = now - start  
        if elapsed > float(timeout_sec):  
            # final snapshot for debugging  
            snap = validate_download(  
                file_path=file_path.strip() if isinstance(file_path, str) and file_path.strip() else None,  
                download_dir=download_dir.strip() if isinstance(download_dir, str) and download_dir.strip() else None,  
                glob=glob,  
                name_contains=name_contains,  
                min_size_bytes=min_size_bytes,  
                cfg=cfg,  
            )  
            return {  
                "ok": False,  
                "path": snap.get("path"),  
                "size_bytes": snap.get("size_bytes"),  
                "elapsed_sec": elapsed,  
                "matches": snap.get("matches") or [],  
                "error": f"TimeoutError: no validated download before timeout_sec={timeout_sec}. Last: {snap.get('error')}",  
            }  
  
        snap = validate_download(  
            file_path=file_path.strip() if isinstance(file_path, str) and file_path.strip() else None,  
            download_dir=download_dir.strip() if isinstance(download_dir, str) and download_dir.strip() else None,  
            glob=glob,  
            name_contains=name_contains,  
            min_size_bytes=min_size_bytes,  
            cfg=cfg,  
        )  
  
        if snap.get("ok") is True:  
            p = snap.get("path")  
            size = snap.get("size_bytes")  
  
            # If no stabilization required, return immediately.  
            if not stable_sec or float(stable_sec) <= 0:  
                return {  
                    "ok": True,  
                    "path": p,  
                    "size_bytes": size,  
                    "elapsed_sec": elapsed,  
                    "matches": snap.get("matches") or [],  
                    "error": None,  
                }  
  
            # Stabilization check: size unchanged for stable_sec.  
            try:  
                current_size = int(os.path.getsize(str(p))) if p else None  
            except Exception:  
                current_size = None  
  
            if current_size is None:  
                # treat as not stable yet  
                last_size = None  
                stable_since = None  
            else:  
                if last_size is None or current_size != last_size:  
                    last_size = current_size  
                    stable_since = now  
                else:  
                    if stable_since is not None and (now - stable_since) >= float(stable_sec):  
                        return {  
                            "ok": True,  
                            "path": p,  
                            "size_bytes": current_size,  
                            "elapsed_sec": elapsed,  
                            "matches": snap.get("matches") or [],  
                            "error": None,  
                        }  
  
        time.sleep(max(0.05, float(poll_sec)))  