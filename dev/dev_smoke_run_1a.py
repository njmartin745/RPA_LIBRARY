# dev/dev_smoke_run_1a.py  
from __future__ import annotations  
  
import json  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from RUN.run_1a_workflow_runner import run_workflow  
  
  
def _find_repo_root(start: Path) -> Path:  
    s = start.parent if start.is_file() else start  
    for cand in [s, *s.parents]:  
        if (cand / "SCHEMA" / "steps_schema.json").exists() and (cand / "PIPE").is_dir():  
            return cand  
    return s  
  
  
def _read_json(p: Path) -> dict:  
    return json.loads(p.read_text(encoding="utf-8"))  
  
  
def _choose_safe_action(schema_obj: dict) -> str:  
    supported = schema_obj.get("supported_actions") or []  
    entries = [e for e in supported if isinstance(e, dict) and isinstance(e.get("action"), str)]  
    if not entries:  
        raise AssertionError("No actions in schema")  
  
    def score(e: dict) -> tuple:  
        a = (e.get("action") or "").lower()  
        desc = (e.get("description") or "").lower()  
        req = [x for x in (e.get("required_fields") or []) if isinstance(x, str) and x != "action"]  
        # Prefer "wait/sleep/log/noop" style actions if present, then fewer required fields  
        kw = 0  
        for k in ("wait", "sleep", "pause", "log", "noop"):  
            if k in a or k in desc:  
                kw += 1  
        return (-kw, len(req), a)  
  
    best = sorted(entries, key=score)[0]  
    return best["action"]  
  
  
def _build_step(schema_obj: dict, action: str) -> dict:  
    supported = schema_obj.get("supported_actions") or []  
    entry = next(e for e in supported if isinstance(e, dict) and e.get("action") == action)  
    req = [x for x in (entry.get("required_fields") or []) if isinstance(x, str) and x != "action"]  
  
    step = {"action": action}  
    for f in req:  
        if f in ("seconds", "timeout", "timeout_seconds"):  
            step[f] = 1  
        elif f in ("url", "href", "page", "target_url"):  
            step[f] = "https://example.com"  
        elif f in ("selector",):  
            step[f] = "body"  
        else:  
            step[f] = f"TODO_{f.upper()}"  
    return step  
  
  
def main() -> int:  
    repo_root = _find_repo_root(Path(__file__).resolve())  
  
    schema = _read_json(repo_root / "SCHEMA" / "steps_schema.json")  
    action = _choose_safe_action(schema)  
  
    wf = {  
        "name": "smoke-run-1a",  
        "version": "1.0",  
        "description": "RUN-1A smoke test workflow",  
        "defaults": {"headless": True},  
        # keep worklist optional; PIPE may ignore if not required  
        "steps": [  
            _build_step(schema, action),  
        ],  
    }  
  
    tmp_dir = repo_root / ".dev_tmp"  
    tmp_dir.mkdir(parents=True, exist_ok=True)  
    wf_path = tmp_dir / "run_1a_smoke_workflow.json"  
    wf_path.write_text(json.dumps(wf, indent=2), encoding="utf-8")  
  
    summary = run_workflow(wf_path, cfg_overrides={"headless": True})  
  
    assert isinstance(summary, dict)  
    assert summary.get("workflow") == "smoke-run-1a"  
    assert isinstance(summary.get("run_id"), str) and summary["run_id"]  
    assert isinstance(summary.get("steps_executed"), int) and summary["steps_executed"] >= 1  
    assert isinstance(summary.get("errors"), list)  
    assert isinstance(summary.get("artifacts"), list)  
    assert isinstance(summary.get("success"), bool)  
  
    print("PASS: RUN-1A")  
    print(f"  workflow: {summary.get('workflow')}")  
    print(f"  run_id: {summary.get('run_id')}")  
    print(f"  steps_executed: {summary.get('steps_executed')}")  
    print(f"  pipe: {summary.get('pipe_entrypoint')}")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  