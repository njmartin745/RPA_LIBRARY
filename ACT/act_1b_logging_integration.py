"""  
ACT-1B — Structured logging integration wrapper for ACT-1A  
  
Purpose  
-------  
Orchestrate execution of ACT-1A steps while automatically emitting structured logs  
(using LOG-1A) for:  
- step_start  
- step_success  
- step_error  
  
This module does NOT change ACT-1A behavior; it wraps ACT-1A execution to add  
consistent logging and cfg-driven stop/continue behavior.  
  
Key behaviors  
-------------  
- Uses cfg["STOP_ON_ERROR"] (default True) to determine fail-fast behavior.  
- Preserves ACT-1A per-step `continue_on_error` behavior.  
- Binds per-item context (run_id/current_id/item_index/total_items) if present in cfg.  
- Uses LOG-1A `log_exception` for exceptions, capturing step_id + milestone + taxonomy tag.  
"""  
  
from __future__ import annotations  
  
from typing import Any, MutableMapping, Optional  
  
from ACT.act_1a_action_engine import ActionEngineError, StepOutcome, run_actions  
from LOG.log_1a_structured_logging import bind_context, log_event, log_exception  
  
__all__ = [  
    "run_actions_logged",  
    "dev_smoke",  
]  
  
  
def _truthy(v: Any) -> bool:  
    s = str(v if v is not None else "").strip().lower()  
    return s in {"1", "true", "yes", "on"}  
  
  
def _bind_from_cfg(cfg: MutableMapping[str, Any]) -> None:  
    fields: dict[str, Any] = {}  
    if "RUN_ID" in cfg and cfg.get("RUN_ID"):  
        fields["run_id"] = cfg.get("RUN_ID")  
    if "CURRENT_ID" in cfg:  
        fields["current_id"] = cfg.get("CURRENT_ID")  
    if "ITEM_INDEX" in cfg:  
        fields["item_index"] = cfg.get("ITEM_INDEX")  
    if "TOTAL_ITEMS" in cfg:  
        fields["total_items"] = cfg.get("TOTAL_ITEMS")  
  
    if fields:  
        bind_context(cfg, **fields)  
    else:  
        # Still ensure RUN_ID exists (LOG-1A bind_context does that)  
        bind_context(cfg)  
  
  
def _step_meta(step: dict[str, Any], idx: int) -> dict[str, Any]:  
    step_id = step.get("step_id", None)  
    if step_id is None:  
        step_id = step.get("id", None)  
    action = step.get("action", None)  
    name = step.get("name", None)  
    return {  
        "step_index": idx,  
        "step_id": step_id,  
        "action": action,  
        "step_name": name,  
    }  
  
  
def _taxonomy_tag(step: dict[str, Any]) -> Optional[str]:  
    # Best-effort: do not invent schema; accept common keys if present  
    for k in ("tag", "error_tag", "taxonomy_tag", "tax_tag"):  
        v = step.get(k)  
        if v is not None and str(v).strip():  
            return str(v).strip()  
    return None  
  
  
def _reindex_outcome(outcome: StepOutcome, idx: int) -> StepOutcome:  
    # ACT-1A returns index=0 when executing a single-step list; adjust to global index.  
    try:  
        outcome.index = idx  # dataclass is mutable in ACT-1A  
    except Exception:  
        pass  
    return outcome  
  
  
def run_actions_logged(  
    driver,  
    steps: list[dict[str, Any]],  
    cfg: MutableMapping[str, Any],  
    *,  
    logger,  
) -> list[StepOutcome]:  
    """  
    Execute steps through ACT-1A while emitting LOG-1A structured events.  
  
    Parameters  
    ----------  
    driver : Selenium WebDriver  
    steps  : list[dict]  
    cfg    : mutable mapping  
    logger : logging.Logger (should be configured via LOG-1A setup_logging)  
  
    Returns  
    -------  
    list[StepOutcome]  
  
    Raises  
    ------  
    ActionEngineError (from ACT-1A) when STOP_ON_ERROR is truthy and an unhandled step fails.  
    """  
    stop_on_error = _truthy(cfg.get("STOP_ON_ERROR", True))  
    outcomes: list[StepOutcome] = []  
    any_failed = False  
  
    for idx, step in enumerate(steps):  
        _bind_from_cfg(cfg)  
        meta = _step_meta(step, idx)  
  
        log_event(logger, "step_start", **meta)  
  
        try:  
            # Execute one step at a time so we can emit step_start/step_success/step_error deterministically.  
            step_outcomes = run_actions(driver, [step], cfg, fail_fast=stop_on_error)  
            if step_outcomes:  
                o = _reindex_outcome(step_outcomes[0], idx)  
                outcomes.append(o)  
  
                if o.ok:  
                    log_event(  
                        logger,  
                        "step_success",  
                        **meta,  
                        duration_s=o.duration_s,  
                    )  
                else:  
                    any_failed = True  
                    # This happens when ACT-1A did not raise (e.g., per-step continue_on_error)  
                    log_event(  
                        logger,  
                        "step_error",  
                        **meta,  
                        duration_s=o.duration_s,  
                        error_type=o.error_type,  
                        error_message=o.error_message,  
                    )  
            else:  
                any_failed = True  
                # Should not occur; treat as error-like.  
                log_event(  
                    logger,  
                    "step_error",  
                    **meta,  
                    error_type="EmptyOutcome",  
                    error_message="No outcome returned",  
                )  
  
        except ActionEngineError as ae:  
            # ACT-1A fail-fast path: outcomes up to the failing step are attached  
            if getattr(ae, "outcomes", None):  
                for o in ae.outcomes:  
                    # If ACT-1A ever returns multi-step outcomes here, preserve relative indexing.  
                    global_idx = idx if len(ae.outcomes) == 1 else (idx + int(getattr(o, "index", 0) or 0))  
                    failing = _reindex_outcome(o, global_idx)  
                    outcomes.append(failing)  
                    if not failing.ok:  
                        any_failed = True  
            else:  
                any_failed = True  
  
            cause = ae.__cause__ if ae.__cause__ is not None else ae  
  
            # Ensure PIPE-1E's event parser always sees a canonical step_error event  
            log_event(  
                logger,  
                "step_error",  
                **meta,  
                error_type=type(cause).__name__,  
                error_message=str(cause),  
            )  
  
            log_exception(  
                logger,  
                cause,  
                event="step_error",  
                step_id=meta.get("step_id"),  
                milestone="ACT-1A",  
                tag=_taxonomy_tag(step),  
                step_index=idx,  
                action=meta.get("action"),  
            )   
  
            if stop_on_error:  
                raise  
            # else continue  
  
    # Explicit aggregate marker for higher layers when STOP_ON_ERROR is false.  
    cfg["ACT_LOGGED_ALL_OK"] = (not any_failed)  
    return outcomes  
  
  
def dev_smoke() -> None:  
    assert _truthy(True) is True  
    assert _truthy("true") is True  
    assert _truthy("1") is True  
    assert _truthy("yes") is True  
    assert _truthy("false") is False  
    assert _truthy("") is False  
  
    assert _taxonomy_tag({"tag": "X"}) == "X"  
    assert _taxonomy_tag({"taxonomy_tag": "Y"}) == "Y"  
    assert _taxonomy_tag({}) is None  