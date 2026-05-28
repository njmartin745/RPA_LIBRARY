"""  
How to run:  
  python dev/dev_smoke_auth_1b.py  
"""  
  
from __future__ import annotations  
  
import importlib  
import pkgutil  
import tempfile  
import traceback  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from typing import Any, Callable, Dict, Optional  
  
from AUTH.auth_1b_session_restore import load_cookies, save_cookies  
  
  
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
  
  
def _has_cookie_named(driver: Any, name: str) -> bool:  
    try:  
        for c in (driver.get_cookies() or []):  
            if isinstance(c, dict) and c.get("name") == name:  
                return True  
    except Exception:  
        return False  
    return False  
  
  
def main() -> int:  
    d1: Optional[Any] = None  
    d2: Optional[Any] = None  
    try:  
        cfg: Dict[str, Any] = {"HEADLESS": True, "BROWSER": "edge"}  
        factory = _resolve_entry_driver_factory()  
  
        with tempfile.TemporaryDirectory(prefix="dev_smoke_auth_1b_") as td:  
            cookie_path = Path(td) / "cookies.json"  
            domain_url = "https://example.com"  
  
            # Session 1: create cookie and save  
            d1 = _make_driver(factory, cfg)  
            d1.get(domain_url)  
            try:  
                d1.add_cookie({"name": "smoke_auth_1b", "value": "1", "path": "/"})  
            except Exception:  
                # Some drivers may require a refresh or may block certain cookies; keep test resilient.  
                pass  
            d1.get(domain_url)  
  
            save_cookies(d1, cookie_path)  
  
            # Session 2: load cookies and verify cookie name exists  
            d2 = _make_driver(factory, cfg)  
            applied = load_cookies(d2, cookie_path, domain_url=domain_url)  
            present = _has_cookie_named(d2, "smoke_auth_1b")  
  
            ok = bool(applied) and bool(present)  
  
            print("\n=== dev_smoke_auth_1b ===")  
            print(f"cookie_path: {cookie_path}")  
            print(f"applied_any: {applied}")  
            print(f"cookie_present_by_name: {present}")  
  
            if ok:  
                print("PASS: dev_smoke_auth_1b")  
                return 0  
  
            print("FAIL: dev_smoke_auth_1b")  
            return 1  
  
    except Exception as e:  
        print("\nFAIL: dev_smoke_auth_1b (exception)")  
        print(f"Error: {type(e).__name__}: {e}")  
        traceback.print_exc()  
        return 1  
  
    finally:  
        try:  
            if d1 is not None:  
                d1.quit()  
        except Exception:  
            pass  
        try:  
            if d2 is not None:  
                d2.quit()  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  