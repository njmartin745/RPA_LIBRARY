from __future__ import annotations  
  
import importlib  
import inspect  
from types import ModuleType  
from typing import Any, Callable, Optional, Sequence, Tuple  
  
__all__ = [  
    "resolve_latest_run_deploy_bundle_cli_module",  
    "resolve_latest_run_deploy_bundle_main",  
    "main",  
    "dev_smoke",  
]  
  
  
def resolve_latest_run_deploy_bundle_cli_module() -> ModuleType:  
    """  
    Resolve the newest available deploy-bundle CLI implementation.  
  
    Deterministic preference order:  
      CLI.cli_1g_run_deploy_bundle_with_report_fail_fast  
      CLI.cli_1f_run_deploy_bundle_with_report  
      CLI.cli_1e_run_deploy_bundle  
    """  
    candidates: Tuple[str, ...] = (  
        "CLI.cli_1g_run_deploy_bundle_with_report_fail_fast",  
        "CLI.cli_1f_run_deploy_bundle_with_report",  
        "CLI.cli_1e_run_deploy_bundle",  
    )  
  
    last_err: Optional[BaseException] = None  
    for mod_name in candidates:  
        try:  
            return importlib.import_module(mod_name)  
        except Exception as e:  
            last_err = e  
            continue  
  
    raise RuntimeError(f"Could not import any deploy-bundle CLI module. Last error: {last_err!r}")  
  
  
def resolve_latest_run_deploy_bundle_main() -> Callable[..., Any]:  
    """  
    Return the newest module's `main` callable.  
    """  
    mod = resolve_latest_run_deploy_bundle_cli_module()  
    main_fn = getattr(mod, "main", None)  
    if not callable(main_fn):  
        raise RuntimeError(f"Resolved module {mod.__name__} does not define a callable main()")  
    return main_fn  
  
  
def _call_main_adaptively(  
    main_fn: Callable[..., Any],  
    argv: Optional[Sequence[str]],  
    runner: Optional[Callable[..., Any]],  
) -> int:  
    """  
    Call main(argv) or main(argv, runner=...) depending on signature.  
    """  
    sig = inspect.signature(main_fn)  
    if "runner" in sig.parameters:  
        return int(main_fn(argv, runner=runner))  
    return int(main_fn(argv))  
  
  
def main(argv: Optional[Sequence[str]] = None, *, runner: Optional[Callable[..., Any]] = None) -> int:  
    """  
    Consolidated deploy-bundle CLI entrypoint.  
  
    - Uses the newest available deploy-bundle CLI module  
    - Adaptively passes `runner=` if the resolved main() supports it  
    """  
    main_fn = resolve_latest_run_deploy_bundle_main()  
    return _call_main_adaptively(main_fn, argv=argv, runner=runner)  
  
  
def dev_smoke() -> None:  
    # covered by dev smoke script  
    pass  