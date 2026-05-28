
# Auto-generated smoke stub by BUILD-1C  
# Workflow name: login_to_a_site_and_download_a_report  
# Workflow path (relative to this stub): ..\WORKFLOWS\login_to_a_site_and_download_a_report.json  
  
from __future__ import annotations  
  
import json  
import os  
import sys  
from pathlib import Path  
  
  
def _find_project_root(start: Path) -> Path:  
    start = start.resolve()  
    for p in [start, *start.parents]:  
        if (p / "RUN").is_dir() and (p / "CLI").is_dir():  
            return p  
    # fallback: repo root is one level up from dev/ in typical layout  
    return start.parents[1] if len(start.parents) > 1 else start  
  
  
def _import_run_workflow():  
    # Try a few likely module paths (kept defensive to avoid coupling).  
    candidates = [  
        ("RUN.run_1a_runner", "run_workflow"),  
        ("RUN.run_1a", "run_workflow"),  
        ("RUN.run_1a_workflow_runner", "run_workflow"),  
    ]  
    last_err = None  
    for mod, sym in candidates:  
        try:  
            m = __import__(mod, fromlist=[sym])  
            fn = getattr(m, sym)  
            return fn  
        except Exception as e:  # noqa: BLE001  
            last_err = e  
    raise ImportError(f"Could not import RUN-1A run_workflow() from expected modules. Last error: {last_err}")  
  
  
def _call_run_workflow(run_workflow, workflow_obj: dict, workflow_path: Path, cfg: dict):  
    # Try common calling conventions without requiring signature knowledge.  
    tried = []  
    for kwargs in (  
        {"workflow": workflow_obj, "cfg": cfg},  
        {"workflow": workflow_obj, "config": cfg},  
        {"workflow_obj": workflow_obj, "cfg": cfg},  
        {"workflow_path": str(workflow_path), "cfg": cfg},  
        {"workflow_path": str(workflow_path), "config": cfg},  
    ):  
        try:  
            return run_workflow(**kwargs)  
        except TypeError as e:  
            tried.append(str(e))  
    # Try positional fallbacks  
    try:  
        return run_workflow(workflow_obj, cfg)  
    except TypeError as e:  
        tried.append(str(e))  
    try:  
        return run_workflow(str(workflow_path), cfg)  
    except TypeError as e:  
        tried.append(str(e))  
  
    raise TypeError("Unable to call run_workflow() with known conventions. Errors: " + " | ".join(tried))  
  
  
def main() -> int:  
    here = Path(__file__).resolve()  
    project_root = _find_project_root(here)  
    if str(project_root) not in sys.path:  
        sys.path.insert(0, str(project_root))  
  
    workflow_path = (here.parent / r"""..\WORKFLOWS\login_to_a_site_and_download_a_report.json""").resolve()  
  
    if not workflow_path.exists():  
        print("FAIL: smoke stub cannot find workflow file:", workflow_path)  
        return 2  
  
    workflow_obj = json.loads(workflow_path.read_text(encoding="utf-8"))  
  
    # Minimal config template (edit as needed).  
    # DRY_RUN=0 can be used to force real execution if your RUN-1A supports it.  
    cfg = {  
        "dry_run": (os.environ.get("DRY_RUN", "1") != "0"),  
        "headless": True,  
        "downloads_dir": "downloads",  
        "artifacts_dir": "artifacts",  
        "reports_dir": "reports",  
    }  
  
    try:  
        run_workflow = _import_run_workflow()  
        result = _call_run_workflow(run_workflow, workflow_obj, workflow_path, cfg)  
    except Exception as e:  # noqa: BLE001  
        print("FAIL: RUN-1A execution raised exception")  
        print(repr(e))  
        return 1  
  
    ok = True  
    if isinstance(result, dict) and "ok" in result:  
        ok = bool(result.get("ok"))  
  
    if ok:  
        print("PASS: SMOKE", "login_to_a_site_and_download_a_report")  
        if isinstance(result, dict):  
            print("summary:", result.get("summary", result))  
        return 0  
  
    print("FAIL: SMOKE", "login_to_a_site_and_download_a_report")  
    if isinstance(result, dict):  
        print("result:", result)  
    return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  
