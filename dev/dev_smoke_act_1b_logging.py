# dev_smoke_act_1b_logging.py  
"""  
Dev smoke test for ACT-1B logging integration.  
  
- Uses ENTRY-1A to create a driver  
- Uses LOG-1A for one-line JSON logs  
- Opens example.com  
- Executes 2–3 steps through ACT-1B, showing automatic step_* logs  
  
Run:  
  python dev_smoke_act_1b_logging.py  
"""  
  
from __future__ import annotations  
  
import json  

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ENTRY.entry_1a_webdriver_bootstrap import make_driver  
from LOG.log_1a_structured_logging import setup_logging  
from ACT.act_1b_logging_integration import run_actions_logged  
from ACT.act_1a_action_engine import outcomes_as_dicts  
  
  
def main() -> int:  
    cfg = {  
        "BROWSER": "edge",  
        "HEADLESS": "true",  
        "EXPLICIT_WAIT": 15,  
        "STOP_ON_ERROR": True,  
        "URL": "https://example.com",  
        # Optional per-item context demonstration:  
        "CURRENT_ID": "DEMO-1",  
        "ITEM_INDEX": 1,  
        "TOTAL_ITEMS": 1,  
    }  
  
    logger = setup_logging(cfg)  
    driver = make_driver(cfg)  
    try:  
        steps = [  
            {"action": "get", "url": "${URL}", "step_id": "s1", "name": "Open example.com"},  
            {"action": "wait_for_element", "by": "css", "selector": "h1", "step_id": "s2"},  
            {  
                "action": "js",  
                "step_id": "s3",  
                "script": "return {ok:true, title: document.title};",  
                "save_as": "PAGE",  
            },  
        ]  
  
        outcomes = run_actions_logged(driver, steps, cfg, logger=logger)  
        print(json.dumps(outcomes_as_dicts(outcomes), indent=2))  
        return 0  
    finally:  
        driver.quit()  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  