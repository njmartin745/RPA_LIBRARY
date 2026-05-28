# dev_smoke_selector_1a.py  
from __future__ import annotations  
  
import json  
import tempfile  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from SELECTOR.selector_1a_registry import get_selector, load_selectors, resolve_selector  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory() as td:  
        tmp = Path(td)  
        data_dir = tmp / "data"  
        data_dir.mkdir(parents=True, exist_ok=True)  
        selectors_path = data_dir / "selectors.json"  
  
        selectors_obj = {  
            "login": {  
                "username_input": {"css": "#username", "xpath": "//input[@name='username']"},  
                "password_input": {"css": "#password"},  
                "submit_button": {"css": "button[type='submit']"},  
            }  
        }  
        selectors_path.write_text(json.dumps(selectors_obj, indent=2), encoding="utf-8")  
  
        # 1) Load registry  
        reg = load_selectors(selectors_path=selectors_path)  
        assert isinstance(reg, dict)  
  
        # 2) Resolve selector path  
        sel = get_selector("login.username_input", registry=reg)  
        assert sel["strategy"] == "css"  
        assert sel["selector"] == "#username"  
  
        # 3) Confirm resolver injects selector into step dict  
        step = {"action": "click", "selector_ref": "login.username_input"}  
        resolved = resolve_selector(step, registry=reg)  
        assert resolved.get("selector") == "#username"  
        assert resolved.get("selector_strategy") == "css"  
        assert "selector_ref" not in resolved  
  
    print("PASS: SELECTOR-1A")  
    print(f"  temp selectors.json created and validated")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  