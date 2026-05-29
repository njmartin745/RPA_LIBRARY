"""
PIPE-1H — JSONL Log Path Policy

Purpose
-------
Resolve runtime JSONL logging destinations using
a deterministic precedence model and manage
temporary log file lifecycle.

Public API
----------
select_log_jsonl_path(...)
maybe_cleanup_log_jsonl_path(...)

Dependencies
------------
None

Status
------
Draft

Notes
-----
Path Resolution Priority:

LOG_JSONL_PATH (env)
        ↓
LOG_PATH (env)
        ↓
LOG_JSONL_PATH (cfg)
        ↓
LOG_PATH (cfg)
        ↓
Temporary File

Temporary files created by the framework may be
cleaned up automatically.

User-provided log files are never automatically
deleted.
"""

from __future__ import annotations  
  
import os  
import tempfile  
from typing import Any, Mapping, MutableMapping  
  
__all__ = [  
    "select_log_jsonl_path",  
    "maybe_cleanup_log_jsonl_path",  
    "dev_smoke",  
]  
  
  
def select_log_jsonl_path(  
    cfg: MutableMapping[str, Any],  
    *,  
    environ: Mapping[str, str] | None = None,  
    prefix: str = "pipe_1e_log_",  
    suffix: str = ".jsonl",  
) -> tuple[str, bool]:  
    env = os.environ if environ is None else environ  
  
    # ENV MUST WIN over cfg (so $env:LOG_PATH overrides workflow/CLI defaults)  
    env_path = env.get("LOG_JSONL_PATH") or env.get("LOG_PATH")  
    cfg_path = cfg.get("LOG_JSONL_PATH") or cfg.get("LOG_PATH")  
  
    path = env_path or cfg_path  
  
    if path:  
        p = os.path.abspath(os.fspath(path))  
        cfg["LOG_JSONL_PATH"] = p  
        cfg["LOG_PATH"] = p  
        return p, False  
  
    fd, p = tempfile.mkstemp(prefix=prefix, suffix=suffix)  
    os.close(fd)  
  
    p = os.path.abspath(p)  
    cfg["LOG_JSONL_PATH"] = p  
    cfg["LOG_PATH"] = p  
    return p, True  
  
  
def maybe_cleanup_log_jsonl_path(path: str, *, is_temp: bool) -> None:  
    if not is_temp:  
        return  
    try:  
        os.remove(path)  
    except FileNotFoundError:  
        return  
  
def dev_smoke() -> None:  
    # Temp path branch  
    cfg1: dict[str, Any] = {}  
    p1, is_temp1 = select_log_jsonl_path(cfg1, environ={})  
    assert is_temp1 is True  
    assert cfg1["LOG_JSONL_PATH"] == p1  
    assert os.path.exists(p1)  
    maybe_cleanup_log_jsonl_path(p1, is_temp=is_temp1)  
    assert not os.path.exists(p1)  
  
    # User-provided branch (must not be deleted)  
    user_path = os.path.abspath("_pipe_1h_user.jsonl")  
    try:  
        if os.path.exists(user_path):  
            os.remove(user_path)  
    except OSError:  
        pass  
  
    cfg2: dict[str, Any] = {"LOG_PATH": user_path}  
    p2, is_temp2 = select_log_jsonl_path(cfg2, environ={})  
    assert is_temp2 is False  
    assert p2 == user_path  
  
    with open(user_path, "w", encoding="utf-8") as f:  
        f.write("{}\n")  
    maybe_cleanup_log_jsonl_path(user_path, is_temp=is_temp2)  
    assert os.path.exists(user_path)  
  
    try:  
        os.remove(user_path)  
    except OSError:  
        pass  
  
  
if __name__ == "__main__":  
    dev_smoke()  