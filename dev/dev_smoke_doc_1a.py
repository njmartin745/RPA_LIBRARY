"""  
How to run:  
  python dev/dev_smoke_doc_1a.py  
"""  
  
from __future__ import annotations  
  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from DOC.doc_1a_library_index import generate_library_index  
  
  
def main() -> int:  
    repo_root = Path(__file__).resolve().parents[1]  
    out = generate_library_index(str(repo_root))  
  
    md_path = Path(out["md_path"])  
    json_path = Path(out["json_path"])  
  
    assert md_path.exists() and md_path.is_file()  
    assert json_path.exists() and json_path.is_file()  
    assert md_path.stat().st_size > 0  
    assert json_path.stat().st_size > 0  
  
    print("PASS: dev_smoke_doc_1a")  
    print(f"MD:   {md_path}")  
    print(f"JSON: {json_path}")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  