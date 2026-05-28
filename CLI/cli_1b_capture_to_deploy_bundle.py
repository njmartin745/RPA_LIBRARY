from __future__ import annotations  
  
import json  
import os  
import sys  
from typing import List, Optional  
  
from CLI.cli_1a_capture_to_deploy_bundle import build_arg_parser_1a  
from BUILD.build_3h_capture_to_deploy_bundle_pipeline import (  
    build_write_deploy_bundle_1a_from_capture_bundle_path,  
)  
from WORKFLOWS.workflow_1g_deploy_bundle_loader import load_deploy_bundle_1a_from_path  
  
__all__ = [  
    "build_arg_parser_1a",  
    "main",  
    "dev_smoke",  
]  
  
  
def main(argv: Optional[List[str]] = None) -> int:  
    args = build_arg_parser_1a().parse_args(argv)  
  
    capture_path = args.capture  
    out_path = args.out  
  
    if not os.path.isfile(capture_path):  
        print(f"ERROR: capture file not found: {capture_path}", file=sys.stderr)  
        print(f"cwd={os.getcwd()}", file=sys.stderr)  
        return 2  
  
    strict = not bool(args.no_strict)  
    require_selector_ref = not bool(args.allow_raw_selectors)  
    atomic = not bool(args.no_atomic)  
  
    try:  
        dep = build_write_deploy_bundle_1a_from_capture_bundle_path(  
            capture_path,  
            out_path,  
            deploy_name=args.name,  
            strict=strict,  
            require_version_fingerprint=True,  
            require_selector_ref=require_selector_ref,  
            pretty=bool(args.pretty),  
            atomic=atomic,  
        )  
    except json.JSONDecodeError as e:  
        print(f"ERROR: invalid JSON in capture file: {capture_path}", file=sys.stderr)  
        print(str(e), file=sys.stderr)  
        return 3  
    except (ValueError, TypeError) as e:  
        print("ERROR: could not build deploy bundle from capture bundle", file=sys.stderr)  
        print(str(e), file=sys.stderr)  
        return 4  
  
    # Optional sanity check: ensure what we wrote can be loaded/validated.  
    try:  
        _ = load_deploy_bundle_1a_from_path(out_path, validate=True)  
    except Exception as e:  
        print("ERROR: wrote deploy bundle but failed to reload/validate it", file=sys.stderr)  
        print(str(e), file=sys.stderr)  
        return 5  
  
    print(f"wrote={out_path}")  
    print(f"version={dep.get('version', '')}")  
    return 0  
  
  
def dev_smoke() -> None:  
    # 1) Missing file should not raise; should return rc=2  
    rc = main(["--capture", "does_not_exist_capture.json", "--out", "x.json"])  
    assert rc == 2  
  
    # 2) Happy path: reuse CLI 1a dev_smoke-style setup  
    from CLI.cli_1a_capture_to_deploy_bundle import dev_smoke as dev_smoke_1a  
  
    dev_smoke_1a()  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  