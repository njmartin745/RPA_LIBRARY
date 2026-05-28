"""  
How to run:  
  python dev/dev_smoke_val_1a.py  
"""  
  
from __future__ import annotations  
  
import importlib  
import pkgutil  
import traceback  
from typing import Any, Callable, Dict, Optional  

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from VAL.val_1a_ui_state import validate_ui_state  
  
  
def _resolve_entry_driver_factory() -> Callable[..., Any]:  
    fn_names = (  
        "create_driver",  
        "make_driver",  
        "build_driver",  
        "get_driver",  
        "create_webdriver",  
        "make_webdriver",  
        "build_webdriver",  
        "get_webdriver",  
    )  
  
    # Prefer canonical ENTRY-1A file  
    try:  
        m = importlib.import_module("ENTRY.entry_1a_webdriver_bootstrap")  
        for n in fn_names:  
            fn = getattr(m, n, None)  
            if callable(fn):  
                return fn  
    except Exception:  
        pass  
  
    # Scan ENTRY.*  
    pkg = importlib.import_module("ENTRY")  
    for mi in pkgutil.iter_modules(pkg.__path__, prefix=pkg.__name__ + "."):  
        try:  
            mod = importlib.import_module(mi.name)  
        except Exception:  
            continue  
        for n in fn_names:  
            fn = getattr(mod, n, None)  
            if callable(fn):  
                return fn  
  
    raise RuntimeError("Could not resolve ENTRY-1A driver factory.")  
  
  
def _make_driver(factory: Callable[..., Any], cfg: Dict[str, Any]) -> Any:  
    try:  
        return factory(cfg)  
    except TypeError:  
        return factory()  
  
  
def main() -> int:  
    driver: Optional[Any] = None  
    try:  
        cfg: Dict[str, Any] = {  
            "HEADLESS": True,  
            "BROWSER": "edge",  
            "EXPLICIT_WAIT": 10,  
        }  
  
        factory = _resolve_entry_driver_factory()  
        driver = _make_driver(factory, cfg)  
  
        driver.get("https://example.com")  
  
        result = validate_ui_state(  
            driver,  
            checks=[  
                {"by": "css", "value": "h1", "expect": "visible", "text_contains": "Example Domain"},  
                {"by": "css", "value": "p", "expect": "present", "text_contains": "illustrative examples"},  
                {"by": "css", "value": "a", "expect": "present", "attr": "href", "attr_contains": "iana.org"},  
            ],  
            cfg=cfg,  
        )  
  
        print("\n=== dev_smoke_val_1a ===")  
        print(result)  
  
        if result.get("ok") is True:  
            print("PASS: dev_smoke_val_1a")  
            return 0  
  
        print("FAIL: dev_smoke_val_1a")  
        return 1  
  
    except Exception as e:  
        print("\nFAIL: dev_smoke_val_1a (exception)")  
        print(f"Error: {type(e).__name__}: {e}")  
        traceback.print_exc()  
        return 1  
  
    finally:  
        try:  
            if driver is not None:  
                driver.quit()  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  