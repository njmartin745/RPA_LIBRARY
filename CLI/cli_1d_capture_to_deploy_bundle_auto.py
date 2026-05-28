from __future__ import annotations  
  
import argparse  
import json  
import os  
import shutil  
import sys  
from typing import List, Optional  
  
from BUILD.build_3h_capture_to_deploy_bundle_pipeline import (  
    build_write_deploy_bundle_1a_from_capture_bundle,  
)  
from WORKFLOWS.workflow_1g_deploy_bundle_loader import load_deploy_bundle_1a_from_path  
  
__all__ = [  
    "discover_capture_bundle_1a_path",  
    "build_arg_parser_1d",  
    "main",  
    "dev_smoke",  
]  
  
  
def discover_capture_bundle_1a_path(root_dir: str, *, filename: str = "capture_bundle_1a.json") -> Optional[str]:  
    """  
    Deterministically discover a capture bundle path under root_dir by filename.  
  
    If multiple matches exist, returns the lexicographically greatest normalized path.  
    """  
    if not isinstance(root_dir, str) or not root_dir.strip():  
        raise ValueError("root_dir must be a non-empty string")  
    if not os.path.isdir(root_dir):  
        return None  
  
    matches: List[str] = []  
    for base, _dirs, files in os.walk(root_dir):  
        for fn in files:  
            if fn == filename:  
                matches.append(os.path.normpath(os.path.join(base, fn)))  
  
    if not matches:  
        return None  
    matches.sort()  
    return matches[-1]  
  
  
def build_arg_parser_1d() -> argparse.ArgumentParser:  
    p = argparse.ArgumentParser(  
        prog="capture_to_deploy_bundle_1d",  
        description=(  
            "Convert a CAPTURE_BUNDLE_1A JSON file into a stamped DEPLOY_BUNDLE_1A JSON file.\n"  
            "Supports BOM-tolerant JSON input and optional auto-discovery under a root directory."  
        ),  
    )  
    p.add_argument(  
        "--capture",  
        default=None,  
        help="Path to CAPTURE_BUNDLE_1A JSON file. If omitted, use --auto to discover one.",  
    )  
    p.add_argument(  
        "--auto",  
        action="store_true",  
        help="Auto-discover capture_bundle_1a.json under --auto-root (default: .\\dev).",  
    )  
    p.add_argument(  
        "--auto-root",  
        default="dev",  
        help="Root directory for --auto discovery (default: dev).",  
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
    args = build_arg_parser_1d().parse_args(argv)  
  
    capture_path = args.capture  
    if capture_path is None:  
        if not args.auto:  
            print("ERROR: --capture is required unless --auto is used", file=sys.stderr)  
            return 2  
        capture_path = discover_capture_bundle_1a_path(args.auto_root)  
        if capture_path is None:  
            print(f"ERROR: no capture_bundle_1a.json found under: {args.auto_root}", file=sys.stderr)  
            print(f"cwd={os.getcwd()}", file=sys.stderr)  
            return 6  
  
    if not os.path.isfile(capture_path):  
        print(f"ERROR: capture file not found: {capture_path}", file=sys.stderr)  
        print(f"cwd={os.getcwd()}", file=sys.stderr)  
        return 2  
  
    strict = not bool(args.no_strict)  
    require_selector_ref = not bool(args.allow_raw_selectors)  
    atomic = not bool(args.no_atomic)  
  
    try:  
        # BOM tolerant input  
        with open(capture_path, "r", encoding="utf-8-sig") as f:  
            cap = json.load(f)  
        if not isinstance(cap, dict):  
            print("ERROR: capture JSON root must be an object", file=sys.stderr)  
            return 4  
  
        dep = build_write_deploy_bundle_1a_from_capture_bundle(  
            cap,  
            args.out,  
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
        _ = load_deploy_bundle_1a_from_path(args.out, validate=True)  
    except Exception as e:  
        print("ERROR: wrote deploy bundle but failed to reload/validate it", file=sys.stderr)  
        print(str(e), file=sys.stderr)  
        return 5  
  
    print(f"capture={capture_path}")  
    print(f"wrote={args.out}")  
    print(f"version={dep.get('version', '')}")  
    return 0  
  
  
def dev_smoke() -> None:  
    auto_root = "dev_smoke_tmp_auto_root"  
    dep_path = "dev_smoke_tmp_deploy_bundle_1a.json"  
    try:  
        os.makedirs(os.path.join(auto_root, "a"), exist_ok=True)  
        os.makedirs(os.path.join(auto_root, "b"), exist_ok=True)  
  
        cap = {  
            "schema_id": "CAPTURE_BUNDLE_1A",  
            "name": "captured",  
            "workflow": {"steps": [{"action": "open", "url": "https://example.test/app"}]},  
            "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "captured", "selectors": {}},  
        }  
  
        # Two candidates; lexicographically "b" should win deterministically.  
        with open(os.path.join(auto_root, "a", "capture_bundle_1a.json"), "w", encoding="utf-8", newline="\n") as f:  
            f.write(json.dumps(cap, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")  
        with open(os.path.join(auto_root, "b", "capture_bundle_1a.json"), "w", encoding="utf-8", newline="\n") as f:  
            f.write(json.dumps(cap, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")  
  
        picked = discover_capture_bundle_1a_path(auto_root)  
        assert picked is not None and os.path.normpath(os.path.join(auto_root, "b", "capture_bundle_1a.json")) == picked  
  
        rc = main(["--auto", "--auto-root", auto_root, "--out", dep_path])  
        assert rc == 0  
        loaded = load_deploy_bundle_1a_from_path(dep_path, validate=True)  
        assert loaded.get("schema_id") == "DEPLOY_BUNDLE_1A"  
    finally:  
        for p in (dep_path, dep_path + ".tmp"):  
            try:  
                if os.path.exists(p):  
                    os.remove(p)  
            except Exception:  
                pass  
        try:  
            if os.path.isdir(auto_root):  
                shutil.rmtree(auto_root)  
        except Exception:  
            pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  