from __future__ import annotations  
  
from typing import Any, Dict, List, Mapping  
  
__all__ = [  
    "DOC_INDEX_ENTRY_1A",  
    "DOC_INDEX_ENTRY",  
    "DOC_INDEX_ENTRIES_1A",  
    "DOC_INDEX_ENTRIES",  
    "get_doc_index_entries_1a",  
    "get_doc_index_entries",  
    "dev_smoke",  
]  
  
# This module must match the shape that DOC.doc_1f_doc_index_aggregator.collect_doc_index_entries_1a()  
# is already collecting successfully from DOC.doc_1e_cli_run_deploy_bundle_cli_resolver_entry.  
DOC_INDEX_ENTRY_1A: Dict[str, Any] = {  
    "kind": "doc_index_entry",  
    "layer": "CLI",  
    "module": "CLI.cli_1i_bundle_doc_index_and_manifest_cli",  
    "name": "Bundle doc index + manifest CLI",  
    "summary": "Generate doc_index_artifact_1a.json and build_manifest_artifact_1a.json into a bundle output directory.",  
    "usage": {  
        "python_module": "CLI.cli_1i_bundle_doc_index_and_manifest_cli",  
        "callable": "run_cli_1a",  
        "examples": [  
            "python -c \"from CLI.cli_1i_bundle_doc_index_and_manifest_cli import run_cli_1a; raise SystemExit(run_cli_1a(['--bundle-out-dir','OUT']))\""  
        ],  
    },  
}  
  
# Compatibility aliases (collector may look for either singular/plural, suffixed/non-suffixed).  
DOC_INDEX_ENTRY: Dict[str, Any] = DOC_INDEX_ENTRY_1A  
  
DOC_INDEX_ENTRIES_1A: List[Mapping[str, Any]] = [DOC_INDEX_ENTRY_1A]  
DOC_INDEX_ENTRIES: List[Mapping[str, Any]] = DOC_INDEX_ENTRIES_1A  
  
  
def get_doc_index_entries_1a() -> List[Mapping[str, Any]]:  
    return list(DOC_INDEX_ENTRIES_1A)  
  
  
def get_doc_index_entries() -> List[Mapping[str, Any]]:  
    return list(DOC_INDEX_ENTRIES_1A)  
  
  
def dev_smoke() -> None:  
    # covered by dev smoke script  
    pass  