"""  
How to run:  
  python dev/dev_smoke_pipe_2c.py  
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
      
from LOG.log_1b_error_taxonomy import SELECTOR_NOT_FOUND, TIMEOUT  
from PIPE.pipe_2c_error_plumbing import run_with_error_plumbing  
  
  
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
  
    try:  
        m = importlib.import_module("ENTRY.entry_1a_webdriver_bootstrap")  
        for n in fn_names:  
            fn = getattr(m, n, None)  
            if callable(fn):  
                return fn  
    except Exception:  
        pass  
  
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
  
  
class _Writer:  
    def __init__(self) -> None:  
        self.rows = []  
  
    def append_row(self, row: Dict[str, Any]) -> None:  
        self.rows.append(dict(row))  
  
  
def _leaf_executor(driver: Any, step: Dict[str, Any], cfg: Dict[str, Any], step_index: int) -> Dict[str, Any]:  
    """  
    Minimal deterministic executor:  
    - get  
    - wait_for_element (simple find, no sleep)  
    - validate_text (uses find_element; missing selector raises Selenium NoSuchElementException if available)  
    """  
    action = step.get("action")  
    if action == "get":  
        driver.get(step["url"])  
        return {"ok": True, "action": action}  
  
    if action == "wait_for_element":  
        by = step.get("by", "css")  
        sel = step.get("value")  
        if by == "css":  
            driver.find_element("css selector", sel)  
        elif by == "xpath":  
            driver.find_element("xpath", sel)  
        else:  
            driver.find_element("css selector", sel)  
        return {"ok": True, "action": action}  
  
    if action == "validate_text":  
        by = step.get("by", "css")  
        sel = step.get("value")  
        expected = step.get("expected", "")  
        if by == "css":  
            el = driver.find_element("css selector", sel)  
        elif by == "xpath":  
            el = driver.find_element("xpath", sel)  
        else:  
            el = driver.find_element("css selector", sel)  
        got = " ".join((el.text or "").split())  
        exp = " ".join(str(expected).split())  
        return {"ok": got == exp, "action": action, "got": got, "expected": exp}  
  
    return {"ok": False, "action": action, "error": f"Unknown action: {action!r}"}  
  
  
def main() -> int:  
    d: Optional[Any] = None  
    try:  
        factory = _resolve_entry_driver_factory()  
  
        # Use PIPE-2B runner deterministically (leaf executor injected via cfg)  
        from PIPE.pipe_2b_step_blocks import run_steps as pipe_2b_run_steps  
  
        steps = [  
            {"action": "get", "url": "https://example.com"},  
            {"action": "wait_for_element", "by": "css", "value": "h1"},  
            # intentional failure: missing selector => should classify as SELECTOR_NOT_FOUND when selenium available  
            {"action": "wait_for_element", "by": "css", "value": "#does_not_exist"},  
        ]  
  
        # --- case 1: STOP_ON_ERROR = False (nonfatal) ---  
        cfg1: Dict[str, Any] = {  
            "HEADLESS": True,  
            "BROWSER": "edge",  
            "STOP_ON_ERROR": False,  
            "STOP_ON_ITEM_ERROR": False,  
            "PIPE_RUNNER": pipe_2b_run_steps,  
            "LEAF_EXECUTOR": _leaf_executor,  
        }  
        writer1 = _Writer()  
        d = _make_driver(factory, cfg1)  
  
        summary1 = run_with_error_plumbing(driver=d, cfg=cfg1, steps=steps, work_items=None, writer=writer1)  
        code1 = (summary1.get("last_error") or {}).get("code")  
  
        ok1 = (summary1["ok"] is False) and (summary1["errors_total"] >= 1) and (code1 in {SELECTOR_NOT_FOUND, TIMEOUT})  
        ok1 = ok1 and (len(writer1.rows) >= 1)  
  
        d.quit()  
        d = None  
  
        # --- case 2: STOP_ON_ERROR = True (fatal) ---  
        cfg2 = dict(cfg1)  
        cfg2["STOP_ON_ERROR"] = True  
        writer2 = _Writer()  
        d = _make_driver(factory, cfg2)  
  
        fatal_raised = False  
        try:  
            _ = run_with_error_plumbing(driver=d, cfg=cfg2, steps=steps, work_items=None, writer=writer2)  
        except Exception:  
            fatal_raised = True  
  
        ok2 = fatal_raised is True  
  
        print("\n=== dev_smoke_pipe_2c ===")  
        print(f"summary1: {summary1}")  
        print(f"writer1_rows: {len(writer1.rows)}")  
        print(f"fatal_raised: {fatal_raised}")  
  
        if ok1 and ok2:  
            print("PASS: dev_smoke_pipe_2c")  
            return 0  
        print("FAIL: dev_smoke_pipe_2c")  
        return 1  
  
    except Exception as e:  
        print("\nFAIL: dev_smoke_pipe_2c (exception)")  
        print(f"Error: {type(e).__name__}: {e}")  
        traceback.print_exc()  
        return 1  
  
    finally:  
        try:  
            if d is not None:  
                d.quit()  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  