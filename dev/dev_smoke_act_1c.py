"""  
How to run:  
  python dev/dev_smoke_act_1c.py  
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

from ACT.act_1c_conditional_guards import element_exists, text_contains, should_run_step  
  
  
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
  
    # Prefer canonical ENTRY-1A file name (if present)  
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
        }  
  
        factory = _resolve_entry_driver_factory()  
        driver = _make_driver(factory, cfg)  
  
        driver.get("https://example.com")  
  
        ok1 = element_exists(driver, "css", "h1")  
        ok2 = text_contains(driver, "css", "h1", "Example")  
  
        # Guarded step that should intentionally skip  
        step = {  
            "action": "click",  
            "by": "css",  
            "value": ".confirm",  
            "if_text_contains": {"selector": "h1", "text": "DOES_NOT_MATCH", "by": "css"},  
        }  
        should_run = should_run_step(driver, step)  
        ok3 = (should_run is False)  
  
        print("\n=== dev_smoke_act_1c ===")  
        print(f"element_exists(h1): {ok1}")  
        print(f"text_contains(h1,'Example'): {ok2}")  
        print(f"guarded step should_run_step == False: {ok3}")  
  
        if ok1 and ok2 and ok3:  
            print("PASS: dev_smoke_act_1c")  
            return 0  
  
        print("FAIL: dev_smoke_act_1c")  
        return 1  
  
    except Exception as e:  
        print("\nFAIL: dev_smoke_act_1c (exception)")  
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