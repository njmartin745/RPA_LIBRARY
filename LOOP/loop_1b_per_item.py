# LOOP/loop_1b_per_item.py  
"""  
LOOP-1B — Per-item loop (generic iterator over worklist)  
  
Purpose  
-------  
Provide a reusable, workflow-agnostic per-item execution loop that:  
- iterates a worklist of item IDs  
- injects per-item context into a shared cfg mapping (e.g., CURRENT_ID)  
- calls a caller-supplied `process_item` function for each item  
- supports either fail-fast (stop_on_error=True) or best-effort continuation  
  
This module is intentionally limited to loop orchestration (LOOP milestone).  
It does NOT:  
- read inputs from Excel/CSV/API (INPUT milestone)  
- select retry/baseline manifests or write audit JSONL (STATE milestone)  
- implement Selenium actions/steps execution (ACT/NAV milestones)  
  
Inputs  
------  
- work_items: iterable[str] of work item identifiers  
- cfg: mutable mapping used as shared run context (e.g., env-derived config)  
- process_item: callable invoked per item:  
    process_item(item_id: str, cfg: MutableMapping[str, Any]) -> Any  
- id_var: cfg key to store current item ID (default: "CURRENT_ID")  
- index_var: cfg key to store 1-based index (default: "ITEM_INDEX")  
- total_var: cfg key to store total items count (default: "TOTAL_ITEMS")  
- stop_on_error: if True, re-raise first exception; else continue and collect errors  
- on_* callbacks (optional): hooks for start/success/error events  
  
Outputs  
-------  
- list[ItemOutcome]: ordered results for each attempted item (including errors if not fail-fast)  
- cfg is mutated in-place with per-item variables during execution  
  
When to use  
-----------  
- Your automation runs the same workflow for a list of IDs (per-location/per-account/etc.).  
- You want a consistent way to inject CURRENT_ID and loop metadata into cfg.  
  
When NOT to use  
---------------  
- Single-run workflows with no worklist (use LOOP-1A).  
- Highly parallel processing (this loop is sequential).  
- You need retry-manifest selection/auditing (use STATE-1B alongside this).  
  
Headless notes  
--------------  
- Headless-agnostic; no browser operations.  
  
Dependencies  
------------  
- Standard library only: dataclasses, typing  
  
Common failure modes + mitigations  
----------------------------------  
- process_item raises -> fail-fast by default; set stop_on_error=False to continue.  
- cfg missing expected keys -> caller should initialize cfg; this module only injects loop vars.  
- work_items is a generator and you need total count -> this module materializes to list once.  
  
Security rule  
-------------  
- Never log secrets. This module does not handle credentials.  
  
Minimal usage example  
---------------------  
from LOOP.loop_1b_per_item import run_per_item_loop  
  
def process_one(item_id: str, cfg: dict) -> None:  
    # e.g., call your step runner here  
    cfg["CURRENT_ID"] = item_id  
    # run_steps(driver, steps, cfg)  
  
cfg = {}  
outcomes = run_per_item_loop(["A1", "A2"], cfg, process_one, stop_on_error=True)  
  
Testing Handoff Checklist  
-------------------------  
- [ ] Unit: injects id_var/index_var/total_var into cfg with correct values.  
- [ ] Unit: preserves and restores prior cfg values for injected keys after each item.  
- [ ] Unit: stop_on_error=True re-raises exception and stops further processing.  
- [ ] Unit: stop_on_error=False continues, returns outcomes with captured exceptions.  
- [ ] Unit: callbacks on_item_start/on_item_success/on_item_error invoked as expected.  
- [ ] Integration: works with a Selenium step-runner that reads cfg["CURRENT_ID"].  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Any, Callable, Iterable, MutableMapping, Optional  
  
__all__ = [  
    "ItemOutcome",  
    "run_per_item_loop",
    "iterate_items"  
]  
  
  
@dataclass(frozen=True)  
class ItemOutcome:  
    """Result container for one work item execution."""  
    item_id: str  
    index: int          # 1-based  
    total: int  
    ok: bool  
    result: Any = None  
    error: Optional[BaseException] = None  
  
  
ProcessItemFn = Callable[[str, MutableMapping[str, Any]], Any]  
HookFn = Callable[[str, int, int, MutableMapping[str, Any]], None]  
  
  
def run_per_item_loop(  
    work_items: Iterable[str],  
    cfg: MutableMapping[str, Any],  
    process_item: ProcessItemFn,  
    *,  
    id_var: str = "CURRENT_ID",  
    index_var: str = "ITEM_INDEX",  
    total_var: str = "TOTAL_ITEMS",  
    stop_on_error: bool = True,  
    on_item_start: Optional[HookFn] = None,  
    on_item_success: Optional[HookFn] = None,  
    on_item_error: Optional[HookFn] = None,  
) -> list[ItemOutcome]:  
    """  
    Iterate over work_items and execute process_item per ID.  
  
    Notes  
    -----  
    This function temporarily injects loop variables into cfg for each item and  
    restores previous values afterward (so callers can safely reuse cfg).  
    """  
    items = [str(x).strip() for x in work_items if str(x).strip()]  
    total = len(items)  
  
    outcomes: list[ItemOutcome] = []  
  
    # Remember prior values to restore after each iteration  
    had_id = id_var in cfg  
    had_index = index_var in cfg  
    had_total = total_var in cfg  
    prev_id = cfg.get(id_var)  
    prev_index = cfg.get(index_var)  
    prev_total = cfg.get(total_var)  
  
    try:  
        for i, item_id in enumerate(items, start=1):  
            cfg[id_var] = item_id  
            cfg[index_var] = i  
            cfg[total_var] = total  
  
            if on_item_start:  
                on_item_start(item_id, i, total, cfg)  
  
            try:  
                result = process_item(item_id, cfg)  
                outcome = ItemOutcome(  
                    item_id=item_id,  
                    index=i,  
                    total=total,  
                    ok=True,  
                    result=result,  
                    error=None,  
                )  
                outcomes.append(outcome)  
                if on_item_success:  
                    on_item_success(item_id, i, total, cfg)  
            except BaseException as e:  
                outcome = ItemOutcome(  
                    item_id=item_id,  
                    index=i,  
                    total=total,  
                    ok=False,  
                    result=None,  
                    error=e,  
                )  
                outcomes.append(outcome)  
                if on_item_error:  
                    on_item_error(item_id, i, total, cfg)  
                if stop_on_error:  
                    raise  
                # else continue  
    finally:  
        # Restore previous cfg state  
        if had_id:  
            cfg[id_var] = prev_id  
        else:  
            cfg.pop(id_var, None)  
  
        if had_index:  
            cfg[index_var] = prev_index  
        else:  
            cfg.pop(index_var, None)  
  
        if had_total:  
            cfg[total_var] = prev_total  
        else:  
            cfg.pop(total_var, None)  
  
    return outcomes  

def iterate_items(cfg, ids):
    """
    PIPE-facing iterator expected by PIPE-1A.
    Simple wrapper around the internal LOOP implementation.
    """
    for item in ids:
        yield item