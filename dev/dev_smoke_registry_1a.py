# dev_smoke_registry_1a.py  
from __future__ import annotations  
  
import json  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from REGISTRY.registry_1a_generate import generate_action_registry  
  
  
def _read_json(p: Path) -> dict:  
    return json.loads(p.read_text(encoding="utf-8"))  
  
  
def _looks_like_repo_root(p: Path) -> bool:  
    if not p.exists() or not p.is_dir():  
        return False  
    if (p / "SCHEMA" / "steps_schema.json").exists():  
        return True  
    if (p / "DOC" / "library_index.json").exists():  
        return True  
    if (p / "REGISTRY").is_dir() and (p / "SCHEMA").is_dir():  
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
    out_dir = repo_root / "REGISTRY"  
  
    # Run generator  
    generate_action_registry(repo_root=repo_root, out_dir=out_dir)  
  
    json_path = out_dir / "action_registry.json"  
    md_path = out_dir / "action_registry.md"  
  
    # Assert both files exist  
    assert json_path.exists(), f"Missing: {json_path}"  
    assert md_path.exists(), f"Missing: {md_path}"  
  
    # Assert JSON valid  
    reg = _read_json(json_path)  
    assert isinstance(reg, dict)  
    assert isinstance(reg.get("actions"), list)  
  
    # Assert registry contains >= number of actions in steps_schema.json  
    schema_path = repo_root / "SCHEMA" / "steps_schema.json"  
    schema = _read_json(schema_path)  
    supported = schema.get("supported_actions")  
    assert isinstance(supported, list), "steps_schema.json supported_actions must be a list"  
  
    reg_actions = reg.get("actions") or []  
    assert len(reg_actions) >= len(supported), f"Expected registry >= schema actions; got {len(reg_actions)} vs {len(supported)}"  
  
    # minimal shape checks  
    for a in reg_actions:  
        assert isinstance(a, dict)  
        assert isinstance(a.get("action"), str)  
        assert "implemented_by" in a and isinstance(a["implemented_by"], dict)  
  
    print("PASS: REGISTRY-1A")  
    print(f"  json: {json_path.as_posix()}")  
    print(f"  md:   {md_path.as_posix()}")  
    print(f"  actions: {len(reg_actions)} (schema had {len(supported)})")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  