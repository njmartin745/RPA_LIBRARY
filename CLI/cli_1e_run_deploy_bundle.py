from __future__ import annotations  
  
import argparse  
import json  
from typing import Any, Callable, Dict, Mapping, Optional, Sequence  
  
from RUN.run_1e_deploy_bundle_runner_adapter import run_deploy_bundle_1a  
from WORKFLOWS.workflow_1g_deploy_bundle_loader import load_deploy_bundle_1a_from_path  
  
__all__ = [  
    "run_deploy_bundle_path_1a",  
    "build_arg_parser",  
    "main",  
    "dev_smoke",  
]  
  
  
def run_deploy_bundle_path_1a(  
    path: str,  
    *,  
    runner: Optional[Callable[..., Any]] = None,  
    validate: bool = True,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
    runner_kwargs: Optional[Mapping[str, Any]] = None,  
) -> Any:  
    """  
    Load a DEPLOY_BUNDLE_1A from JSON file path and run it via the deploy-bundle runner adapter.  
    """  
    deploy_bundle = load_deploy_bundle_1a_from_path(  
        path,  
        validate=validate,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
    )  
    return run_deploy_bundle_1a(  
        deploy_bundle,  
        runner=runner,  
        validate=validate,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
        runner_kwargs=runner_kwargs,  
    )  
  
  
def build_arg_parser() -> argparse.ArgumentParser:  
    p = argparse.ArgumentParser(prog="rpa-run-deploy-bundle", add_help=True)  
    p.add_argument("path", help="Path to DEPLOY_BUNDLE_1A JSON file")  
    p.add_argument("--no-validate", action="store_true", help="Skip DEPLOY_BUNDLE_1A validation")  
    p.add_argument(  
        "--allow-missing-version-fingerprint",  
        action="store_true",  
        help="Do not require version/fingerprint fields",  
    )  
    p.add_argument(  
        "--allow-raw-selectors",  
        action="store_true",  
        help="Do not require selector_ref (permit raw selector usage)",  
    )  
    return p  
  
  
def _print_result(result: Any) -> None:  
    # Deterministic printing when JSON-serializable; fallback to string.  
    try:  
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))  
    except Exception:  
        print(str(result))  
  
  
def main(argv: Optional[Sequence[str]] = None) -> int:  
    """  
    CLI entrypoint.  
  
    Returns process exit code:  
      0 success  
      1 failure (exception)  
    """  
    p = build_arg_parser()  
    args = p.parse_args(list(argv) if argv is not None else None)  
  
    validate = not bool(args.no_validate)  
    require_version_fingerprint = not bool(args.allow_missing_version_fingerprint)  
    require_selector_ref = not bool(args.allow_raw_selectors)  
  
    try:  
        result = run_deploy_bundle_path_1a(  
            args.path,  
            validate=validate,  
            require_version_fingerprint=require_version_fingerprint,  
            require_selector_ref=require_selector_ref,  
        )  
        _print_result(result)  
        return 0  
    except Exception as e:  
        # Keep failure output minimal and deterministic.  
        print(f"ERROR: {e}")  
        return 1  
  
  
def dev_smoke() -> None:  
    # Exercised via dev smoke script with an injected stub runner (no Selenium).  
    pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  