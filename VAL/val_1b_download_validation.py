"""  
VAL-1B — Download validation (file exists, size > 0, optional name patterns).  
  
Purpose  
-------  
Validate that a download artifact is present and non-empty, optionally selecting it  
from a directory by glob/name filters.  
  
This module intentionally does NOT implement polling/waiting; it validates current state.  
  
Public API  
----------  
validate_download(  
    *,  
    file_path: str | None = None,  
    download_dir: str | None = None,  
    glob: str | None = None,  
    name_contains: str | None = None,  
    min_size_bytes: int = 1,  
    cfg: dict | None = None,  
) -> dict  
  
Config (env-friendly)  
---------------------  
DOWNLOAD_PATH (explicit file)  
DOWNLOAD_DIR  
DOWNLOAD_GLOB  
DOWNLOAD_NAME_CONTAINS  
MIN_SIZE_BYTES  
  
Return contract  
---------------  
{  
  "ok": bool,  
  "path": str | None,  
  "size_bytes": int | None,  
  "matches": list[str],  
  "error": str | None  
}  
"""  
  
from __future__ import annotations  
  
import fnmatch  
import os  
from dataclasses import dataclass  
from typing import Any, Dict, List, Mapping, Optional  
  
__all__ = ["validate_download"]  
  
  
@dataclass(frozen=True)  
class _Candidate:  
    path: str  
    mtime: float  
    size: int  
  
  
def _get_str(cfg: Optional[Mapping[str, Any]], key: str) -> Optional[str]:  
    if not cfg:  
        return None  
    v = cfg.get(key)  
    if isinstance(v, str) and v.strip():  
        return v.strip()  
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
  
  
def _list_matches(download_dir: str, glob_pat: Optional[str], name_contains: Optional[str]) -> List[_Candidate]:  
    matches: List[_Candidate] = []  
    if not download_dir or not os.path.isdir(download_dir):  
        return matches  
  
    nc = name_contains.lower() if isinstance(name_contains, str) and name_contains else None  
    gp = glob_pat if isinstance(glob_pat, str) and glob_pat.strip() else None  
  
    for name in os.listdir(download_dir):  
        full = os.path.join(download_dir, name)  
        if not os.path.isfile(full):  
            continue  
  
        if gp and not fnmatch.fnmatch(name, gp):  
            continue  
        if nc and nc not in name.lower():  
            continue  
  
        try:  
            st = os.stat(full)  
            matches.append(_Candidate(path=full, mtime=float(st.st_mtime), size=int(st.st_size)))  
        except Exception:  
            continue  
  
    # newest first  
    matches.sort(key=lambda c: (c.mtime, c.path), reverse=True)  
    return matches  
  
  
def validate_download(  
    *,  
    file_path: Optional[str] = None,  
    download_dir: Optional[str] = None,  
    glob: Optional[str] = None,  
    name_contains: Optional[str] = None,  
    min_size_bytes: int = 1,  
    cfg: Optional[Mapping[str, Any]] = None,  
) -> Dict[str, Any]:  
    """  
    Validate a downloaded file.  
  
    Selection:  
      - If file_path is provided (or cfg['DOWNLOAD_PATH']), validate that file.  
      - Else, select the newest matching file in download_dir (or cfg['DOWNLOAD_DIR'])  
        using optional glob/name_contains (or cfg keys).  
  
    Returns a dict per the return contract in module docstring.  
    """  
    # cfg defaults  
    if file_path is None:  
        file_path = _get_str(cfg, "DOWNLOAD_PATH")  
    if download_dir is None:  
        download_dir = _get_str(cfg, "DOWNLOAD_DIR")  
    if glob is None:  
        glob = _get_str(cfg, "DOWNLOAD_GLOB")  
    if name_contains is None:  
        name_contains = _get_str(cfg, "DOWNLOAD_NAME_CONTAINS")  
  
    cfg_min = _get_int(cfg, "MIN_SIZE_BYTES")  
    if cfg_min is not None:  
        min_size_bytes = cfg_min  
  
    # explicit file validation  
    if isinstance(file_path, str) and file_path.strip():  
        p = file_path.strip()  
        if not os.path.exists(p):  
            return {"ok": False, "path": p, "size_bytes": None, "matches": [], "error": f"FileNotFoundError: {p}"}  
        if not os.path.isfile(p):  
            return {"ok": False, "path": p, "size_bytes": None, "matches": [], "error": f"NotAFileError: {p}"}  
        try:  
            size = os.path.getsize(p)  
        except Exception as e:  
            return {"ok": False, "path": p, "size_bytes": None, "matches": [], "error": f"{type(e).__name__}: {e}"}  
        if size < int(min_size_bytes):  
            return {  
                "ok": False,  
                "path": p,  
                "size_bytes": size,  
                "matches": [p],  
                "error": f"ValueError: file too small (size={size}, min_size_bytes={min_size_bytes})",  
            }  
        return {"ok": True, "path": p, "size_bytes": size, "matches": [p], "error": None}  
  
    # directory selection + validation  
    if not (isinstance(download_dir, str) and download_dir.strip()):  
        return {"ok": False, "path": None, "size_bytes": None, "matches": [], "error": "ValueError: missing download_dir (DOWNLOAD_DIR)"}  
  
    dd = download_dir.strip()  
    cands = _list_matches(dd, glob, name_contains)  
    match_paths = [c.path for c in cands]  
  
    if not cands:  
        return {  
            "ok": False,  
            "path": None,  
            "size_bytes": None,  
            "matches": [],  
            "error": f"FileNotFoundError: no matches in {dd!r} (glob={glob!r}, name_contains={name_contains!r})",  
        }  
  
    best = cands[0]  
    if best.size < int(min_size_bytes):  
        return {  
            "ok": False,  
            "path": best.path,  
            "size_bytes": best.size,  
            "matches": match_paths,  
            "error": f"ValueError: matched file too small (size={best.size}, min_size_bytes={min_size_bytes})",  
        }  
  
    return {"ok": True, "path": best.path, "size_bytes": best.size, "matches": match_paths, "error": None}  