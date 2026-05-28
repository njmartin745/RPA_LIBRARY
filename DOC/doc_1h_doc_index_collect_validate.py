"""  
DOC-1H — Doc Index Collect + Validate Wrapper  
  
Single responsibility:  
- Collect doc-index entries using DOC-1F and validate them using DOC-1G.  
  
Why:  
- Prevent silent omissions: if a module is discovered but its entry shape is wrong,  
  validation can fail fast with actionable errors.  
  
Deterministic, side-effect free beyond what the collector already does.  
"""  
  
from __future__ import annotations  
  
from typing import Any, Dict, List, Mapping, Sequence  
  
from DOC.doc_1f_doc_index_aggregator import collect_doc_index_entries_1a  
from DOC.doc_1g_doc_index_entry_contract import validate_doc_index_entries_1a  
  
__all__ = [  
    "format_doc_index_validation_errors_1a",  
    "collect_and_validate_doc_index_entries_1a",  
    "dev_smoke",  
]  
  
  
def format_doc_index_validation_errors_1a(errors: Mapping[int, Sequence[str]]) -> str:  
    lines: List[str] = ["DOC index entry validation failed:"]  
    for idx in sorted(errors.keys()):  
        lines.append(f"- entry[{idx}]:")  
        for msg in errors[idx]:  
            lines.append(f"  - {msg}")  
    return "\n".join(lines)  
  
  
def collect_and_validate_doc_index_entries_1a(  
    module_names: Sequence[str],  
    *,  
    strict_imports: bool = False,  
    strict_validation: bool = True,  
) -> List[Dict[str, Any]]:  
    entries = collect_doc_index_entries_1a(list(module_names), strict=strict_imports)  
    errors = validate_doc_index_entries_1a(entries)  
    if errors and strict_validation:  
        raise ValueError(format_doc_index_validation_errors_1a(errors))  
    return list(entries)  
  
  
def dev_smoke() -> None:  
    from DOC.doc_1f_doc_index_aggregator import iter_doc_module_names_in_dir_1a  
  
    mods = list(iter_doc_module_names_in_dir_1a(repo_root=".", doc_dir="DOC"))  
    entries = collect_and_validate_doc_index_entries_1a(  
        mods, strict_imports=False, strict_validation=True  
    )  
    assert len(entries) >= 2  
    assert any(  
        isinstance(e, dict)  
        and e.get("module") == "CLI.cli_1i_bundle_doc_index_and_manifest_cli"  
        for e in entries  
    )  