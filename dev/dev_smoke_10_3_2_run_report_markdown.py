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
  
    from REPORT.report_1b_run_report_markdown import dev_smoke  
  
    dev_smoke()  
    print("DEV_SMOKE_OK: 10.3.2 run report markdown (report/run_report.md)")  
  
  
if __name__ == "__main__":  
    main()  