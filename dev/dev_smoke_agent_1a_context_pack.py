# dev/dev_smoke_agent_1a_context_pack.py  
from __future__ import annotations  
  
import json  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from AGENT.agent_1a_context_pack import generate_agent_context_pack  
  
  
def _read_json(p: Path) -> dict:  
    return json.loads(p.read_text(encoding="utf-8"))  
  
  
def _looks_like_repo_root(p: Path) -> bool:  
    if not p.exists() or not p.is_dir():  
        return False  
    if (p / "SCHEMA" / "steps_schema.json").exists() and (p / "DOC" / "library_index.json").exists():  
        return True  
    if (p / "DOC" / "library_index.json").exists():  
        return True  
    return False  
  
  
def _find_repo_root(start: Path) -> Path:  
    s = start.parent if start.is_file() else start  
    for cand in [s, *s.parents]:  
        if _looks_like_repo_root(cand):  
            return cand  
    return s  
  
  
def main() -> int:  
    repo_root = _find_repo_root(Path(__file__).resolve())  
    packet = generate_agent_context_pack(repo_root=repo_root)  
  
    md_path = repo_root / "DOC" / "AGENT_PACKET.md"  
    json_path = repo_root / "DOC" / "agent_packet.json"  
  
    assert md_path.exists(), f"Missing: {md_path}"  
    assert json_path.exists(), f"Missing: {json_path}"  
    assert md_path.read_text(encoding="utf-8").strip(), "AGENT_PACKET.md is empty"  
  
    obj = _read_json(json_path)  
    assert isinstance(obj, dict)  
    assert obj.get("modules"), "agent_packet.json missing modules"  
    assert obj.get("actions"), "agent_packet.json missing actions"  
  
    module_count = len(obj.get("modules") or [])  
    action_count = len(obj.get("actions") or [])  
    smoke_count = len(obj.get("smoke_test_mapping") or [])  
  
    print("PASS: AGENT-1A")  
    print(f"  md:    {md_path.as_posix()}")  
    print(f"  json:  {json_path.as_posix()}")  
    print(f"  modules: {module_count}  actions: {action_count}  smoke_tests: {smoke_count}")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  