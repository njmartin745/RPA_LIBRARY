from __future__ import annotations  
  
import argparse  
import json  
from typing import Any, Callable, Mapping, Optional, Sequence  
  
from CLI.cli_1f_run_deploy_bundle_with_report import (  
    run_deploy_bundle_path_1a_with_optional_validation_report,  
)  
  
__all__ = [  
    "build_arg_parser",  
    "main",  
    "dev_smoke",  
]  
  
  
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
  
    p.add_argument(  
        "--write-validation-report",  
        action="store_true",  
        help="Write a deploy bundle validation report JSON alongside the bundle",  
    )  
    p.add_argument(  
        "--validation-report-path",  
        default=None,  
        help="Optional explicit report path (default: alongside bundle as *.validation.json)",  
    )  
    p.add_argument(  
        "--no-overwrite-report",  
        action="store_true",  
        help="Fail if the report path already exists",  
    )  
    p.add_argument(  
        "--fail-if-report-not-ok",  
        action="store_true",  
        help="Exit code 1 if the written validation report has ok=false (requires --write-validation-report)",  
    )  
    return p  
  
  
def _print_result(result: Any) -> None:  
    try:  
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))  
    except Exception:  
        print(str(result))  
  
  
def main(argv: Optional[Sequence[str]] = None, *, runner: Optional[Callable[..., Any]] = None) -> int:  
    """  
    Exit codes:  
      0 success  
      1 failure (exception OR report ok=false when --fail-if-report-not-ok)  
    """  
    p = build_arg_parser()  
    args = p.parse_args(list(argv) if argv is not None else None)  
  
    validate = not bool(args.no_validate)  
    require_version_fingerprint = not bool(args.allow_missing_version_fingerprint)  
    require_selector_ref = not bool(args.allow_raw_selectors)  
  
    if bool(args.fail_if_report_not_ok) and (not bool(args.write_validation_report)):  
        print("ERROR: --fail-if-report-not-ok requires --write-validation-report")  
        return 1  
  
    try:  
        out = run_deploy_bundle_path_1a_with_optional_validation_report(  
            args.path,  
            runner=runner,  
            validate=validate,  
            require_version_fingerprint=require_version_fingerprint,  
            require_selector_ref=require_selector_ref,  
            write_validation_report=bool(args.write_validation_report),  
            validation_report_path=args.validation_report_path,  
            overwrite_report=not bool(args.no_overwrite_report),  
        )  
  
        if bool(args.fail_if_report_not_ok):  
            rep = out.get("validation_report")  
            if isinstance(rep, Mapping) and (rep.get("ok") is False):  
                _print_result(out)  
                return 1  
  
        _print_result(out)  
        return 0  
    except Exception as e:  
        print(f"ERROR: {e}")  
        return 1  
  
  
def dev_smoke() -> None:  
    # covered by dev smoke script  
    pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  