# dev/dev_smoke_workflow_1a_loader.py  
from __future__ import annotations  

import json  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from WORKFLOWS.workflow_1a_loader import load_validate_normalize_workflow  
  
  
def _looks_like_repo_root(p: Path) -> bool:  
    return (p / "SCHEMA" / "steps_schema.json").exists() and (p / "DOC" / "library_index.json").exists()  
  
  
def _find_repo_root(start: Path) -> Path:  
    s = start.parent if start.is_file() else start  
    for cand in [s, *s.parents]:  
        if _looks_like_repo_root(cand):  
            return cand  
    return s  
  
  
def _read_json(p: Path) -> dict:  
    return json.loads(p.read_text(encoding="utf-8"))  
  
  
def _build_min_step_from_schema(schema_obj: dict, action: str) -> dict:  
    # required-only (presence check only in loader, so placeholders are fine)  
    supported = schema_obj.get("supported_actions") or []  
    entry = None  
    for e in supported:  
        if isinstance(e, dict) and e.get("action") == action:  
            entry = e  
            break  
    assert entry is not None  
  
    step = {"action": action}  
    for f in (entry.get("required_fields") or []):  
        if f == "action":  
            continue  
        # placeholder values (types not enforced here)  
        if f in ("url", "href", "page", "target_url"):  
            step[f] = "https://example.com"  
        elif f in ("seconds", "timeout", "timeout_seconds"):  
            step[f] = 2  
        else:  
            step[f] = f"TODO_{f.upper()}"  
    return step  
  
  
def main() -> int:  
    repo_root = _find_repo_root(Path(__file__).resolve())  
  
    schema_path = repo_root / "SCHEMA" / "steps_schema.json"  
    schema = _read_json(schema_path)  
    actions = [  
        e["action"]  
        for e in (schema.get("supported_actions") or [])  
        if isinstance(e, dict) and isinstance(e.get("action"), str)  
    ]  
    assert actions, "No actions found in SCHEMA/steps_schema.json"  
  
    # pick 2-3 actions with fewest required fields to keep it robust  
    def req_count(a: str) -> int:  
        for e in schema["supported_actions"]:  
            if isinstance(e, dict) and e.get("action") == a:  
                req = [x for x in (e.get("required_fields") or []) if isinstance(x, str) and x != "action"]  
                return len(req)  
        return 999999  
  
    actions_sorted = sorted(actions, key=lambda a: (req_count(a), a))  
    chosen = actions_sorted[:3] if len(actions_sorted) >= 3 else actions_sorted[:1]  
  
    steps = []  
    for a in chosen:  
        steps.append(_build_min_step_from_schema(schema, a))  
  
    # include alias normalization check on step[0] (by/value -> selector/selector_strategy)  
    steps[0]["by"] = "css"  
    steps[0]["value"] = "#todo"  
  
    wf = {  
        "name": "smoke-workflow-1a",  
        "version": "1.0",  
        "description": "workflow loader smoke test",  
        "defaults": {"headless": True, "timeout_seconds": 5},  
        "vars": {"seed_key": "seed_val"},  
        "worklist": {"path": "data/manifest.jsonl", "sheet": "Sheet1", "id_column": "id"},  
        "steps": steps,  
    }  
  
    tmp_dir = repo_root / ".dev_tmp"  
    tmp_dir.mkdir(parents=True, exist_ok=True)  
    wf_path = tmp_dir / "workflow_1a_smoke.json"  
    wf_path.write_text(json.dumps(wf, indent=2), encoding="utf-8")  
  
    workflow_norm, cfg_out, steps_out = load_validate_normalize_workflow(wf_path, repo_root=repo_root)  
  
    assert steps_out and isinstance(steps_out, list)  
    assert isinstance(steps_out[0], dict)  
    assert isinstance(steps_out[0].get("action"), str)  
  
    # normalized aliases should exist if by/value were provided  
    assert steps_out[0].get("selector") == "#todo"  
    assert steps_out[0].get("selector_strategy") == "css"  
  
    # cfg_out contains merged defaults  
    assert cfg_out.get("headless") is True  
    assert cfg_out.get("timeout_seconds") == 5  
    assert cfg_out.get("worklist_path") == "data/manifest.jsonl"  
    assert cfg_out.get("worklist_sheet") == "Sheet1"  
    assert cfg_out.get("id_column") == "id"  
  
    print("PASS: WORKFLOW-1A")  
    print(f"  workflow: {workflow_norm.get('name')}")  
    print(f"  steps: {len(steps_out)}")  
    print(f"  first action: {steps_out[0].get('action')}")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  