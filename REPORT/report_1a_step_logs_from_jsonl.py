"""  
REPORT-1A — Build step_logs from LOG JSONL events.  
  
Goal  
----  
Derive per-step statuses from the JSONL event stream:  
- step_success => status="success"  
- step_error   => status="failure" + error message  
  
Key rule (fixes the behavior you are seeing)  
--------------------------------------------  
If a step already has status "success", later "step_error" events for the same step_index  
are ignored (prevents item-level "step_error" noise from overwriting real success).  
  
This module is additive and does not require changes to ACT/PIPE internals to be useful.  
"""  
  
from __future__ import annotations  
  
import json  
from pathlib import Path  
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple  
  
__all__ = [  
    "build_step_logs_from_jsonl",  
    "dev_smoke",  
]  
  
  
def _safe_json_loads(line: str) -> Optional[dict]:  
    line = line.strip()  
    if not line:  
        return None  
    try:  
        obj = json.loads(line)  
    except Exception:  
        return None  
    return obj if isinstance(obj, dict) else None  
  
  
def _pick_error_message(evt: Mapping[str, Any]) -> Optional[str]:  
    # Prefer explicit error fields; fall back to exception string; lastly message.  
    for k in ("error_message", "error", "exc"):  
        v = evt.get(k)  
        if isinstance(v, str) and v.strip():  
            return v.strip()  
  
    fields = evt.get("fields")  
    if isinstance(fields, dict):  
        v = fields.get("error_message") or fields.get("error") or fields.get("exc")  
        if isinstance(v, str) and v.strip():  
            return v.strip()  
  
    msg = evt.get("message")  
    if isinstance(msg, str) and msg.strip() and msg.strip().lower() not in {"step_error"}:  
        return msg.strip()  
  
    return None  
  
  
def _normalize_steps(steps: Optional[Sequence[Mapping[str, Any]]]) -> List[Mapping[str, Any]]:  
    if not steps:  
        return []  
    out: List[Mapping[str, Any]] = []  
    for s in steps:  
        if isinstance(s, dict):  
            out.append(s)  
    return out  
  
  
