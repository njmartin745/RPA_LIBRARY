"""  
HISTORY-1B — Step outcomes recorder (10.2.2)  
  
Single responsibility:  
- Build and append per-step outcome records to a JSONL file under a run output dir.  
  
This module does NOT:  
- normalize exceptions/tracebacks in a structured way (10.2.3)  
- run steps or interact with Selenium  
"""  
  
from __future__ import annotations  
  
import datetime as _dt  
import json  
import os  
from pathlib import Path  
from typing import Any, Mapping  
  
__all__ = [  
    "build_step_outcome",  
    "append_step_outcome",  
    "dev_smoke",  
]  
  
  
def _utc_now_iso() -> str:  
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()  
  
  
def _stable_json_line(obj: Any) -> str:  
    # Deterministic JSONL encoding: sorted keys, ascii, stable separators.  
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))  
  
  
def _redact_step(step: Mapping[str, Any]) -> dict[str, Any]:  
    """  
    Best-effort redaction to avoid writing secrets into history.  
    - If a key contains 'secret' (case-insensitive), replace string values with '<redacted>'.  
    - Recurse into dicts/lists.  
    """  
    def walk(v: Any, k: str | None = None) -> Any:  
        if isinstance(v, Mapping):  
            out: dict[str, Any] = {}  
            for kk, vv in v.items():  
                out[str(kk)] = walk(vv, str(kk))  
            return out  
        if isinstance(v, list):  
            return [walk(x, k) for x in v]  
        if isinstance(v, tuple):  
            return [walk(x, k) for x in v]  
        if k is not None and "secret" in k.lower() and isinstance(v, str):  
            return "<redacted>"  
        return v  
  
    return walk(dict(step))  # type: ignore[return-value]  
  
  
def build_step_outcome(  
    *,  
    workflow_name: str,  
    step_index: int,  
    step: Mapping[str, Any],  
    status: str,  
    started_at_utc: str | None = None,  
    finished_at_utc: str | None = None,  
    error: BaseException | None = None,  
    notes: str | None = None,  
) -> dict[str, Any]:  
    """  
    Build a JSON-serializable outcome record.  
  
    status: typically 'ok' or 'error' (kept flexible).  
    error: captured minimally as {class, message} (full normalization in 10.2.3).  
    """  
    if started_at_utc is None:  
        started_at_utc = _utc_now_iso()  
  
    err_obj: dict[str, Any] | None = None  
    if error is not None:  
        # Keep deterministic: class + message only (no repr() which can vary).  
        err_obj = {  
            "class": error.__class__.__name__,  
            "message": str(error),  
        }  
  
    rec: dict[str, Any] = {  
        "schema": "HISTORY-1B",  
        "workflow_name": workflow_name,  
        "step_index": int(step_index),  
        "step": _redact_step(step),  
        "status": str(status),  
        "timestamps": {  
            "started_at_utc": started_at_utc,  
            "finished_at_utc": finished_at_utc,  
        },  
        "error": err_obj,  
        "notes": notes,  
    }  
    return rec  
  
  
def append_step_outcome(  
    *,  
    run_output_dir: str | os.PathLike[str],  
    outcome: Mapping[str, Any],  
) -> dict[str, Any]:  
    """  
    Append one outcome record to:  
      {run_output_dir}/history/step_outcomes.jsonl  
  
    Returns a small write-result payload.  
    """  
    root = Path(run_output_dir)  
    out_path = root / "history" / "step_outcomes.jsonl"  
    out_path.parent.mkdir(parents=True, exist_ok=True)  
  
    line = _stable_json_line(dict(outcome)) + "\n"  
    # newline normalization: always write '\n' (text mode with newline='\n')  
    with out_path.open("a", encoding="utf-8", newline="\n") as f:  
        f.write(line)  
  
    return {  
        "schema": "HISTORY-1B-APPEND",  
        "path": str(out_path),  
        "path_relative": out_path.resolve().relative_to(root.resolve()).as_posix(),  
        "bytes_appended": len(line.encode("utf-8")),  
    }  
  
  
def dev_smoke() -> None:  
    repo_root = Path(__file__).resolve().parents[1]  
    out_root = repo_root / "dev" / "_smoke_artifacts" / "10_2_2"  
  
    # deterministic cleanup  
    if out_root.exists():  
        for p in sorted(out_root.rglob("*"), key=lambda x: str(x), reverse=True):  
            if p.is_file():  
                p.unlink()  
            elif p.is_dir():  
                try:  
                    p.rmdir()  
                except OSError:  
                    pass  
        try:  
            out_root.rmdir()  
        except OSError:  
            pass  
  
    out_root.mkdir(parents=True, exist_ok=True)  
  
    step1 = {"action": "open", "url": "https://example.com"}  
    step2 = {"action": "type_selector_secret", "selector_ref": "login.password", "secret_value": "SHOULD_NOT_APPEAR"}  
  
    rec1 = build_step_outcome(  
        workflow_name="wf",  
        step_index=0,  
        step=step1,  
        status="ok",  
        started_at_utc="2026-01-01T00:00:00+00:00",  
        finished_at_utc="2026-01-01T00:00:01+00:00",  
    )  
    rec2 = build_step_outcome(  
        workflow_name="wf",  
        step_index=1,  
        step=step2,  
        status="error",  
        started_at_utc="2026-01-01T00:00:02+00:00",  
        finished_at_utc="2026-01-01T00:00:03+00:00",  
        error=ValueError("bad input"),  
    )  
  
    w1 = append_step_outcome(run_output_dir=out_root, outcome=rec1)  
    w2 = append_step_outcome(run_output_dir=out_root, outcome=rec2)  
  
    assert w1["schema"] == "HISTORY-1B-APPEND"  
    assert w2["path_relative"] == "history/step_outcomes.jsonl"  
  
    jsonl_path = out_root / "history" / "step_outcomes.jsonl"  
    content = jsonl_path.read_text(encoding="utf-8").splitlines()  
  
    assert len(content) == 2  
  
    # Exact deterministic line match  
    expected1 = _stable_json_line(rec1)  
    expected2 = _stable_json_line(rec2)  
    assert content[0] == expected1  
    assert content[1] == expected2  
  
    # Ensure redaction occurred  
    assert "SHOULD_NOT_APPEAR" not in jsonl_path.read_text(encoding="utf-8")  
    assert "<redacted>" in jsonl_path.read_text(encoding="utf-8")  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: HISTORY.history_1b_step_outcomes")  