# HISTORY/history_1a_store.py  
"""  
HISTORY-1A — Run History Store (append-only JSONL)  
  
- No Selenium  
- Append-only JSONL history suitable for analytics/agent reasoning  
- Sanitizes records to avoid secrets  
  
Public API:  
  sanitize_run_record(record: dict) -> dict  
  append_run_history(record: dict, *, history_path="history/run_history.jsonl") -> Path  
  read_run_history(*, history_path="history/run_history.jsonl", limit=200) -> list[dict]  
  summarize_history(rows: list[dict]) -> dict  
"""  
  
from __future__ import annotations  
  
import json  
from collections import Counter, deque  
from datetime import datetime, timezone  
from pathlib import Path  
from typing import Any, Dict, Iterable, List, Optional, Tuple  
  
__all__ = [  
    "sanitize_run_record",  
    "append_run_history",  
    "read_run_history",  
    "summarize_history",  
]  
  
_SUSPICIOUS_KEY_SUBSTRINGS = (  
    "password",  
    "secret",  
    "token",  
    "cookie",  
    "authorization",  
)  
  
_MAX_STRING = 500  
_MAX_NOTES_ITEM = 500  
  
  
def _utc_now_iso() -> str:  
    return datetime.now(timezone.utc).isoformat()  
  
  
def _is_path_key(k: str) -> bool:  
    kk = (k or "").lower()  
    return (  
        kk.endswith("_path")  
        or kk.endswith("_dir")  
        or "path" in kk  
        or "dir" in kk  
        or kk in ("workflow", "workflow_path", "artifacts_dir", "report_dir")  
    )  
  
  
def _looks_like_path(v: str) -> bool:  
    # Heuristic only; used only for truncation decisions  
    if not isinstance(v, str):  
        return False  
    if len(v) < 2:  
        return False  
    return ("/" in v) or ("\\" in v) or (":" in v and len(v) < 260)  
  
  
def _truncate_string(v: str, *, keep_long: bool) -> str:  
    if not isinstance(v, str):  
        return v  
    if keep_long:  
        return v  
    if len(v) <= _MAX_STRING:  
        return v  
    return v[:_MAX_STRING] + "...(truncated)"  
  
  
def _sanitize_obj(obj: Any, *, parent_key: str = "") -> Any:  
    """  
    Recursively remove suspicious keys and truncate long strings.  
    """  
    if isinstance(obj, dict):  
        out: Dict[str, Any] = {}  
        for k, v in obj.items():  
            ks = str(k)  
            ksl = ks.lower()  
  
            # Drop suspicious keys entirely  
            if any(s in ksl for s in _SUSPICIOUS_KEY_SUBSTRINGS):  
                continue  
  
            # Keep traceback/stack out of history (drop)  
            if "traceback" in ksl or "stack" in ksl:  
                continue  
  
            out[ks] = _sanitize_obj(v, parent_key=ks)  
        return out  
  
    if isinstance(obj, list):  
        return [_sanitize_obj(x, parent_key=parent_key) for x in obj]  
  
    if isinstance(obj, str):  
        keep_long = _is_path_key(parent_key) or _looks_like_path(obj)  
        return _truncate_string(obj, keep_long=keep_long)  
  
    # basic scalars  
    if obj is None or isinstance(obj, (bool, int, float)):  
        return obj  
  
    # fallback: stringify but truncate  
    s = str(obj)  
    keep_long = _is_path_key(parent_key) or _looks_like_path(s)  
    return _truncate_string(s, keep_long=keep_long)  
  
  
def _pick_first(record: dict, keys: Iterable[str]) -> Any:  
    for k in keys:  
        if k in record and record[k] is not None:  
            return record[k]  
    return None  
  
  
def _to_bool_success(v: Any) -> Optional[bool]:  
    if isinstance(v, bool):  
        return v  
    if isinstance(v, str):  
        s = v.strip().lower()  
        if s in ("ok", "success", "true", "passed", "pass"):  
            return True  
        if s in ("fail", "failed", "false", "error"):  
            return False  
    return None  
  
  
