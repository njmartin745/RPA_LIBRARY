"""  
Dev smoke test — PIPE-1C (steps loader + template substitution)  
  
Behavior  
--------  
- Create a temp directory and write a small steps.json file containing:  
    - get to https://example.com (via ${BASE_URL})  
    - wait_for_element on ("css", "h1")  
    - js step returning a dict and using save_as  
- Build cfg:  
    - STEPS_PATH -> temp steps.json  
    - browser/headless/waits set to common defaults  
    - Does NOT require a real Excel; omits WORKLIST_PATH on purpose  
- Call:  
    steps = load_steps_from_cfg(cfg)  
    summary = PIPE.pipe_1a_run_orchestrator.run_worklist(cfg, steps)  
- Print:  
    - resolved steps count  
    - summary JSON  
- Exit 0 if summary["failed"] == 0 else exit 1  
"""  
  
from __future__ import annotations  
  
import json  
import tempfile  
import traceback  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from typing import Any, Dict  
  
from PIPE.pipe_1a_run_orchestrator import run_worklist  
from PIPE.pipe_1c_steps_loader import load_steps_from_cfg  
  
  
def _write_steps_file(path: Path) -> None:  
    steps = [  
        {  
            "action": "get",  
            "url": "${BASE_URL}",  
        },  
        {  
            "action": "wait_for_element",  
            "by": "css",  
            "value": "h1",  
        },  
        {  
            "action": "js",  
            "script": "return {ok: true, title: document.title};",  
            "save_as": "page_info",  
        },  
    ]  
    payload: Dict[str, Any] = {"steps": steps}  
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")  
  
  
def main() -> int:  
    try:  
        with tempfile.TemporaryDirectory(prefix="dev_smoke_pipe_1c_") as td:  
            steps_path = Path(td) / "steps.json"  
            _write_steps_file(steps_path)  
  
            cfg: Dict[str, Any] = {  
                # PIPE-1C  
                "STEPS_PATH": str(steps_path),  
                "BASE_URL": "https://example.com",  
                # Common runtime toggles (framework-specific keys may vary; safe to include)  
                "HEADLESS": True,  
                "BROWSER": "chrome",  
                "IMPLICIT_WAIT_SEC": 2,  
                "PAGELOAD_TIMEOUT_SEC": 30,  
                "SCRIPT_TIMEOUT_SEC": 30,  
                # Worklist sheet+id column are commonly required; omit WORKLIST_PATH per requirements  
                "WORKLIST_SHEET": "Worklist",  
                "WORKLIST_ID_COLUMN": "ID",
            }  
  
            steps = load_steps_from_cfg(cfg)  
            print(f"[dev_smoke_pipe_1c] Resolved steps: {len(steps)}")  
  
            summary = run_worklist(cfg, steps)  
  
            print("[dev_smoke_pipe_1c] Summary:")  
            print(json.dumps(summary, indent=2, default=str))  
  
            failed = summary.get("failed", None) if isinstance(summary, dict) else None  
            if failed == 0:  
                return 0  
            return 1  
  
    except Exception as e:  
        print("\n[dev_smoke_pipe_1c] FAILED")  
        print(f"[dev_smoke_pipe_1c] Error: {type(e).__name__}: {e}")  
        print("[dev_smoke_pipe_1c] Traceback:")  
        traceback.print_exc()  
        print(  
            "\n[dev_smoke_pipe_1c] Diagnostics / Next steps:\n"  
            "- Ensure PIPE.pipe_1a_run_orchestrator.run_worklist(cfg, steps) is available.\n"  
            "- Ensure the ACT/NAV modules recognize step dicts with keys like:\n"  
            "    {'action': 'get', 'url': ...}\n"  
            "    {'action': 'wait_for_element', 'by': 'css', 'value': 'h1'}\n"  
            "    {'action': 'js', 'script': '...', 'save_as': 'page_info'}\n"  
            "- If your framework uses different step keys, adjust the test steps.json accordingly.\n"  
            "- If the pipeline requires an explicit worklist path, set WORKLIST_PATH (or provider aliases) in cfg."  
        )  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  