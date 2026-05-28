# dev/dev_smoke_schema_1a.py  
from __future__ import annotations  
  
import json  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from SCHEMA.schema_1a_generate import generate_steps_schema  
  
  
def _read_json(p: Path) -> dict:  
    return json.loads(p.read_text(encoding="utf-8"))  
  
  
def _looks_like_repo_root(p: Path) -> bool:  
    if not p.exists() or not p.is_dir():  
        return False  
    if (p / "LIBRARY_MAP.md").exists():  
        return True  
    if (p / "DOC" / "library_index.json").exists():  
        return True  
    if any((p / d).is_dir() for d in ("ACT", "PIPE", "VAL", "NAV")):  
        return True  
    if (p / "SCHEMA").is_dir():  
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
    out_dir = repo_root / "SCHEMA"  
  
    # 1) run generator  
    generate_steps_schema(repo_root=repo_root, out_dir=out_dir, prefer_library_index=True)  
  
    # 2) confirm schema files exist  
    schema_path = out_dir / "steps_schema.json"  
    examples_path = out_dir / "steps_examples.json"  
  
    assert schema_path.exists(), f"Missing: {schema_path}"  
    assert examples_path.exists(), f"Missing: {examples_path}"  
  
    # 3) confirm JSON is valid  
    schema_obj = _read_json(schema_path)  
    examples_obj = _read_json(examples_path)  
  
    assert isinstance(schema_obj, dict)  
    assert isinstance(examples_obj, dict)  
  
    # 4) confirm at least 8 actions exist  
    actions = schema_obj.get("supported_actions")  
    assert isinstance(actions, list), "supported_actions must be a list"  
    assert len(actions) >= 8, f"Expected >= 8 actions, got {len(actions)}"  
  
    # basic shape checks  
    for a in actions:  
        assert isinstance(a, dict)  
        assert "action" in a and isinstance(a["action"], str)  
        assert "required_fields" in a and isinstance(a["required_fields"], list)  
        assert "optional_fields" in a and isinstance(a["optional_fields"], list)  
  
    # 5) print PASS banner with paths  
    print("PASS: SCHEMA-1A")  
    print(f"  schema:    {schema_path.as_posix()}")  
    print(f"  examples:  {examples_path.as_posix()}")  
    print(f"  actions:   {len(actions)}")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  