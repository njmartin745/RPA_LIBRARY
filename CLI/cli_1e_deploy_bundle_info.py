from __future__ import annotations  
  
import argparse  
import json  
import os  
import sys  
from typing import Dict, List, Optional, Tuple  
  
from BUILD.build_3h_capture_to_deploy_bundle_pipeline import (  
    build_write_deploy_bundle_1a_from_capture_bundle,  
)  
from WORKFLOWS.workflow_1g_deploy_bundle_loader import load_deploy_bundle_1a_from_path  
  
__all__ = [  
    "build_arg_parser_1e",  
    "summarize_deploy_bundle_1a",  
    "main",  
    "dev_smoke",  
]  
  
  
def build_arg_parser_1e() -> argparse.ArgumentParser:  
    p = argparse.ArgumentParser(  
        prog="deploy_bundle_info_1e",  
        description="Load + validate a DEPLOY_BUNDLE_1A JSON file and print a deterministic summary.",  
    )  
    p.add_argument("--deploy", required=True, help="Path to DEPLOY_BUNDLE_1A JSON file.")  
    p.add_argument("--json", action="store_true", help="Emit JSON summary (default: text).")  
    return p  
  
  
def _count_actions_1a(steps: List[dict]) -> Dict[str, int]:  
    counts: Dict[str, int] = {}  
    for s in steps:  
        if not isinstance(s, dict):  
            continue  
        a = s.get("action")  
        if not isinstance(a, str):  
            continue  
        counts[a] = counts.get(a, 0) + 1  
    return counts  
  
  
def summarize_deploy_bundle_1a(dep: dict) -> dict:  
    workflow = dep.get("workflow") if isinstance(dep, dict) else None  
    steps = []  
    if isinstance(workflow, dict) and isinstance(workflow.get("steps"), list):  
        steps = workflow["steps"]  
  
    selector_pack = dep.get("selector_pack") if isinstance(dep, dict) else None  
    selectors = {}  
    if isinstance(selector_pack, dict) and isinstance(selector_pack.get("selectors"), dict):  
        selectors = selector_pack["selectors"]  
  
    return {  
        "schema_id": dep.get("schema_id"),  
        "name": dep.get("name"),  
        "version": dep.get("version"),  
        "steps_count": len(steps),  
        "actions_count": _count_actions_1a(steps),  
        "selectors_count": len(selectors),  
    }  
  
  
def main(argv: Optional[List[str]] = None) -> int:  
    args = build_arg_parser_1e().parse_args(argv)  
  
    if not os.path.isfile(args.deploy):  
        print(f"ERROR: deploy bundle not found: {args.deploy}", file=sys.stderr)  
        print(f"cwd={os.getcwd()}", file=sys.stderr)  
        return 2  
  
    try:  
        dep = load_deploy_bundle_1a_from_path(args.deploy, validate=True)  
    except Exception as e:  
        print(f"ERROR: failed to load/validate deploy bundle: {args.deploy}", file=sys.stderr)  
        print(str(e), file=sys.stderr)  
        return 3  
  
    summary = summarize_deploy_bundle_1a(dep)  
  
    if args.json:  
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))  
    else:  
        # deterministic text  
        print(f"schema_id={summary.get('schema_id')}")  
        print(f"name={summary.get('name')}")  
        print(f"version={summary.get('version')}")  
        print(f"steps_count={summary.get('steps_count')}")  
        print(f"selectors_count={summary.get('selectors_count')}")  
        for k in sorted((summary.get("actions_count") or {}).keys()):  
            print(f"action.{k}={summary['actions_count'][k]}")  
  
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
        # Build a real deploy bundle using the existing pipeline (ensures schema correctness)  
        build_write_deploy_bundle_1a_from_capture_bundle(  
            cap,  
            dep_path,  
            deploy_name="deploy",  
            strict=True,  
            require_version_fingerprint=True,  
            require_selector_ref=False,  
            pretty=False,  
            atomic=True,  
        )  
  
        rc = main(["--deploy", dep_path, "--json"])  
        assert rc == 0  
    finally:  
        for p in (cap_path, dep_path, dep_path + ".tmp"):  
            try:  
                if os.path.exists(p):  
                    os.remove(p)  
            except Exception:  
                pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  