# dev/dev_smoke_doc_1a_library_index.py  
from __future__ import annotations  
  
import json  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from DOC.doc_1a_library_index import generate_library_index  
  
  
def _read_json(p: Path) -> dict:  
    return json.loads(p.read_text(encoding="utf-8"))  
  
  
def _looks_like_repo_root(p: Path) -> bool:  
    if not p.exists() or not p.is_dir():  
        return False  
    if (p / "DOC").is_dir() and (p / "SCHEMA").is_dir():  
        return True  
    if (p / "DOC" / "library_index.json").exists():  
        return True  
    if any((p / d).is_dir() for d in ("ACT", "PIPE", "STATE", "ENTRY")):  
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
    doc_dir = repo_root / "DOC"  
    out_json = doc_dir / "library_index.json"  
  
    # Run generator  
    idx = generate_library_index(repo_root=repo_root)  
  
    # Assert JSON written and non-empty  
    assert out_json.exists(), f"Missing: {out_json}"  
    obj = _read_json(out_json)  
    assert isinstance(obj, dict)  
    assert obj.get("modules"), "Expected non-empty 'modules'"  
  
    modules = obj.get("modules") or []  
    smoke = obj.get("smoke_tests") or []  
    pkgs = obj.get("top_level_packages") or []  
  
    print("PASS: DOC-1A (library index)")  
    print(f"  json:        {out_json.as_posix()}")  
    print(f"  module_count:{len(modules)}")  
    print(f"  smoke_count: {len(smoke)}")  
    print(f"  packages:    {', '.join(pkgs) if pkgs else '(none)'}")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  