def _duration_ms_from_any(v: Any) -> Optional[int]:  
    if v is None:  
        return None  
    if isinstance(v, int):  
        return v  
    if isinstance(v, float):  
        # assume seconds if small-ish; otherwise ms-like  
        if v < 1e6:  
            return int(round(v * 1000))  
        return int(round(v))  
    if isinstance(v, str):  
        try:  
            if v.endswith("ms"):  
                return int(float(v[:-2].strip()))  
            if v.endswith("s"):  
                return int(round(float(v[:-1].strip()) * 1000))  
            return int(float(v))  
        except Exception:  
            return None  
    return None  
  
  
def sanitize_run_record(record: dict) -> dict:  
    """  
    Accepts a flexible input record (RUN/REPORT/OBS/etc) and normalizes to a canonical shape:  
      {  
        "ts_utc": "...",  
        "run_id": "...",  
        "workflow": "...",  
        "success": true/false,  
        "duration_ms": int|None,  
        "failure_category": str|None,  
        "artifacts_dir": str|None,  
        "report_dir": str|None,  
        "patch_path": str|None,  
        "overall_hash": str|None,  
        "notes": [...]  
      }  
  
    Sanitization:  
    - drops suspicious keys (password/secret/token/cookie/authorization)  
    - truncates long strings (>500 chars) except paths  
    - drops traceback/stack fields  
    """  
    src = record if isinstance(record, dict) else {}  
  
    # First sanitize the full input to avoid accidentally carrying secrets into derived fields.  
    cleaned = _sanitize_obj(src)  
  
    # Pull common fields from sanitized source  
    run_id = _pick_first(cleaned, ["run_id", "replay_of", "id"])  
    workflow = _pick_first(cleaned, ["workflow", "workflow_name", "workflow_path"])  
  
    success = _to_bool_success(_pick_first(cleaned, ["success", "ok", "passed", "status"]))  
    # Duration may appear under different keys  
    duration_ms = _duration_ms_from_any(  
        _pick_first(cleaned, ["duration_ms", "durationMillis", "duration", "duration_seconds", "elapsed_ms", "elapsed"])  
    )  
  
    # Failure category often comes from REASON/report fields  
    failure_category = _pick_first(  
        cleaned,  
        [  
            "failure_category",  
            "category",  
            "error_category",  
        ],  
    )  
    if isinstance(cleaned.get("diagnosis"), dict) and failure_category is None:  
        failure_category = cleaned["diagnosis"].get("category")  
    if isinstance(cleaned.get("failure"), dict) and failure_category is None:  
        failure_category = cleaned["failure"].get("error_type")  
  
    artifacts_dir = _pick_first(cleaned, ["artifacts_dir", "artifacts", "artifacts_path"])  
    report_dir = _pick_first(cleaned, ["report_dir", "reports_dir", "reports"])  
    patch_path = _pick_first(cleaned, ["patch_path", "patch_md", "patch_json"])  
  
    overall_hash = _pick_first(cleaned, ["overall_hash", "fingerprint_overall_hash"])  
    if isinstance(cleaned.get("fingerprint"), dict) and overall_hash is None:  
        overall_hash = cleaned["fingerprint"].get("overall_hash")  
  
    # Notes: keep small + sanitized  
    notes: List[str] = []  
    raw_notes = cleaned.get("notes")  
    if isinstance(raw_notes, list):  
        for n in raw_notes:  
            if n is None:  
                continue  
            s = _truncate_string(str(n), keep_long=False)  
            if len(s) > _MAX_NOTES_ITEM:  
                s = s[:_MAX_NOTES_ITEM] + "...(truncated)"  
            notes.append(s)  
  
    # If error summary exists, keep short form  
    err_msg = _pick_first(cleaned, ["error_message", "message", "error"])  
    if isinstance(cleaned.get("failure"), dict) and err_msg is None:  
        err_msg = cleaned["failure"].get("error_message")  
    if isinstance(err_msg, str) and err_msg.strip():  
        notes.append(_truncate_string(err_msg.strip(), keep_long=False))  
  
    # If ts present, prefer it; else now  
    ts_utc = _pick_first(cleaned, ["ts_utc", "timestamp_utc", "generated_at", "ts"])  
    if not isinstance(ts_utc, str) or not ts_utc.strip():  
        ts_utc = _utc_now_iso()  
  
    # Canonical record (only safe fields)  
    canonical = {  
        "ts_utc": ts_utc,  
        "run_id": str(run_id) if run_id is not None else None,  
        "workflow": str(workflow) if workflow is not None else None,  
        "success": bool(success) if success is not None else False,  
        "duration_ms": duration_ms,  
        "failure_category": str(failure_category) if failure_category is not None else None,  
        "artifacts_dir": str(artifacts_dir) if artifacts_dir is not None else None,  
        "report_dir": str(report_dir) if report_dir is not None else None,  
        "patch_path": str(patch_path) if patch_path is not None else None,  
        "overall_hash": str(overall_hash) if overall_hash is not None else None,  
        "notes": notes,  
    }  
    return canonical  
  
  
