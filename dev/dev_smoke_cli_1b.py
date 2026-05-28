"""  
How to run:  
  python dev/dev_smoke_cli_1b.py  
"""  
  
from __future__ import annotations  
  
import json  
import os  
import tempfile  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from CLI.cli_1b_config_loader import load_config  
  
  
def main() -> int:  
    os.environ["TEMP_VAR"] = "hello123"  
  
    with tempfile.TemporaryDirectory(prefix="dev_smoke_cli_1b_") as td:  
        cfg_path = Path(td) / "cfg.json"  
        cfg_path.write_text(  
            json.dumps({"RUN_ID": "${TEMP_VAR}", "HEADLESS": True, "BROWSER": "edge"}),  
            encoding="utf-8",  
        )  
  
        cfg = load_config(str(cfg_path))  
  
        assert cfg["RUN_ID"] == "hello123"  
        assert cfg["HEADLESS"] is True  
        assert cfg["BROWSER"] == "edge"  
  
        print("PASS: dev_smoke_cli_1b")  
        print(f"config_path: {cfg_path}")  
        return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  