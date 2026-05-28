from __future__ import annotations  
  
import os  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
  
__all__ = ["main"]  
  
  
def main() -> None:  
    repo_root = os.path.dirname(os.path.dirname(__file__))  
    if repo_root not in sys.path:  
        sys.path.insert(0, repo_root)  
  
    from BUILD.build_2d_determinism import dev_smoke as determinism_dev_smoke  
  
    determinism_dev_smoke()  
    print("DEV_SMOKE_OK: 9.4.3 deterministic generation")  
  
  
if __name__ == "__main__":  
    main()  