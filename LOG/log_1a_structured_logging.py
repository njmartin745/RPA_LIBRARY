# LOG/log_1a_structured_logging.py  
"""  
LOG-1A — Standard structured logging + run_id + per-item context (stdlib only)  
  
Purpose  
-------  
Establish a consistent, enterprise-friendly logging layer using ONLY the Python  
standard library (`logging`) that emits one-line JSON logs with:  
  
- Stable top-level keys:  
    timestamp_utc, level, logger, message, event,  
    run_id, current_id, item_index, total_items, fields  
- A lightweight context mechanism (run_id + per-item context) that works across  
  modules without passing logger adapters everywhere.  
- Built-in redaction to prevent accidental leakage of secrets.  
  
Inputs / Outputs  
----------------  
setup_logging(cfg) -> logging.Logger  
- Reads cfg keys:  
  - LOG_LEVEL (default "INFO")  
  - LOG_PATH (optional file path; enables rotating file logging)  
  - RUN_ID (optional; generated if missing)  
  - LOG_JSON (default true; retained for compatibility; JSON output remains the default)  
  - QUIET_CONSOLE (optional; suppress console handler if truthy)  
- Returns the base logger ("rpa") configured with handlers + JSON formatter.  
  
bind_context(cfg, **fields) -> None  
- Stores run_id/current_id/item_index/total_items into a context store.  
- Also ensures cfg["RUN_ID"] exists (generated if missing).  
- Common workflow usage: call once per run, and again per item.  
  
log_event(logger, event: str, **fields) -> None  
- Emits one structured JSON log line.  
- Redacts secrets by key name: password, secret, token, api_key (case-insensitive).  
  
log_exception(logger, exc, *, step_id=None, milestone=None, tag=None, event="exception", **fields) -> None  
- Emits one structured error log line with traceback + optional step metadata.  
  
When to use  
-----------  
- Any Selenium/RPA workflow where consistent, machine-parsable logs are needed.  
- CI runs, headless runs, enterprise environments requiring stdlib-only logging.  
  
When NOT to use  
---------------  
- If you need distributed tracing, OpenTelemetry exporters, or third-party logging stacks.  
  (This module intentionally stays stdlib-only; integrate downstream if needed.)  
  
Failure modes + mitigations  
---------------------------  
- Duplicate logs due to repeated setup: setup_logging() is idempotent and replaces handlers.  
- Non-JSON-serializable field values: values are JSON-dumped with default=str.  
- Secret leakage: keys matching the sensitive set are redacted; avoid passing whole cfg  
  or raw credential blobs into log_event fields.  
  
Minimal usage example  
---------------------  
from LOG.log_1a_structured_logging import setup_logging, bind_context, log_event  
  
cfg = {"LOG_LEVEL": "INFO"}  
logger = setup_logging(cfg)  
bind_context(cfg, run_id=cfg["RUN_ID"])  
  
log_event(logger, "run_start", version="1.0.0")  
bind_context(cfg, current_id="A123", item_index=1, total_items=10)  
log_event(logger, "item_start")  
"""  
  
from __future__ import annotations
 
import json
import logging
import os
import re
import sys
import traceback as _tb
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, MutableMapping, Optional
 
__all__ = [
    "setup_logging",
    "get_logger",
    "bind_context",
    "clear_context",
    "redact",
    "log_event",
    "log_exception",
]
 
_BASE_LOGGER_NAME = "rpa"
_LOG_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("LOG_1A_CONTEXT", default={})
 
_SENSITIVE_KEYS = {"password", "secret", "token", "api_key"}
 
# Best-effort in-string redaction (primary protection is key-based redaction)
_RE_KV_SECRETS = re.compile(r"(?i)\b(password|secret|token|api[_-]?key)\b(\s*[:=]\s*)([^\s,}]+)")
_RE_BEARER = re.compile(r"(?i)\bBearer\s+([A-Za-z0-9\._\-]+)")
 
 
def _utc_ts() -> str:
    # ISO 8601 with milliseconds, UTC "Z" suffix
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
 
 
def _truthy(v: Any) -> bool:
    s = str(v or "").strip().lower()
    return s in {"1", "true", "yes", "on"}
 
 
def _level_from_cfg(cfg: MutableMapping[str, Any]) -> int:
    raw = str(cfg.get("LOG_LEVEL", "INFO")).strip().upper()
    return int(getattr(logging, raw, logging.INFO))
 
 
def _ensure_run_id(cfg: MutableMapping[str, Any]) -> str:
    run_id = str(cfg.get("RUN_ID") or "").strip()
    if not run_id:
        run_id = uuid.uuid4().hex
        cfg["RUN_ID"] = run_id
    return run_id
 
 
def _should_json(cfg: MutableMapping[str, Any]) -> bool:
    # LOG_JSON default true (compat)
    return _truthy(cfg.get("LOG_JSON", True))
 
 
def _quiet_console(cfg: MutableMapping[str, Any]) -> bool:
    return _truthy(cfg.get("QUIET_CONSOLE", False))
 
 
def _log_path(cfg: MutableMapping[str, Any]) -> Optional[Path]:  
    p = str(cfg.get("LOG_JSONL_PATH") or cfg.get("LOG_PATH") or "").strip()  
    if not p:
        return None
    return Path(p).expanduser().resolve()
 
 
def _redact_value(s: str) -> str:
    # redact common patterns
    s = _RE_KV_SECRETS.sub(lambda m: f"{m.group(1)}{m.group(2)}***", s)
    s = _RE_BEARER.sub("Bearer ***", s)
    return s
 
 
