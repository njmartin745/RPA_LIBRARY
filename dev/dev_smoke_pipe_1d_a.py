"""  
Dev smoke test — PIPE-1D (step execution adapter)  
  
Flow  
----  
1) Use ENTRY-1A to create driver  
2) Load steps from PIPE-1C  
3) Execute steps through PIPE-1D  
4) Run: get example.com -> wait_for_element h1 -> js return document.title  
5) Print results for each step  
6) Exit 0 if all steps succeed  
"""  
  
from __future__ import annotations  
  
import importlib  
import json  
import pkgutil  
import tempfile  
import traceback  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from typing import Any, Callable, Dict, Optional  
  
from PIPE.pipe_1c_steps_loader import load_steps_from_cfg  
from PIPE.pipe_1d_step_executor import execute_step  
  
  
def _write_steps_file(path: Path) -> None:  
    payload = {  
        "steps": [  
            {"action": "get", "url": "${BASE_URL}"},  
            {"action": "wait_for_element", "by": "css", "value": "h1"},  
            {  
                "action": "js",  
                "script": "return { ok: true, value: document.title };",  
                "save_as": "page_title",  
            },  
        ]  
    }  
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")  
  
def _resolve_entry_driver_factory() -> Callable[..., Any]:  
    """  
    Resolve ENTRY-1A driver factory in a robust way.  
  
    The framework may expose the driver factory under different module/function names.  
    We:  
      1) Try common top-level exports on the ENTRY package.  
      2) Scan ENTRY.* submodules and look for common factory function names.  
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
        "new_driver",  
        "start_driver",  
    )  
  
    # 1) ENTRY package-level exports  
    try:  
        entry_pkg = importlib.import_module("ENTRY")  
        for name in fn_names:  
            fn = getattr(entry_pkg, name, None)  
            if callable(fn):  
                return fn  
    except Exception:  
        # We'll fall back to scanning modules below.  
        entry_pkg = None  # type: ignore[assignment]  
  
    # 2) Scan ENTRY.* modules  
    try:  
        if entry_pkg is None:  
            entry_pkg = importlib.import_module("ENTRY")  
  
        if not hasattr(entry_pkg, "__path__"):  
            raise RuntimeError("ENTRY is not a package (missing __path__).")  
  
        for modinfo in pkgutil.iter_modules(entry_pkg.__path__, prefix=entry_pkg.__name__ + "."):  
            try:  
                mod = importlib.import_module(modinfo.name)  
            except Exception:  
                continue  
  
            for name in fn_names:  
                fn = getattr(mod, name, None)  
                if callable(fn):  
                    return fn  
    except Exception as e:  
        raise RuntimeError(f"Failed while scanning ENTRY package for a driver factory: {type(e).__name__}: {e}") from e  
  
    tried = ", ".join(fn_names)  
    raise RuntimeError(  
        "Could not resolve ENTRY-1A driver factory. "  
        f"Searched ENTRY package and ENTRY.* modules for any of: {tried}"  
    )  
  
  
def _make_driver(factory: Callable[..., Any], cfg: Dict[str, Any]) -> Any:  
    """  
    Call the resolved factory with best-effort signature handling.  
    """  
    # Prefer (cfg)  
    try:  
        return factory(cfg)  
    except TypeError:  
        pass  
  
    # Try no-arg  
    try:  
        return factory()  
    except TypeError:  
        pass  
  
    # Try kwargs common variants  
    try:  
        return factory(cfg=cfg)  
    except TypeError as e:  
        raise RuntimeError(  
            f"Resolved driver factory '{getattr(factory, '__name__', repr(factory))}' "  
            "but could not call it with (cfg), (), or (cfg=cfg)."  
        ) from e  
  
  
def main() -> int:  
    driver: Optional[Any] = None  
    try:  
        with tempfile.TemporaryDirectory(prefix="dev_smoke_pipe_1d_") as td:  
            steps_path = Path(td) / "steps.json"  
            _write_steps_file(steps_path)  
  
            cfg: Dict[str, Any] = {  
                "STEPS_PATH": str(steps_path),  
                "BASE_URL": "https://example.com",  
                # Common config keys (provide upper+lower to match typical variations)  
                "HEADLESS": True,  
                "headless": True,  
                "BROWSER": "chrome",  
                "browser": "chrome",  
                "IMPLICIT_WAIT_SEC": 2,  
                "PAGELOAD_TIMEOUT_SEC": 30,  
                "SCRIPT_TIMEOUT_SEC": 30,  
            }  
  
            steps = load_steps_from_cfg(cfg)  
  
            factory = _resolve_entry_driver_factory()  
            driver = _make_driver(factory, cfg)  
  
            all_ok = True  
            for i, step in enumerate(steps):  
                res = execute_step(driver, step, cfg)  
                print(  
                    f"[dev_smoke_pipe_1d] step[{i}] action={step.get('action')!r} -> "  
                    f"{json.dumps(res, default=str)}"  
                )  
                if not res.get("ok", False):  
                    all_ok = False  
  
            return 0 if all_ok else 1  
  
    except Exception as e:  
        print("\n[dev_smoke_pipe_1d] FAILED")  
        print(f"[dev_smoke_pipe_1d] Error: {type(e).__name__}: {e}")  
        print("[dev_smoke_pipe_1d] Traceback:")  
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