def append_run_history(record: dict, *, history_path: str | Path = "history/run_history.jsonl") -> Path:  
    """  
    Append-only: writes one JSON object per line (UTF-8). Never rewrites existing file.  
    """  
    hp = Path(history_path)  
    hp.parent.mkdir(parents=True, exist_ok=True)  
  
    row = sanitize_run_record(record)  
    line = json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"  
    with hp.open("a", encoding="utf-8") as f:  
        f.write(line)  
    return hp  
  
  
def read_run_history(*, history_path: str | Path = "history/run_history.jsonl", limit: int = 200) -> List[dict]:  
    """  
    Reads up to the last `limit` records (best-effort).  
    """  
    hp = Path(history_path)  
    if not hp.exists():  
        return []  
  
    if limit <= 0:  
        return []  
  
    buf: deque[dict] = deque(maxlen=limit)  
    with hp.open("r", encoding="utf-8", errors="replace") as f:  
        for line in f:  
            s = line.strip()  
            if not s:  
                continue  
            try:  
                obj = json.loads(s)  
                if isinstance(obj, dict):  
                    buf.append(obj)  
            except Exception:  
                continue  
    return list(buf)  
  
  
def summarize_history(rows: List[dict]) -> dict:  
    total = len(rows)  
    if total == 0:  
        return {  
            "total_runs": 0,  
            "success_rate": 0.0,  
            "top_workflows": [],  
            "top_failure_categories": [],  
            "last_run_ts": None,  
        }  
  
    successes = 0  
    wf_counter: Counter[str] = Counter()  
    cat_counter: Counter[str] = Counter()  
    last_ts: Optional[str] = None  
  
    for r in rows:  
        if not isinstance(r, dict):  
            continue  
        if r.get("success") is True:  
            successes += 1  
  
        wf = r.get("workflow")  
        if isinstance(wf, str) and wf.strip():  
            wf_counter[wf.strip()] += 1  
  
        cat = r.get("failure_category")  
        if isinstance(cat, str) and cat.strip():  
            cat_counter[cat.strip()] += 1  
  
        ts = r.get("ts_utc")  
        if isinstance(ts, str) and ts.strip():  
            if last_ts is None or ts > last_ts:  
                last_ts = ts  
  
    success_rate = successes / total if total else 0.0  
  
    return {  
        "total_runs": total,  
        "success_rate": float(success_rate),  
        "top_workflows": [{"workflow": k, "count": int(v)} for k, v in wf_counter.most_common(10)],  
        "top_failure_categories": [{"category": k, "count": int(v)} for k, v in cat_counter.most_common(10)],  
        "last_run_ts": last_ts,  
    }  