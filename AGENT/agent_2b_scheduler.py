"""  
AGENT-2B — Continuous / Scheduled Execution (timing + orchestration only)  
  
Reuses AGENT-2A as the execution engine; does not implement execution logic.  
No Selenium.  
  
Public API:  
- run_continuous(...)  
- run_once_with_delay(...)  
"""  
  
from __future__ import annotations  
  
import copy  
import time  
from pathlib import Path  
from typing import Any, Dict, List, Optional  
  
from AGENT.agent_2a_autonomous_loop import run_autonomous  
  
__all__ = [  
    "run_continuous",  
    "run_once_with_delay",  
]  
  
  
def _ensure_path(p: str | Path) -> Path:  
    return p if isinstance(p, Path) else Path(p)  
  
  
def _safe_sleep(seconds: int) -> None:  
    # Avoid busy loops; enforce non-negative and at least 1s for continuous mode.  
    if seconds <= 0:  
        seconds = 1  
    time.sleep(seconds)  
  
  
def run_once_with_delay(  
    workflow_path: str | Path,  
    *,  
    delay_seconds: int,  
    cfg: Dict[str, Any] | None = None,  
) -> Dict[str, Any]:  
    wf_path = _ensure_path(workflow_path)  
    cfg2 = copy.deepcopy(cfg or {})  
  
    print(f"[AGENT-2B] run_once_with_delay: sleeping delay_seconds={delay_seconds}")  
    if delay_seconds > 0:  
        time.sleep(delay_seconds)  
  
    try:  
        out = run_autonomous(str(wf_path), cfg=cfg2)  
        return out  
    except Exception as e:  
        return {  
            "success": False,  
            "attempts": 0,  
            "run_ids": [],  
            "final_report": None,  
            "patches_applied": [],  
            "recommendations": [],  
            "error": f"{type(e).__name__}: {e}",  
        }  
  
  
def run_continuous(  
    workflow_path: str | Path,  
    *,  
    interval_seconds: int = 300,  
    max_cycles: int | None = None,  
    cfg: Dict[str, Any] | None = None,  
) -> Dict[str, Any]:  
    wf_path = _ensure_path(workflow_path)  
    cfg2 = copy.deepcopy(cfg or {})  
  
    runs: List[Dict[str, Any]] = []  
    success_count = 0  
    failure_count = 0  
    cycles = 0  
  
    print(  
        "[AGENT-2B] run_continuous شروع: "  
        f"workflow={wf_path} interval_seconds={interval_seconds} max_cycles={max_cycles}"  
    )  
  
    try:  
        while True:  
            if max_cycles is not None and cycles >= max_cycles:  
                break  
  
            cycle_no = cycles + 1  
            print(f"[AGENT-2B] cycle={cycle_no} starting")  
  
            try:  
                out = run_autonomous(str(wf_path), cfg=cfg2)  
                run_entry = {"cycle": cycle_no, "result": out}  
                runs.append(run_entry)  
                if out.get("success") is True:  
                    success_count += 1  
                else:  
                    failure_count += 1  
            except Exception as e:  
                # Must handle exceptions and continue loop  
                failure_count += 1  
                runs.append(  
                    {  
                        "cycle": cycle_no,  
                        "result": {  
                            "success": False,  
                            "attempts": 0,  
                            "run_ids": [],  
                            "final_report": None,  
                            "patches_applied": [],  
                            "recommendations": [],  
                            "error": f"{type(e).__name__}: {e}",  
                        },  
                    }  
                )  
  
            cycles += 1  
            print(f"[AGENT-2B] cycle={cycle_no} complete (cycles={cycles})")  
  
            if max_cycles is not None and cycles >= max_cycles:  
                break  
  
            print(f"[AGENT-2B] sleeping interval_seconds={interval_seconds}")  
            _safe_sleep(interval_seconds)  
  
    except KeyboardInterrupt:  
        print("[AGENT-2B] interrupted by user; stopping scheduler loop")  
  
    return {  
        "cycles": cycles,  
        "runs": runs,  
        "success_count": success_count,  
        "failure_count": failure_count,  
    }  