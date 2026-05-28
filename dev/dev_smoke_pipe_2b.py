"""  
How to run:  
  python dev/dev_smoke_pipe_2b.py  
"""  
  
from __future__ import annotations  
  
import importlib  
import pkgutil  
import time  
import traceback  
from typing import Any, Callable, Dict, Optional  

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from PIPE.pipe_2b_step_blocks import run_steps  
from VAR.var_1a_runtime_store import set_var  
  
  
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
  
  
def _leaf_executor(driver: Any, step: Dict[str, Any], cfg: Dict[str, Any], step_index: int) -> Dict[str, Any]:  
    """  
    Minimal leaf executor for smoke testing.  
    Intended only to demonstrate PIPE-2B block execution calling a leaf executor via PIPE-2A.  
    """  
    action = step.get("action")  
    try:  
        if action == "get":  
            url = step["url"]  
            driver.get(url)  
            return {"ok": True, "action": action, "url": url}  
  
        if action == "wait_for_element":  
            by = step.get("by", "css")  
            sel = step.get("value")  
            timeout = float(step.get("timeout_sec", 5.0))  
            end = time.time() + timeout  
            while time.time() < end:  
                try:  
                    if by == "css":  
                        els = driver.find_elements("css selector", sel)  
                    elif by == "xpath":  
                        els = driver.find_elements("xpath", sel)  
                    else:  
                        els = driver.find_elements("css selector", sel)  
                    if els:  
                        return {"ok": True, "action": action, "by": by, "value": sel}  
                except Exception:  
                    pass  
                time.sleep(0.1)  
            return {"ok": False, "action": action, "error": f"Timeout waiting for {by}:{sel}"}  
  
        if action == "validate_text":  
            by = step.get("by", "css")  
            sel = step.get("value")  
            expected = step.get("expected", "")  
            if by == "css":  
                el = driver.find_elements("css selector", sel)[0]  
            elif by == "xpath":  
                el = driver.find_elements("xpath", sel)[0]  
            else:  
                el = driver.find_elements("css selector", sel)[0]  
            got = " ".join((el.text or "").split())  
            exp = " ".join(str(expected).split())  
            ok = got == exp  
            return {"ok": ok, "action": action, "got": got, "expected": exp}  
  
        if action == "js":  
            script = step.get("script", "")  
            out = driver.execute_script(script)  
            # If JS returns a dict with ok field, treat that as the step ok signal.  
            if isinstance(out, dict) and "ok" in out:  
                return {"ok": bool(out.get("ok")), "action": action, "result": out}  
            return {"ok": True, "action": action, "result": out}  
  
        return {"ok": False, "action": action, "error": f"Unknown action: {action!r}"}  
  
    except Exception as e:  
        return {"ok": False, "action": action, "error": f"{type(e).__name__}: {e}"}  
  
  
def main() -> int:  
    driver: Optional[Any] = None  
    try:  
        cfg: Dict[str, Any] = {"HEADLESS": True, "BROWSER": "edge", "STOP_ON_ERROR": False}  
  
        # Vars used in steps via ${...}  
        set_var(cfg, "base_url", "https://example.com")  
        set_var(cfg, "expected_h1", "Example Domain")  
  
        # Inject leaf executor for deterministic smoke behavior.  
        cfg["LEAF_EXECUTOR"] = _leaf_executor  
  
        steps = [  
            {  
                "action": "group",  
                "name": "baseline",  
                "steps": [  
                    {"action": "get", "url": "${base_url}"},  
                    {"action": "wait_for_element", "by": "css", "value": "h1"},  
                ],  
            },  
            {  
                "action": "if",  
                "condition": {"type": "exists", "by": "css", "value": "h1"},  
                "then": [  
                    {"action": "validate_text", "by": "css", "value": "h1", "expected": "${expected_h1}"},  
                ],  
                "else": [  
                    # Should not run on example.com; included to show structure.  
                    {"action": "js", "script": "return {ok:false, reason:'h1 missing'}"},  
                ],  
            },  
            {  
                "action": "try",  
                "steps": [  
                    # Intentional failure  
                    {"action": "validate_text", "by": "css", "value": "h1", "expected": "NOT_THE_TITLE"},  
                ],  
                "catch": [  
                    {"action": "js", "script": "return {ok:true, recovered:true}"},  
                ],  
                "finally": [  
                    {"action": "js", "script": "return {ok:true, finally:true}"},  
                ],  
            },  
        ]  
  
        factory = _resolve_entry_driver_factory()  
        driver = _make_driver(factory, cfg)  
  
        results = run_steps(driver, steps, cfg)  
  
        print("\n=== dev_smoke_pipe_2b ===")  
        overall_ok = True  
        for i, r in enumerate(results):  
            print(f"step[{i}] -> {r}")  
            overall_ok = overall_ok and bool(r.get("ok"))  
  
        if overall_ok:  
            print("PASS: dev_smoke_pipe_2b")  
            return 0  
  
        print("FAIL: dev_smoke_pipe_2b")  
        return 1  
  
    except Exception as e:  
        print("\nFAIL: dev_smoke_pipe_2b (exception)")  
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