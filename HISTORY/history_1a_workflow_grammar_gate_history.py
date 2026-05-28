"""  
HISTORY-1A: Workflow grammar gate history.  
  
Single responsibility:  
- Persist and load workflow-grammar-gate run records to/from a JSONL file, with  
  deterministic serialization and deterministic run_id derivation (when omitted).  
"""  
  
from __future__ import annotations  
  
import hashlib  
import json  
from pathlib import Path  
from typing import Any, Dict, List, Mapping, Optional  
  
__all__ = [  
    "HISTORY_SCHEMA_ID",  
    "derive_run_id_workflow_grammar_gate",  
    "build_workflow_grammar_gate_history_record",  
    "append_workflow_grammar_gate_history_jsonl",  
    "read_workflow_grammar_gate_history_jsonl",  
]  
  
HISTORY_SCHEMA_ID = "HISTORY-1A.workflow_grammar_gate"  
  
  
def derive_run_id_workflow_grammar_gate(  
    *,  
    root_dir: str,  
    mode: str,  
    exit_code: int,  
    report_text: str,  
) -> str:  
    """  
    Deterministically derive a run_id from primary outputs.  
  
    This is intentionally stable and does not use time/randomness.  
    """  
    payload = f"{root_dir}\n{mode}\n{int(exit_code)}\n{report_text}"  
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()  
    return f"wggh_{digest}"  
  
  
def build_workflow_grammar_gate_history_record(  
    *,  
    root_dir: str,  
    mode: str,  
    ok: bool,  
    exit_code: int,  
    report_text: str,  
    report: Optional[Dict[str, Any]] = None,  
    run_id: Optional[str] = None,  
    meta: Optional[Mapping[str, Any]] = None,  
) -> Dict[str, Any]:  
    """  
    Build a JSON-serializable history record dict.  
  
    Notes:  
    - No timestamps are generated here (caller may pass them in meta).  
    - If run_id is omitted, it is derived deterministically.  
    """  
    rid = run_id or derive_run_id_workflow_grammar_gate(  
        root_dir=str(root_dir),  
        mode=str(mode),  
        exit_code=int(exit_code),  
        report_text=str(report_text),  
    )  
  
    rec: Dict[str, Any] = {  
        "schema": HISTORY_SCHEMA_ID,  
        "run_id": str(rid),  
        "root_dir": str(root_dir),  
        "mode": str(mode),  
        "ok": bool(ok),  
        "exit_code": int(exit_code),  
        "report_text": str(report_text),  
        "report": report,  
    }  
    if meta is not None:  
        rec["meta"] = dict(meta)  
    return rec  
  
  
def append_workflow_grammar_gate_history_jsonl(path: str, record: Mapping[str, Any]) -> None:  
    """  
    Append a single record as JSON to a JSONL file (one line per record),  
    with deterministic serialization.  
    """  
    p = Path(path)  
    p.parent.mkdir(parents=True, exist_ok=True)  
  
    line = json.dumps(  
        dict(record),  
        ensure_ascii=False,  
        sort_keys=True,  
        separators=(",", ":"),  
    )  
    with p.open("a", encoding="utf-8", newline="\n") as f:  
        f.write(line)  
        f.write("\n")  
  
  
def read_workflow_grammar_gate_history_jsonl(path: str) -> List[Dict[str, Any]]:  
    """  
    Read a JSONL history file into a list of dict records.  
    Missing file => empty list.  
    """  
    p = Path(path)  
    if not p.exists():  
        return []  
  
    out: List[Dict[str, Any]] = []  
    with p.open("r", encoding="utf-8") as f:  
        for raw in f:  
            s = raw.strip()  
            if not s:  
                continue  
            out.append(json.loads(s))  
    return out  