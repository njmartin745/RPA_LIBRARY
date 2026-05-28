from __future__ import annotations  
  
import importlib  
import inspect  
from typing import Any, Callable, Dict, Mapping, Optional, Tuple  
  
from WORKFLOWS.workflow_1g_deploy_bundle_loader import (  
    extract_runnable_from_deploy_bundle_1a,  
    load_deploy_bundle_1a,  
)  
  
__all__ = [  
    "resolve_default_workflow_runner_callable",  
    "run_deploy_bundle_1a",  
    "run_deploy_bundle_1a_with_meta",  
    "dev_smoke",  
]  
  
  
def resolve_default_workflow_runner_callable() -> Callable[..., Any]:  
    """  
    Resolve the framework's workflow runner callable.  
  
    Deterministic resolution order; raises if none found.  
    """  
    candidates: Tuple[Tuple[str, Tuple[str, ...]], ...] = (  
        ("RUN.run_1a_workflow_runner", ("run_workflow", "run", "main")),  
        ("RUN.run_1b_workflow_runner", ("run_workflow", "run", "main")),  
        ("RUN.run_1c_workflow_runner", ("run_workflow", "run", "main")),  
        ("RUN.run_1d_workflow_runner", ("run_workflow", "run", "main")),  
    )  
  
    for mod_name, fn_names in candidates:  
        try:  
            mod = importlib.import_module(mod_name)  
        except Exception:  
            continue  
  
        for fn in fn_names:  
            c = getattr(mod, fn, None)  
            if callable(c):  
                return c  
  
    raise RuntimeError(  
        "Could not resolve a workflow runner callable. "  
        "Tried RUN.run_1a/1b/1c/1d_workflow_runner: run_workflow/run/main."  
    )  
  
  
def _filter_kwargs_for_callable(fn: Callable[..., Any], kwargs: Mapping[str, Any]) -> Dict[str, Any]:  
    sig = inspect.signature(fn)  
    params = sig.parameters  
    out: Dict[str, Any] = {}  
    for k, v in kwargs.items():  
        if k in params:  
            out[k] = v  
    return out  
  
  
def _call_runner_deterministically(  
    runner: Callable[..., Any],  
    *,  
    workflow: Dict[str, Any],  
    selector_pack: Dict[str, Any],  
    run_meta: Dict[str, Any],  
    runner_kwargs: Optional[Mapping[str, Any]] = None,  
) -> Any:  
    """  
    Call a runner with a deterministic adaptation strategy:  
      1) keyword call using recognized parameter names + filtered runner_kwargs  
      2) positional fallback: (workflow, selector_pack, run_meta)  
      3) positional fallback: (workflow, selector_pack)  
      4) positional fallback: (workflow)  
    """  
    if runner_kwargs is None:  
        runner_kwargs = {}  
  
    recognized: Dict[str, Any] = {  
        # workflow  
        "workflow": workflow,  
        "workflow_dict": workflow,  
        # selector pack (or selectors only)  
        "selector_pack": selector_pack,  
        "selector_pack_dict": selector_pack,  
        "selectors": selector_pack.get("selectors") if isinstance(selector_pack.get("selectors"), Mapping) else None,  
        # meta  
        "run_meta": run_meta,  
        "meta": run_meta,  
    }  
  
    # 1) kwargs-first  
    kw = {}  
    kw.update(_filter_kwargs_for_callable(runner, recognized))  
    kw.update(_filter_kwargs_for_callable(runner, runner_kwargs))  
    try:  
        return runner(**kw)  
    except TypeError:  
        # 2..4 positional fallbacks (stable order)  
        try:  
            return runner(workflow, selector_pack, run_meta)  
        except TypeError:  
            try:  
                return runner(workflow, selector_pack)  
            except TypeError:  
                return runner(workflow)  
  
  
def run_deploy_bundle_1a(  
    deploy_bundle: Mapping[str, Any],  
    *,  
    runner: Optional[Callable[..., Any]] = None,  
    validate: bool = True,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
    runner_kwargs: Optional[Mapping[str, Any]] = None,  
) -> Any:  
    """  
    Run a DEPLOY_BUNDLE_1A directly (no manual extraction required).  
  
    - Loads + (optional) validates the bundle  
    - Extracts workflow + selector_pack  
    - Delegates to the resolved runner (or provided runner)  
    """  
    loaded = load_deploy_bundle_1a(  
        deploy_bundle,  
        validate=validate,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
    )  
    workflow, selector_pack, run_meta = extract_runnable_from_deploy_bundle_1a(loaded)  
  
    r = runner if runner is not None else resolve_default_workflow_runner_callable()  
    return _call_runner_deterministically(  
        r,  
        workflow=workflow,  
        selector_pack=selector_pack,  
        run_meta=run_meta,  
        runner_kwargs=runner_kwargs,  
    )  
  
  
def run_deploy_bundle_1a_with_meta(  
    deploy_bundle: Mapping[str, Any],  
    *,  
    runner: Optional[Callable[..., Any]] = None,  
    validate: bool = True,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
    runner_kwargs: Optional[Mapping[str, Any]] = None,  
) -> Tuple[Any, Dict[str, Any]]:  
    """  
    Like run_deploy_bundle_1a, but returns (runner_result, run_meta).  
    """  
    loaded = load_deploy_bundle_1a(  
        deploy_bundle,  
        validate=validate,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
    )  
    workflow, selector_pack, run_meta = extract_runnable_from_deploy_bundle_1a(loaded)  
  
    r = runner if runner is not None else resolve_default_workflow_runner_callable()  
    result = _call_runner_deterministically(  
        r,  
        workflow=workflow,  
        selector_pack=selector_pack,  
        run_meta=run_meta,  
        runner_kwargs=runner_kwargs,  
    )  
    return result, run_meta  
  
  
def dev_smoke() -> None:  
    # Use an injected stub runner so this smoke test does not require Selenium.  
    from BUILD.build_3c_deploy_bundle_builder import build_stamp_validate_deploy_bundle_1a  
    from SNAP.snap_1a_workflow_capture import CapturedEvent  
    from SNAP.snap_1c_capture_bundle import build_capture_bundle_from_events  
  
    events = [  
        CapturedEvent(kind="navigate", seq=1, url="https://example.test/app"),  
        CapturedEvent(kind="click", seq=2, selector="#login"),  
    ]  
    cap = build_capture_bundle_from_events(events, bundle_name="captured")  
    dep = build_stamp_validate_deploy_bundle_1a(cap, strict=True)  
  
    called: Dict[str, Any] = {"ok": False}  
  
    def stub_runner(*, workflow: Dict[str, Any], selector_pack: Dict[str, Any], run_meta: Dict[str, Any]) -> Dict[str, Any]:  
        assert workflow["steps"][0]["action"] == "open"  
        assert workflow["steps"][1]["action"] == "click_selector"  
        assert isinstance(selector_pack.get("selectors"), Mapping)  
        assert run_meta["bundle_name"] == "captured"  
        assert str(run_meta["bundle_version"]).startswith("sha256:")  
        called["ok"] = True  
        return {"status": "ok"}  
  
    out = run_deploy_bundle_1a(dep, runner=stub_runner, validate=True)  
    assert out == {"status": "ok"}  
    assert called["ok"] is True  