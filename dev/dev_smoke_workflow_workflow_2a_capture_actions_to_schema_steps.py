from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from WORKFLOW.workflow_2a_capture_actions_to_schema_steps import dev_smoke  
  
__all__ = ["dev_smoke"]  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("PASS")  