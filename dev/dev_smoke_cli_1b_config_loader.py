"""  
How to run:  
  python dev/dev_smoke_cli_1b_config_loader.py  
"""  
  
from __future__ import annotations  
  
import os  
import tempfile  
import traceback  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from CLI.cli_1b_config_loader import load_config  
  
  
def main() -> int:  
    try:  
        os.environ["RUN_ID"] = "R123"  
  
        with tempfile.TemporaryDirectory(prefix="dev_smoke_cli_1b_") as td:  
            p = Path(td) / "config.yaml"  
            p.write_text(  
                "\n".join(  
                    [  
                        "BROWSER: edge",  
                        "HEADLESS: true",  
                        "RUN_ID: ${RUN_ID}",  
                        "STEPS: []",  
                    ]  
                ),  
                encoding="utf-8",  
            )  
  
            cfg = load_config(str(p))  
  
            ok = True  
            ok = ok and (cfg.get("BROWSER") == "edge")  
            ok = ok and (cfg.get("HEADLESS") is True)  
            ok = ok and (cfg.get("RUN_ID") == "R123")  
  
            print("\n=== dev_smoke_cli_1b_config_loader ===")  
            print(f"config_path: {p}")  
            print(cfg)  
  
            if ok:  
                print("PASS: dev_smoke_cli_1b_config_loader")  
                return 0  
            print("FAIL: dev_smoke_cli_1b_config_loader")  
            return 1  
  
    except Exception as e:  
        print("\nFAIL: dev_smoke_cli_1b_config_loader (exception)")  
        print(f"Error: {type(e).__name__}: {e}")  
        traceback.print_exc()  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  