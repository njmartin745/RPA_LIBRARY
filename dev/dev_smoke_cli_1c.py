"""  
How to run:  
  python dev/dev_smoke_cli_1c.py  
"""  
  
from __future__ import annotations  

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from CLI.cli_1c_args_overrides import apply_overrides, build_arg_parser  
  
  
def main() -> int:  
    base_cfg = {  
        "BROWSER": "edge",  
        "HEADLESS": False,  
        "STOP_ON_ERROR": False,  
        "MAX_ITEMS": 999,  
    }  
  
    parser = build_arg_parser()  
    args = parser.parse_args(["--browser", "chrome", "--headless", "true", "--max-items", "2"])  
  
    new_cfg = apply_overrides(base_cfg, args)  
  
    assert base_cfg["BROWSER"] == "edge"  # not mutated  
    assert base_cfg["HEADLESS"] is False  
    assert new_cfg["BROWSER"] == "chrome"  
    assert new_cfg["HEADLESS"] is True  
    assert new_cfg["MAX_ITEMS"] == 2  
  
    print("PASS: dev_smoke_cli_1c")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  