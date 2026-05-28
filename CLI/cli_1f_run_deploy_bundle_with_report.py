from __future__ import annotations  
  
import argparse  
import json  
from typing import Any, Callable, Dict, Mapping, Optional, Sequence  
  
from CLI.cli_1e_run_deploy_bundle import run_deploy_bundle_path_1a  
from REPORT.report_1e_deploy_bundle_validation_report_writer import (  
    write_deploy_bundle_validation_report_alongside_1a,  
)  
  
__all__ = [  
    "run_deploy_bundle_path_1a_with_optional_validation_report",  
    "build_arg_parser",  
    "main",  
    "dev_smoke",  
]  
  
  
def run_deploy_bundle_path_1a_with_optional_validation_report(  
    path: str,  
    *,  
    runner: Optional[Callable[..., Any]] = None,  
    validate: bool = True,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
    runner_kwargs: Optional[Mapping[str, Any]] = None,  
    write_validation_report: bool = False,  
    validation_report_path: Optional[str] = None,  
    overwrite_report: bool = True,  
) -> Dict[str, Any]:  
    """  
    Run a DEPLOY_BUNDLE_1A from path, optionally writing a validation report alongside it.  
  
    Returns a dict:  
      {  
        "result": <runner_result>,  
        "validation_report": {"path": <str>, "ok": <bool>} | None  
      }  
    """  
    report_info = None  
    if write_validation_report:  
        out_path, report = write_deploy_bundle_validation_report_alongside_1a(  
            path,  
            report_path=validation_report_path,  
            overwrite=overwrite_report,  
            require_version_fingerprint=require_version_fingerprint,  
            require_selector_ref=require_selector_ref,  
        )  
        ok = bool(report.get("validation", {}).get("ok"))  
        report_info = {"path": out_path, "ok": ok}  
  
    result = run_deploy_bundle_path_1a(  
        path,  
        runner=runner,  
        validate=validate,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
        runner_kwargs=runner_kwargs,  
    )  
  
    return {"result": result, "validation_report": report_info}  
  
  
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
    return p  
  
  
def _print_result(result: Any) -> None:  
    try:  
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))  
    except Exception:  
        print(str(result))  
  
  
def main(argv: Optional[Sequence[str]] = None) -> int:  
    """  
    Exit codes:  
      0 success  
      1 failure  
    """  
    p = build_arg_parser()  
    args = p.parse_args(list(argv) if argv is not None else None)  
  
    validate = not bool(args.no_validate)  
    require_version_fingerprint = not bool(args.allow_missing_version_fingerprint)  
    require_selector_ref = not bool(args.allow_raw_selectors)  
  
    try:  
        out = run_deploy_bundle_path_1a_with_optional_validation_report(  
            args.path,  
            validate=validate,  
            require_version_fingerprint=require_version_fingerprint,  
            require_selector_ref=require_selector_ref,  
            write_validation_report=bool(args.write_validation_report),  
            validation_report_path=args.validation_report_path,  
            overwrite_report=not bool(args.no_overwrite_report),  
        )  
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