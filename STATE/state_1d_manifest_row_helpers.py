"""  
STATE-1D — Manifest Row Helpers (standardize queued/success/fail shapes).  
  
Additive helpers to produce consistent manifest JSONL rows and write them through  
an existing STATE-1B writer instance.  
  
Constraints  
-----------  
- Does NOT duplicate STATE-1B open_manifest/append logic; accepts a writer.  
- Never include secrets in rows (best-effort redaction for common patterns).  
"""  
  
from __future__ import annotations  
  
from datetime import datetime, timezone  
from typing import Any, Dict, Optional  
  
__all__ = [  
    "now_utc_ts",  
    "build_row_base",  
    "row_queued",  
    "row_success",  
    "row_failure",  
    "write_row",  
]  
  
  
def now_utc_ts() -> str:  
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")  
  
  
def _redact_text(s: str) -> str:  
    if not s:  
        return s  
    t = str(s)  
  
    # Basic best-effort redactions for common secret patterns  
    lower = t.lower()  
    for key in ("password", "passwd", "pwd", "token", "secret", "api_key", "apikey", "authorization", "cookie"):  
        if key in lower:  
            # blunt redaction: keep message but remove likely secrets after separators  
            # e.g. "password=abc" -> "password=<REDACTED>"  
            import re  
  
            t = re.sub(rf"(?i)\b({key})\b\s*[:=]\s*([^\s,;]+)", r"\1=<REDACTED>", t)  
    if len(t) > 2000:  
        t = t[:2000] + "…"  
    return t  
  
  
def _safe_obj(x: Any) -> Any:  
    """  
    Convert to JSON-serializable-ish structure while redacting strings.  
    Keeps dict/list scalars; converts unknown objects to redacted string.  
    """  
    if x is None:  
        return None  
    if isinstance(x, (bool, int, float)):  
        return x  
    if isinstance(x, str):  
        return _redact_text(x)  
    if isinstance(x, list):  
        return [_safe_obj(v) for v in x[:200]]  # avoid huge payloads  
    if isinstance(x, dict):  
        out: Dict[str, Any] = {}  
        for k, v in list(x.items())[:200]:  
            out[str(k)] = _safe_obj(v)  
        return out  
    return _redact_text(str(x))  
  
  
def build_row_base(  
    *,  
    run_id: str | None,  
    item_id: str | None,  
    step: str | None,  
    meta: dict | None,  
) -> Dict[str, Any]:  
    row: Dict[str, Any] = {"ts": now_utc_ts()}  
    if run_id is not None:  
        row["run_id"] = _safe_obj(str(run_id))  
    if item_id is not None:  
        row["item_id"] = _safe_obj(str(item_id))  
    if step is not None:  
        row["step"] = _safe_obj(str(step))  
    if meta:  
        row["meta"] = _safe_obj(meta)  
    return row  
  
  
def row_queued(  
    *,  
    run_id: str | None = None,  
    item_id: str | None = None,  
    step: str | None = None,  
    meta: dict | None = None,  
    reason: str | None = None,  
) -> Dict[str, Any]:  
    row = build_row_base(run_id=run_id, item_id=item_id, step=step, meta=meta)  
    row["status"] = "queued"  
    if reason is not None:  
        row["reason"] = _safe_obj(reason)  
    return row  
  
  
def row_success(  
    *,  
    run_id: str | None = None,  
    item_id: str | None = None,  
    step: str | None = None,  
    meta: dict | None = None,  
    details: dict | None = None,  
) -> Dict[str, Any]:  
    row = build_row_base(run_id=run_id, item_id=item_id, step=step, meta=meta)  
    row["status"] = "success"  
    if details:  
        row["details"] = _safe_obj(details)  
    return row  
  
  
def _normalize_error_payload(error: Dict[str, Any]) -> Dict[str, Any]:  
    """  
    Accepts either:  
    - LOG-1B.classify_exception output: {code,type,message,details?}  
    - LOG-1B.format_error_for_manifest output: {error_code,error_type,error_message}  
    Returns a safe subset under keys: code,type,message  
    """  
    if not isinstance(error, dict):  
        return {"code": "UNKNOWN_ERROR", "type": "InvalidError", "message": "Invalid error payload"}  
  
    if "code" in error or "type" in error or "message" in error:  
        return {  
            "code": _safe_obj(error.get("code")),  
            "type": _safe_obj(error.get("type")),  
            "message": _safe_obj(error.get("message")),  
        }  
  
    # manifest-shaped  
    if "error_code" in error or "error_type" in error or "error_message" in error:  
        return {  
            "code": _safe_obj(error.get("error_code")),  
            "type": _safe_obj(error.get("error_type")),  
            "message": _safe_obj(error.get("error_message")),  
        }  
  
    return {"code": "UNKNOWN_ERROR", "type": "Exception", "message": "Unrecognized error payload"}  
  
  
def row_failure(  
    *,  
    run_id: str | None = None,  
    item_id: str | None = None,  
    step: str | None = None,  
    meta: dict | None = None,  
    error: dict,  
    details: dict | None = None,  
) -> Dict[str, Any]:  
    row = build_row_base(run_id=run_id, item_id=item_id, step=step, meta=meta)  
    row["status"] = "fail"  
    row["error"] = _normalize_error_payload(error)  
    if details:  
        row["details"] = _safe_obj(details)  
    return row  
  
  
def write_row(writer: Any, row: Dict[str, Any]) -> None:  
    """  
    Write a row via an existing STATE-1B writer.  
  
    Tries common contracts:  
    - writer.append(row)  
    - writer.write(row)  
    - writer.append_row(row)  
    - writer.write_row(row)  
    - writer(row) if callable  
    """  
    if writer is None:  
        raise ValueError("writer is required")  
    if not isinstance(row, dict):  
        raise TypeError("row must be a dict")  
  
    for meth in ("append", "write", "append_row", "write_row", "add_row"):  
        fn = getattr(writer, meth, None)  
        if callable(fn):  
            fn(row)  
            return  
  
    if callable(writer):  
        writer(row)  
        return  
  
    raise TypeError("Unsupported writer contract (no append/write method found).")  