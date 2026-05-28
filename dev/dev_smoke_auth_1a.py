"""  
How to run:  
  python dev/dev_smoke_auth_1a.py  
"""  
  
from __future__ import annotations  
  
import importlib  
import pkgutil  
import traceback  
import urllib.parse  
from typing import Any, Callable, Dict, Optional  

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from AUTH.auth_1a_form_login_guarded import ensure_logged_in  
  
  
def _resolve_entry_driver_factory() -> Callable[..., Any]:  
    """  
    ENTRY-1A webdriver bootstrap is present, but we resolve factory via introspection  
    (Auto-1 friendly).  
    """  
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
  
    # Try known module first  
    try:  
        m = importlib.import_module("ENTRY.entry_1a_webdriver_bootstrap")  
        for n in fn_names:  
            fn = getattr(m, n, None)  
            if callable(fn):  
                return fn  
    except Exception:  
        pass  
  
    # Scan ENTRY package  
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
  
  
def _data_url(html: str) -> str:  
    return "data:text/html;charset=utf-8," + urllib.parse.quote(html)  
  
  
def main() -> int:  
    driver: Optional[Any] = None  
    try:  
        html = """  
<!doctype html>  
<html>  
  <head><meta charset="utf-8"><title>AUTH-1A Smoke</title></head>  
  <body>  
    <div id="login">  
      <input id="username" />  
      <input id="password" type="password" />  
      <button id="submit">Login</button>  
    </div>  
    <div id="logged_in" style="display:none">Logged In</div>  
  
    <script>  
      document.getElementById('submit').addEventListener('click', function () {  
        var u = document.getElementById('username').value;  
        var p = document.getElementById('password').value;  
        if (u && p) {  
          document.getElementById('login').style.display = 'none';  
          document.getElementById('logged_in').style.display = 'block';  
        }  
      });  
    </script>  
  </body>  
</html>  
""".strip()  
  
        cfg: Dict[str, Any] = {  
            "HEADLESS": True,  
            "BROWSER": "edge",  
            "EXPLICIT_WAIT": 5,  
  
            "LOGIN_URL": _data_url(html),  
            "USERNAME": "demo_user",  
            "PASSWORD": "demo_pass",  
  
            "USERNAME_SELECTOR": "#username",  
            "PASSWORD_SELECTOR": "#password",  
            "SUBMIT_SELECTOR": "#submit",  
            "LOGGED_IN_SELECTOR": "#logged_in",  
        }  
  
        factory = _resolve_entry_driver_factory()  
        driver = _make_driver(factory, cfg)  
  
        r1 = ensure_logged_in(driver, cfg)  
        r2 = ensure_logged_in(driver, cfg)  # should be guarded/skip  
  
        ok = bool(r1.get("ok")) and bool(r2.get("ok")) and bool(r2.get("already_logged_in"))  
  
        print("\n=== dev_smoke_auth_1a ===")  
        print(f"first_call:  {r1}")  
        print(f"second_call: {r2}")  
  
        if ok:  
            print("PASS: dev_smoke_auth_1a")  
            return 0  
        print("FAIL: dev_smoke_auth_1a")  
        return 1  
  
    except Exception as e:  
        print("\nFAIL: dev_smoke_auth_1a (exception)")  
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