def redact(obj: Any, *, key: Optional[str] = None) -> Any:
    """
    Best-effort redaction:
    - If key name looks sensitive -> "***"
    - If strings contain obvious secret patterns -> masked
    - Recurses dict/list/tuple
    """
    if key and str(key).strip().lower() in _SENSITIVE_KEYS:
        return "***"
 
    if obj is None:
        return None
 
    if isinstance(obj, (int, float, bool)):
        return obj
 
    if isinstance(obj, str):
        return _redact_value(obj)
 
    if isinstance(obj, dict):
        return {k: redact(v, key=str(k)) for k, v in obj.items()}
 
    if isinstance(obj, (list, tuple)):
        t = [redact(v) for v in obj]
        return t if isinstance(obj, list) else tuple(t)
 
    # fallback: stringify then mask obvious patterns
    return _redact_value(str(obj))
 
 
class _JsonLineFormatter(logging.Formatter):
    def __init__(self, *, cfg: MutableMapping[str, Any]):
        super().__init__()
        self._cfg = cfg
 
    def format(self, record: logging.LogRecord) -> str:
        base_ctx = dict(_LOG_CONTEXT.get() or {})
        run_id = _ensure_run_id(self._cfg)
 
        payload: dict[str, Any] = {
            "timestamp_utc": _utc_ts(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "event": getattr(record, "event", None),
            "run_id": run_id,
            "current_id": base_ctx.get("current_id"),
            "item_index": base_ctx.get("item_index"),
            "total_items": base_ctx.get("total_items"),
        }
 
        # Merge any extra fields
        fields = getattr(record, "fields", None)  
        if isinstance(fields, dict):  
            payload["fields"] = fields  
            # also expose non-colliding keys at top-level for easy parsing  
            for k, v in fields.items():  
                if k not in payload:  
                    payload[k] = v  
 
        # Redact all
        payload = redact(payload)  # type: ignore[assignment]
 
        try:
            return json.dumps(payload, ensure_ascii=False, default=str)
        except Exception:
            # last-resort
            return json.dumps({"message": "log-json-encode-failed", "raw": str(payload)})
 
 
def setup_logging(cfg: MutableMapping[str, Any]) -> logging.Logger:
    """
    Configure base logger "rpa" with:
    - console JSON line logs (default)
    - optional rotating file logging (LOG_PATH)
    Idempotent: replaces handlers each call.
    """
    logger = logging.getLogger(_BASE_LOGGER_NAME)
    logger.setLevel(_level_from_cfg(cfg))
    logger.propagate = False
 
    # Replace handlers (idempotent)
    for h in list(logger.handlers):
        logger.removeHandler(h)
 
    formatter: logging.Formatter
    if _should_json(cfg):
        formatter = _JsonLineFormatter(cfg=cfg)
    else:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
 
    if not _quiet_console(cfg):
        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setLevel(_level_from_cfg(cfg))
        sh.setFormatter(formatter)
        logger.addHandler(sh)
 
    lp = _log_path(cfg)
    if lp is not None:
        lp.parent.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(
            filename=str(lp),
            maxBytes=int(cfg.get("LOG_MAX_BYTES", 1_000_000) or 1_000_000),
            backupCount=int(cfg.get("LOG_BACKUPS", 3) or 3),
            encoding="utf-8",
        )
        fh.setLevel(_level_from_cfg(cfg))
        fh.setFormatter(formatter)
        logger.addHandler(fh)
 
    _ensure_run_id(cfg)
    return logger
 
 
def get_logger(name: str = _BASE_LOGGER_NAME) -> logging.Logger:
    """Return a logger (defaults to base 'rpa')."""
    return logging.getLogger(name)
 
 
def bind_context(cfg: MutableMapping[str, Any], **fields: Any) -> None:
    """
    Bind run/per-item context for subsequent log lines.
    Stores in a ContextVar so you don't have to pass LoggerAdapters around.
    """
    _ensure_run_id(cfg)
    current = dict(_LOG_CONTEXT.get() or {})
    current.update(fields)
    _LOG_CONTEXT.set(current)
 
 
def clear_context() -> None:
    """Clear the bound context."""
    _LOG_CONTEXT.set({})
 
 
def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:  
    """Emit one structured log line (JSON by default)."""  
    extra = {"event": event, "fields": fields}  
    msg = str(fields.get("message", event))  
  
    ev = str(event or "").lower()  
    if "error" in ev or "exception" in ev or "fail" in ev:  
        logger.error(msg, extra=extra)  
    else:  
        logger.info(msg, extra=extra)  
 
 
def log_exception(
    logger: logging.Logger,
    exc: BaseException,
    *,
    step_id: Optional[str] = None,
    milestone: Optional[str] = None,
    tag: Optional[str] = None,
    event: str = "exception",
    **fields: Any,
) -> None:
    """
    Emit one structured error line with traceback + optional step metadata.
    """
    tb = "".join(_tb.format_exception(type(exc), exc, exc.__traceback__))
    payload = dict(fields)
    payload.update(
        {
            "exc_type": type(exc).__name__,
            "exc": str(exc),
            "traceback": tb,
        }
    )
    if step_id is not None:
        payload["step_id"] = step_id
    if milestone is not None:
        payload["milestone"] = milestone
    if tag is not None:
        payload["tag"] = tag
 
    extra = {"event": event, "fields": payload}
    logger.error(str(exc), extra=extra)