"""  
Dev bootstrap: ensure repo root is on sys.path.  
  
When running:  
  python dev/dev_smoke_state_input.py  
  
Python typically puts the *dev/* directory on sys.path (not the repo root),  
so imports like `import INPUT...` can fail. This file is auto-imported by  
Python's `site` module (unless -S is used) and adds the repo root deterministically.  
"""  
  
from __future__ import annotations  
  
import sys  
from pathlib import Path  

ROOT = Path(__file__).resolve().parents[1]  
if str(ROOT) not in sys.path:  
    sys.path.insert(0, str(ROOT)) 
      
__all__ = ["ensure_repo_root_on_syspath", "dev_smoke"]  
  
  
def ensure_repo_root_on_syspath() -> Path:  
    dev_dir = Path(__file__).resolve().parent  
    repo_root = dev_dir.parent  
    repo_root_s = str(repo_root)  
    if repo_root_s not in sys.path:  
        sys.path.insert(0, repo_root_s)  
    return repo_root  
  
  
# Run on import (deterministic, no side effects beyond sys.path fix)  
ensure_repo_root_on_syspath()  
  
  
def dev_smoke() -> None:  
    root = ensure_repo_root_on_syspath()  
    assert (root / "INPUT").exists()  