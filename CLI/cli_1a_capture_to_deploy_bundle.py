from __future__ import annotations  
  
import argparse  
import json  
import os  
from typing import List, Optional  
  
from BUILD.build_3h_capture_to_deploy_bundle_pipeline import (  
    build_write_deploy_bundle_1a_from_capture_bundle_path,  
)  
from WORKFLOWS.workflow_1g_deploy_bundle_loader import load_deploy_bundle_1a_from_path  
  
__all__ = [  
    "build_arg_parser_1a",  
    "main",  
    "dev_smoke",  
]  
  
  
def build_arg_parser_1a() -> argparse.ArgumentParser:  
    p = argparse.ArgumentParser(  
        prog="capture_to_deploy_bundle_1a",  
        description="Convert a CAPTURE_BUNDLE_1A JSON file into a stamped DEPLOY_BUNDLE_1A JSON file.",  
    )  
    p.add_argument(  
        "--capture",  
        required=True,  
        help="Path to CAPTURE_BUNDLE_1A JSON file.",  
    )  
    p.add_argument(  
        "--out",  
        required=True,  
        help="Output path for DEPLOY_BUNDLE_1A JSON file.",  
    )  
    p.add_argument(  
        "--name",  
        default=None,  
        help="Optional deploy bundle name override.",  
    )  
    p.add_argument(  
        "--no-strict",  
        action="store_true",  
        help="Disable strict conversion checks (strict is default).",  
    )  
    p.add_argument(  
        "--pretty",  
        action="store_true",  
        help="Pretty-print output JSON (default is compact).",  
    )  
    p.add_argument(  
        "--no-atomic",  
        action="store_true",  
        help="Disable atomic write (default is atomic).",  
    )  
    p.add_argument(  
        "--allow-raw-selectors",  
        action="store_true",  
        help="Allow steps to include raw selectors (default requires selector_ref where applicable).",  
    )  
    return p  
  
  
def main(argv: Optional[List[str]] = None) -> int:  
    args = build_arg_parser_1a().parse_args(argv)  
  
    strict = not bool(args.no_strict)  
    require_selector_ref = not bool(args.allow_raw_selectors)  
    atomic = not bool(args.no_atomic)  
  
    dep = build_write_deploy_bundle_1a_from_capture_bundle_path(  
        args.capture,  
        args.out,  
        deploy_name=args.name,  
        strict=strict,  
        require_version_fingerprint=True,  
        require_selector_ref=require_selector_ref,  
        pretty=bool(args.pretty),  
        atomic=atomic,  
    )  
  
    # Minimal deterministic stdout: path + version (useful for scripts)  
    print(f"wrote={args.out}")  
    print(f"version={dep.get('version', '')}")  
    return 0  
  
  
def dev_smoke() -> None:  
    cap_path = "dev_smoke_tmp_capture_bundle_1a.json"  
    dep_path = "dev_smoke_tmp_deploy_bundle_1a.json"  
    try:  
        cap = {  
            "schema_id": "CAPTURE_BUNDLE_1A",  
            "name": "captured",  
            "workflow": {"steps": [{"action": "open", "url": "https://example.test/app"}]},  
            "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "captured", "selectors": {}},  
        }  
        with open(cap_path, "w", encoding="utf-8", newline="\n") as f:  
            f.write(json.dumps(cap, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")  
  
        rc = main(["--capture", cap_path, "--out", dep_path])  
        assert rc == 0  
        assert os.path.exists(dep_path)  
  
        loaded = load_deploy_bundle_1a_from_path(dep_path, validate=True)  
        assert loaded.get("schema_id") == "DEPLOY_BUNDLE_1A"  
        assert isinstance(loaded.get("version"), str) and loaded["version"].startswith("sha256:")  
    finally:  
        for p in (cap_path, dep_path, dep_path + ".tmp"):  
            try:  
                if os.path.exists(p):  
                    os.remove(p)  
            except Exception:  
                pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  