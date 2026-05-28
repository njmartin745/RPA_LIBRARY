from __future__ import annotations  
  
import argparse  
import json  
from typing import Any, Dict, Optional, Sequence  
  
from DOC.doc_1f_doc_index_aggregator import (  
    build_doc_index_artifact_1a,  
    collect_doc_index_entries_1a,  
    iter_doc_module_names_in_dir_1a,  
    write_doc_index_artifact_1a,  
)  
  
__all__ = [  
    "build_arg_parser",  
    "build_doc_index_artifact_from_repo_1a",  
    "main",  
    "dev_smoke",  
]  
  
  
def build_doc_index_artifact_from_repo_1a(  
    *,  
    repo_root: str = ".",  
    doc_dir: str = "DOC",  
    out_path: str = "DOC/doc_index_artifact_1a.json",  
    strict_imports: bool = False,  
    overwrite: bool = True,  
) -> Dict[str, Any]:  
    module_names = iter_doc_module_names_in_dir_1a(repo_root=repo_root, doc_dir=doc_dir)  
    entries = collect_doc_index_entries_1a(module_names, strict=strict_imports)  
    artifact = build_doc_index_artifact_1a(entries)  
    written = write_doc_index_artifact_1a(artifact, out_path, overwrite=overwrite)  
    return {"out_path": written, "count": int(artifact.get("count", 0)), "schema_id": artifact.get("schema_id")}  
  
  
def build_arg_parser() -> argparse.ArgumentParser:  
    p = argparse.ArgumentParser(prog="rpa-build-doc-index", add_help=True)  
    p.add_argument("--repo-root", default=".", help="Repo root (default: .)")  
    p.add_argument("--doc-dir", default="DOC", help="DOC directory (default: DOC)")  
    p.add_argument(  
        "--out",  
        default="DOC/doc_index_artifact_1a.json",  
        help="Output JSON path (default: DOC/doc_index_artifact_1a.json)",  
    )  
    p.add_argument(  
        "--strict",  
        action="store_true",  
        help="Fail if any DOC module import fails during discovery/collection (default: non-strict)",  
    )  
    p.add_argument(  
        "--no-overwrite",  
        action="store_true",  
        help="Fail if output path already exists",  
    )  
    return p  
  
  
def main(argv: Optional[Sequence[str]] = None) -> int:  
    """  
    Exit codes:  
      0 success  
      1 failure  
    """  
    p = build_arg_parser()  
    args = p.parse_args(list(argv) if argv is not None else None)  
  
    try:  
        result = build_doc_index_artifact_from_repo_1a(  
            repo_root=str(args.repo_root),  
            doc_dir=str(args.doc_dir),  
            out_path=str(args.out),  
            strict_imports=bool(args.strict),  
            overwrite=not bool(args.no_overwrite),  
        )  
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))  
        return 0  
    except Exception as e:  
        print(f"ERROR: {e}")  
        return 1  
  
  
def dev_smoke() -> None:  
    # covered by dev smoke script  
    pass  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  