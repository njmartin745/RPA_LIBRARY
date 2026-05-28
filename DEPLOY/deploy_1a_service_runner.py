"""  
DEPLOY-1A — Runtime Service + Packaging (service runner)  
  
No Selenium logic. Orchestration + lifecycle only.  
Reuses AGENT-2A as the execution engine.  
  
Public API:  
- run_service(workflows, interval_seconds=300, cfg=None) -> None  
- run_single_job(workflow, cfg=None) -> dict  
  
Notes:  
- run_service loops until stopped (KeyboardInterrupt) or until cfg["max_cycles"] (if provided) is reached.  
- Exceptions are caught and logged; service continues.  
"""  
  
from __future__ import annotations  
  
import copy  
import time  
from typing import Any, Dict, List, Optional  
  
from AGENT.agent_2a_autonomous_loop import run_autonomous  
  
__all__ = ["run_service", "run_single_job"]  
  
  
def _safe_sleep(seconds: int) -> None:  
    if seconds <= 0:  
        seconds = 1  
    time.sleep(seconds)  
  
  
def run_single_job(workflow: str, *, cfg: dict | None = None) -> dict:  
    cfg2: Dict[str, Any] = copy.deepcopy(cfg or {})  
    try:  
        # Reuse AGENT-2A (no execution logic here).  
        return run_autonomous(workflow, cfg=cfg2)  
    except TypeError:  
        # Backward compatibility if signature differs.  
        return run_autonomous(workflow)  
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
  
  
def run_service(  
    *,  
    workflows: List[str],  
    interval_seconds: int = 300,  
    cfg: dict | None = None,  
) -> None:  
    cfg2: Dict[str, Any] = copy.deepcopy(cfg or {})  
    max_cycles = cfg2.get("max_cycles", None)  
    if max_cycles is not None:  
        try:  
            max_cycles = int(max_cycles)  
        except Exception:  
            max_cycles = None  
  
    print(  
        "[DEPLOY-1A] service start: "  
        f"workflows={len(workflows)} interval_seconds={interval_seconds} max_cycles={max_cycles}"  
    )  
  
    cycle = 0  
    try:  
        while True:  
            if max_cycles is not None and cycle >= max_cycles:  
                print(f"[DEPLOY-1A] max_cycles reached ({max_cycles}); stopping service")  
                return  
  
            cycle += 1  
            print(f"[DEPLOY-1A] cycle={cycle} begin")  
  
            for wf in workflows:  
                print(f"[DEPLOY-1A] cycle={cycle} run workflow={wf}")  
                try:  
                    out = run_single_job(wf, cfg=cfg2)  
                    ok = bool(isinstance(out, dict) and out.get("success") is True)  
                    print(f"[DEPLOY-1A] cycle={cycle} workflow={wf} ok={ok}")  
                except Exception as e:  
                    # Should not crash the service  
                    print(f"[DEPLOY-1A] cycle={cycle} workflow={wf} ERROR: {type(e).__name__}: {e}")  
                    continue  
  
            print(f"[DEPLOY-1A] cycle={cycle} complete; sleeping interval_seconds={interval_seconds}")  
            _safe_sleep(interval_seconds)  
  
    except KeyboardInterrupt:  
        print("[DEPLOY-1A] received KeyboardInterrupt; shutting down gracefully")  
        return  