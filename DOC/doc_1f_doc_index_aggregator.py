from __future__ import annotations
  
import importlib  
import json  
import os  
from types import ModuleType  
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple  
  
__all__ = [  
    "iter_doc_module_names_in_dir_1a",  
    "load_doc_index_entry_from_module_1a",  
    "collect_doc_index_entries_1a",  
    "merge_doc_index_entries_1a",  
    "build_doc_index_artifact_1a",  
    "write_doc_index_artifact_1a",  
    "dev_smoke",  
]  
  
DOC_INDEX_ARTIFACT_SCHEMA_ID = "DOC_INDEX_ARTIFACT_1A"  
  
  
def iter_doc_module_names_in_dir_1a(  
    *,  
    repo_root: str = ".",  
    doc_dir: str = "DOC",  
    filename_prefix: str = "doc_",  
) -> List[str]:  
    """  
    Deterministically discover DOC modules on disk (sorted), returning importable module names.  
  
    Example return values:  
      ["DOC.doc_1a_library_index", "DOC.doc_1e_cli_run_deploy_bundle_cli_resolver_entry", ...]  
    """  
    base = os.path.join(repo_root, doc_dir)  
    if not os.path.isdir(base):  
        raise FileNotFoundError(base)  
  
    names: List[str] = []  
    for fn in sorted(os.listdir(base)):  
        if not fn.endswith(".py"):  
            continue  
        if fn == "__init__.py":  
            continue  
        if not fn.startswith(filename_prefix):  
            continue  
        mod = fn[:-3]  # strip .py  
        names.append(f"{doc_dir}.{mod}")  
    return names  
  
  
def load_doc_index_entry_from_module_1a(mod: ModuleType) -> Optional[Mapping[str, Any]]:  
    """  
    Load a single doc index entry from a DOC module if present.  
  
    Supports either:  
      - get_doc_index_entry_1a() -> Mapping  
      - DOC_INDEX_ENTRY_1A: Mapping  
  
    Returns None if the module doesn't expose an entry or if the entry kind != "doc_index_entry".  
    """  
    entry: Optional[Mapping[str, Any]] = None  
  
    getter = getattr(mod, "get_doc_index_entry_1a", None)  
    if callable(getter):  
        got = getter()  
        if isinstance(got, Mapping):  
            entry = got  
  
    if entry is None:  
        got2 = getattr(mod, "DOC_INDEX_ENTRY_1A", None)  
        if isinstance(got2, Mapping):  
            entry = got2  
  
    if entry is None:  
        return None  
  
    if entry.get("kind") != "doc_index_entry":  
        return None  
  
    return entry  
  
  
def collect_doc_index_entries_1a(  
    module_names: Sequence[str],  
    *,  
    strict: bool = True,  
) -> List[Mapping[str, Any]]:  
    """  
    Import modules and collect their doc_index_entry records.  
  
    strict=True: import or extraction failures raise  
    strict=False: failures are skipped  
    """  
    entries: List[Mapping[str, Any]] = []  
    for name in module_names:  
        try:  
            mod = importlib.import_module(name)  
            entry = load_doc_index_entry_from_module_1a(mod)  
            if entry is not None:  
                entries.append(entry)  
        except Exception:  
            if strict:  
                raise  
            continue  
    return entries  
  
  
def merge_doc_index_entries_1a(entries: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:  
    """  
    Merge/dedupe entries deterministically by (layer, module), preferring the first occurrence.  
    Returns a sorted list by (layer, module).  
    """  
    seen: set[Tuple[str, str]] = set()  
    merged: List[Dict[str, Any]] = []  
    for e in entries:  
        layer = str(e.get("layer", ""))  
        module = str(e.get("module", ""))  
        key = (layer, module)  
        if key in seen:  
            continue  
        seen.add(key)  
        merged.append(dict(e))  
  
    merged.sort(key=lambda x: (str(x.get("layer", "")), str(x.get("module", ""))))  
    return merged  
  
  
def build_doc_index_artifact_1a(entries: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:  
    merged = merge_doc_index_entries_1a(entries)  
    return {  
        "schema_id": DOC_INDEX_ARTIFACT_SCHEMA_ID,  
        "count": len(merged),  
        "entries": merged,  
    }  
  
  
def write_doc_index_artifact_1a(artifact: Mapping[str, Any], out_path: str, *, overwrite: bool = True) -> str:  
    if not isinstance(artifact, Mapping):  
        raise ValueError("artifact must be a mapping")  
    if not isinstance(out_path, str) or not out_path.strip():  
        raise ValueError("out_path must be a non-empty string")  
  
    if (not overwrite) and os.path.exists(out_path):  
        raise FileExistsError(out_path)  
  
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)  
    with open(out_path, "w", encoding="utf-8") as f:  
        json.dump(dict(artifact), f, ensure_ascii=False, sort_keys=True, indent=2)  
    return out_path  
  
  
def dev_smoke() -> None:  
    # covered by dev smoke script  
    pass  