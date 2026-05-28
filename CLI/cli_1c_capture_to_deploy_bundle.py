from __future__ import annotations  
  
import json  
import os  
import sys  
from typing import List, Optional  
  
from CLI.cli_1a_capture_to_deploy_bundle import build_arg_parser_1a  
from BUILD.build_3h_capture_to_deploy_bundle_pipeline import (  
    build_write_deploy_bundle_1a_from_capture_bundle,  
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
        with open(capture_path, "r", encoding="utf-8-sig") as f:  
            cap = json.load(f)  
        if not isinstance(cap, dict):  
            print("ERROR: capture JSON root must be an object", file=sys.stderr)  
            return 4  
  
        dep = build_write_deploy_bundle_1a_from_capture_bundle(  
            cap,  
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
    cap_path = "dev_smoke_tmp_capture_bundle_1a_bom.json"  
    dep_path = "dev_smoke_tmp_deploy_bundle_1a.json"  
    try:  
        cap = {  
            "schema_id": "CAPTURE_BUNDLE_1A",  
            "name": "captured",  
            "workflow": {"steps": [{"action": "open", "url": "https://example.test/app"}]},  
            "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "captured", "selectors": {}},  
        }  
        # Write with BOM (utf-8-sig) to ensure we tolerate it  
        with open(cap_path, "w", encoding="utf-8-sig", newline="\n") as f:  
            f.write(json.dumps(cap, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")  
  
        rc = main(["--capture", cap_path, "--out", dep_path])  
        assert rc == 0  
        loaded = load_deploy_bundle_1a_from_path(dep_path, validate=True)  
        assert loaded.get("schema_id") == "DEPLOY_BUNDLE_1A"  
    finally:  
        for p in (cap_path, dep_path, dep_path + ".tmp"):  
            try:  
                if os.path.exists(p):  
                    os.remove(p)  
            except Exception:  
                pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  