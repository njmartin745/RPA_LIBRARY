from __future__ import annotations  
  
import argparse  
import json  
import os  
import sys  
from typing import Any, Dict, List, Optional  
  
from BUILD.build_3e_bundle_build_manifest_integrator import (  
    build_bundle_out_dir_doc_index_and_manifest_1a,  
)  
  
__all__ = [  
    "build_arg_parser_1a",  
    "run_cli_1a",  
    "dev_smoke",  
]  
  
  
def build_arg_parser_1a() -> argparse.ArgumentParser:  
    p = argparse.ArgumentParser(  
        prog="bundle-doc-index-and-manifest",  
        description="Write doc_index_artifact_1a.json and build_manifest_artifact_1a.json into a bundle output directory.",  
    )  
    p.add_argument(  
        "--bundle-out-dir",  
        required=True,  
        help="Bundle output directory to write artifacts into.",  
    )  
    p.add_argument(  
        "--repo-root",  
        default=".",  
        help="Repository root (default: .).",  
    )  
    p.add_argument(  
        "--doc-dir",  
        default="DOC",  
        help="DOC directory under repo root (default: DOC).",  
    )  
    p.add_argument(  
        "--strict-imports",  
        action="store_true",  
        help="Fail if any DOC module cannot be imported.",  
    )  
    p.add_argument(  
        "--no-overwrite",  
        action="store_true",  
        help="Do not overwrite existing artifact files.",  
    )  
    p.add_argument(  
        "--doc-index-filename",  
        default="doc_index_artifact_1a.json",  
        help="Output filename for the doc index artifact.",  
    )  
    p.add_argument(  
        "--manifest-filename",  
        default="build_manifest_artifact_1a.json",  
        help="Output filename for the build manifest artifact.",  
    )  
    return p  
  
  
def run_cli_1a(argv: Optional[List[str]] = None) -> int:  
    """  
    CLI entrypoint.  
  
    Returns:  
      0 on success, non-zero on failure.  
    """  
    parser = build_arg_parser_1a()  
    ns = parser.parse_args(argv)  
  
    bundle_out_dir = str(ns.bundle_out_dir)  
    repo_root = str(ns.repo_root)  
    doc_dir = str(ns.doc_dir)  
    strict_imports = bool(ns.strict_imports)  
    overwrite = not bool(ns.no_overwrite)  
    doc_index_filename = str(ns.doc_index_filename)  
    manifest_filename = str(ns.manifest_filename)  
  
    try:  
        os.makedirs(bundle_out_dir, exist_ok=True)  
        res: Dict[str, Any] = build_bundle_out_dir_doc_index_and_manifest_1a(  
            repo_root=repo_root,  
            doc_dir=doc_dir,  
            bundle_out_dir=bundle_out_dir,  
            doc_index_filename=doc_index_filename,  
            manifest_filename=manifest_filename,  
            strict_imports=strict_imports,  
            overwrite=overwrite,  
        )  
    except Exception as e:  
        print(f"ERROR: {e}", file=sys.stderr)  
        return 2  
  
    print(json.dumps(res, ensure_ascii=False, sort_keys=True, indent=2))  
    return 0  
  
  
def dev_smoke() -> None:  
    # covered by dev smoke script  
    pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(run_cli_1a())  