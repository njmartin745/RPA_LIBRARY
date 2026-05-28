# dev_smoke_act_action_engine.py  
"""  
Dev smoke test for ACT-1A action engine.  
  
- Uses ENTRY-1A webdriver bootstrap  
- Opens example.com  
- Runs a small varied set of step types  
- Prints structured results  
  
Run:  
  python dev_smoke_act_action_engine.py  
"""  
  
from __future__ import annotations  
  
import json  

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from ENTRY.entry_1a_webdriver_bootstrap import make_driver  
from ACT.act_1a_action_engine import run_actions, outcomes_as_dicts  
  
  
def main() -> int:  
    cfg = {  
        "BROWSER": "edge",  
        "HEADLESS": "true",  
        "EXPLICIT_WAIT": 15,  
        "DOWNLOAD_DIR": "downloads",  
        "URL": "https://example.com",  
    }  
  
    driver = make_driver(cfg)  
    try:  
        steps = [  
            {"action": "get", "url": "${URL}", "name": "Open example.com"},  
            {"action": "wait_for_element", "by": "css", "selector": "h1", "condition": "visible"},  
            {  
                "action": "js",  
                "name": "Read title via JS contract",  
                "script": "return {ok:true, title: document.title, url: location.href};",  
                "save_as": "PAGE",  
            },  
            {"action": "assert", "expr": "PAGE['ok'] and 'Example Domain' in PAGE.get('title','')"},  
            {"action": "click", "by": "css", "selector": "a", "name": "Click the IANA link"},  
        ]  
  
        outcomes = run_actions(driver, steps, cfg, fail_fast=True)  
        print(json.dumps(outcomes_as_dicts(outcomes), indent=2))  
        print("cfg.PAGE:", json.dumps(cfg.get("PAGE", {}), indent=2))  
        return 0  
    finally:  
        driver.quit()  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  