def _extract_step_basics(step: Mapping[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:  
    action = step.get("action")  
    action_s = str(action) if isinstance(action, str) else None  
  
    inputs = step.get("inputs")  
    if isinstance(inputs, dict):  
        inputs_d = dict(inputs)  
    else:  
        # SCHEMA-1A normally uses "inputs"; if absent, keep minimal deterministic fallback.  
        inputs_d = {}  
  
    return action_s, inputs_d  
  
  
def build_step_logs_from_jsonl(  
    jsonl_path: str | Path,  
    *,  
    steps: Optional[Sequence[Mapping[str, Any]]] = None,  
    run_id: Optional[str] = None,  
    current_id: Optional[str] = None,  
) -> List[Dict[str, Any]]:  
    """  
    Build step_logs from a JSONL log file.  
  
    Parameters  
    ----------  
    jsonl_path:  
        Path to the JSONL event log.  
    steps:  
        Optional list of workflow steps (SCHEMA-1A step dicts). If provided, output ordering  
        and action/inputs are taken from here.  
    run_id:  
        Optional run_id filter (recommended).  
    current_id:  
        Optional item filter. If None, we select the last current_id that had step events.  
  
    Returns  
    -------  
    List[dict] compatible with existing CLI output shape:  
      [{"index": 0, "action": "...", "inputs": {...}, "status": "success|failure|unknown", "error": "..."}]  
    """  
    p = Path(jsonl_path)  
    steps_norm = _normalize_steps(steps)  
  
    # Default unknown step logs if we have steps but no file.  
    def _unknown_from_steps() -> List[Dict[str, Any]]:  
        out: List[Dict[str, Any]] = []  
        for i, st in enumerate(steps_norm):  
            action, inputs = _extract_step_basics(st)  
            out.append({"index": i, "action": action, "inputs": inputs, "status": "unknown"})  
        return out  
  
    if not p.exists():  
        return _unknown_from_steps()  
  
    # First pass: find last current_id with step events (for this run_id filter).  
    last_step_current_id: Optional[str] = None  
    with p.open("r", encoding="utf-8") as f:  
        for line in f:  
            evt = _safe_json_loads(line)  
            if not evt:  
                continue  
            if run_id is not None and str(evt.get("run_id")) != str(run_id):  
                continue  
            if evt.get("event") in {"step_start", "step_success", "step_error"}:  
                cid = evt.get("current_id")  
                if isinstance(cid, str) and cid:  
                    last_step_current_id = cid  
  
    effective_current_id = current_id or last_step_current_id  
  
    # Second pass: build statuses.  
    status_by_index: Dict[int, str] = {}  
    error_by_index: Dict[int, str] = {}  
  
    with p.open("r", encoding="utf-8") as f:  
        for line in f:  
            evt = _safe_json_loads(line)  
            if not evt:  
                continue  
  
            if run_id is not None and str(evt.get("run_id")) != str(run_id):  
                continue  
  
            if effective_current_id is not None:  
                cid = evt.get("current_id")  
                if str(cid) != str(effective_current_id):  
                    continue  
  
            ev = evt.get("event")  
            if ev not in {"step_start", "step_success", "step_error"}:  
                continue  
  
            si = evt.get("step_index")  
            if not isinstance(si, int):  
                # Sometimes it might be nested; tolerate that deterministically.  
                fields = evt.get("fields")  
                if isinstance(fields, dict) and isinstance(fields.get("step_index"), int):  
                    si = int(fields["step_index"])  
                else:  
                    continue  
  
            # Do not allow later errors to overwrite success.  
            existing = status_by_index.get(si)  
            if existing == "success" and ev == "step_error":  
                continue  
  
            if ev == "step_success":  
                status_by_index[si] = "success"  
                error_by_index.pop(si, None)  
            elif ev == "step_error":  
                status_by_index[si] = "failure"  
                msg = _pick_error_message(evt)  
                if isinstance(msg, str) and msg.strip():  
                    error_by_index[si] = msg.strip()  
            else:  
                # step_start: only set if nothing exists yet  
                status_by_index.setdefault(si, "unknown")  
  
    # Emit ordered logs using steps list if provided; otherwise emit by observed indices.  
    if steps_norm:  
        out = _unknown_from_steps()  
        for row in out:  
            i = int(row["index"])  
            if i in status_by_index:  
                row["status"] = status_by_index[i]  
            if i in error_by_index and row.get("status") == "failure":  
                row["error"] = error_by_index[i]  
        return out  
  
    # Fallback: no steps provided; emit only observed indices.  
    out2: List[Dict[str, Any]] = []  
    for i in sorted(status_by_index.keys()):  
        row: Dict[str, Any] = {"index": i, "action": None, "inputs": {}, "status": status_by_index[i]}  
        if i in error_by_index and row["status"] == "failure":  
            row["error"] = error_by_index[i]  
        out2.append(row)  
    return out2  
  
  
def dev_smoke() -> None:  
    tmp = Path(".dev_tmp")  
    tmp.mkdir(parents=True, exist_ok=True)  
    p = tmp / "report_1a_step_logs_smoke.jsonl"  
  
    run_id = "RID123"  
    current_id = "SINGLE"  
  
    # Step 0 success, step 1 failure, then spurious late "step_error" for step 0 (should be ignored).  
    lines = [  
        {"event": "step_start", "run_id": run_id, "current_id": current_id, "step_index": 0, "action": "open"},  
        {"event": "step_success", "run_id": run_id, "current_id": current_id, "step_index": 0, "action": "open"},  
        {  
            "event": "step_error",  
            "run_id": run_id,  
            "current_id": current_id,  
            "step_index": 1,  
            "action": "wait_for_selector",  
            "error_message": "boom",  
        },  
        {  
            "event": "step_error",  
            "run_id": run_id,  
            "current_id": current_id,  
            "step_index": 0,  
            "action": "open",  
            "error_message": "spurious",  
        },  
    ]  
    p.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")  
  
    steps = [  
        {"action": "open", "inputs": {"url": "https://example.com"}},  
        {"action": "wait_for_selector", "inputs": {"selector": ".nope", "timeout": 2}},  
        {"action": "wait_for_selector", "inputs": {"selector": "body", "timeout": 2}},  
    ]  
  
    out = build_step_logs_from_jsonl(p, steps=steps, run_id=run_id)  
    assert out[0]["status"] == "success"  
    assert out[1]["status"] == "failure"  
    assert out[1]["error"] == "boom"  
    assert out[2]["status"] == "unknown"  
  
  
if __name__ == "__main__":  
    dev_smoke()  