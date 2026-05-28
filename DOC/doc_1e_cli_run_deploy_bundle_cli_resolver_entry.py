from __future__ import annotations  
  
from typing import Any, Dict, Mapping  
  
__all__ = [  
    "DOC_INDEX_ENTRY_1A",  
    "get_doc_index_entry_1a",  
    "dev_smoke",  
]  
  
DOC_INDEX_ENTRY_1A: Dict[str, Any] = {  
    "kind": "doc_index_entry",  
    "layer": "CLI",  
    "module": "CLI.cli_1h_run_deploy_bundle_cli_resolver",  
    "name": "Deploy bundle runner CLI (resolver)",  
    "summary": (  
        "Consolidated deploy-bundle CLI entrypoint that resolves to the newest available "  
        "implementation (prefers cli_1g, then cli_1f, then cli_1e)."  
    ),  
    "usage": {  
        "python_module": "CLI.cli_1h_run_deploy_bundle_cli_resolver",  
        "callable": "main",  
        "examples": [  
            "python -c \"from CLI.cli_1h_run_deploy_bundle_cli_resolver import main; raise SystemExit(main(['bundle.json']))\"",  
            "python -c \"from CLI.cli_1h_run_deploy_bundle_cli_resolver import main; raise SystemExit(main(['bundle.json','--write-validation-report']))\"",  
        ],  
    },  
}  
  
  
def get_doc_index_entry_1a() -> Mapping[str, Any]:  
    """  
    Doc/index entry describing the consolidated deploy-bundle CLI resolver.  
  
    Intended to be consumed by the library doc/index tooling.  
    """  
    return DOC_INDEX_ENTRY_1A  
  
  
def dev_smoke() -> None:  
    # covered by dev smoke script  
    pass  