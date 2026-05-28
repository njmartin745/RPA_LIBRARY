"""  
DOC-1G — Doc Index Entry Contract (Validator)  
  
Single responsibility:  
- Validate the dict shape expected by DOC.doc_1f_doc_index_aggregator.collect_doc_index_entries_1a().  
  
This module is pure + deterministic and safe to import (no side effects).  
"""  
  
from __future__ import annotations  
  
from typing import Any, Dict, Iterable, List, Mapping, Sequence  
  
__all__ = [  
    "DOC_INDEX_ENTRY_KIND_1A",  
    "DOC_INDEX_LAYERS_1A",  
    "validate_doc_index_entry_1a",  
    "validate_doc_index_entries_1a",  
    "dev_smoke",  
]  
  
DOC_INDEX_ENTRY_KIND_1A = "doc_index_entry"  
  
# Keep in sync with the architecture layer list (used as a sanity check).  
DOC_INDEX_LAYERS_1A = (  
    "ENTRY",  
    "INPUT",  
    "STATE",  
    "LOOP",  
    "ACT",  
    "NAV",  
    "VAL",  
    "OUT",  
    "VAR",  
    "LOG",  
    "PIPE",  
    "AUTH",  
    "DOC",  
    "REGISTRY",  
    "SELECTOR",  
    "AGENT",  
    "WORKFLOW",  
    "RUN",  
    "REASON",  
    "HEAL",  
    "SNAP",  
    "REPLAY",  
    "REPORT",  
    "GUARD",  
    "DIFF",  
    "HISTORY",  
    "DOCTOR",  
    "CLI",  
    "BUILD",  
)  
  
  
def _is_nonempty_str(x: Any) -> bool:  
    return isinstance(x, str) and bool(x.strip())  
  
  
def validate_doc_index_entry_1a(entry: Any) -> List[str]:  
    """  
    Validate a single doc-index entry.  
  
    Expected minimal shape (based on known-good entry output):  
      {  
        "kind": "doc_index_entry",  
        "layer": "CLI",  
        "module": "CLI.some_module",  
        "name": "...",  
        "summary": "...",  
        "usage": {  
          "python_module": "CLI.some_module",  
          "callable": "main",  
          "examples": ["python -c ...", ...]  
        }  
      }  
  
    Returns:  
      List of human-readable error strings. Empty list => valid.  
    """  
    errors: List[str] = []  
  
    if not isinstance(entry, Mapping):  
        return ["entry must be a mapping/dict"]  
  
    kind = entry.get("kind")  
    if kind != DOC_INDEX_ENTRY_KIND_1A:  
        errors.append(f"entry.kind must be '{DOC_INDEX_ENTRY_KIND_1A}'")  
  
    layer = entry.get("layer")  
    if not _is_nonempty_str(layer):  
        errors.append("entry.layer must be a non-empty string")  
    elif str(layer).upper() not in DOC_INDEX_LAYERS_1A:  
        errors.append(f"entry.layer must be one of {list(DOC_INDEX_LAYERS_1A)}")  
  
    module = entry.get("module")  
    if not _is_nonempty_str(module):  
        errors.append("entry.module must be a non-empty string")  
    elif " " in str(module):  
        errors.append("entry.module must not contain spaces")  
  
    name = entry.get("name")  
    if not _is_nonempty_str(name):  
        errors.append("entry.name must be a non-empty string")  
  
    summary = entry.get("summary")  
    if not _is_nonempty_str(summary):  
        errors.append("entry.summary must be a non-empty string")  
  
    usage = entry.get("usage")  
    if not isinstance(usage, Mapping):  
        errors.append("entry.usage must be a mapping/dict")  
        return errors  
  
    py_mod = usage.get("python_module")  
    if not _is_nonempty_str(py_mod):  
        errors.append("usage.python_module must be a non-empty string")  
  
    callable_name = usage.get("callable")  
    if not _is_nonempty_str(callable_name):  
        errors.append("usage.callable must be a non-empty string")  
  
    examples = usage.get("examples")  
    if examples is None:  
        errors.append("usage.examples must be present (can be empty list)")  
    elif not isinstance(examples, Sequence) or isinstance(examples, (str, bytes)):  
        errors.append("usage.examples must be a list/sequence of strings")  
    else:  
        for i, ex in enumerate(examples):  
            if not _is_nonempty_str(ex):  
                errors.append(f"usage.examples[{i}] must be a non-empty string")  
  
    return errors  
  
  
def validate_doc_index_entries_1a(entries: Iterable[Any]) -> Dict[int, List[str]]:  
    """  
    Validate many entries. Returns index->errors for any invalid entries.  
    """  
    out: Dict[int, List[str]] = {}  
    for i, e in enumerate(entries):  
        errs = validate_doc_index_entry_1a(e)  
        if errs:  
            out[i] = errs  
    return out  
  
  
def dev_smoke() -> None:  
    ok = {  
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
    assert validate_doc_index_entry_1a(ok) == []  
  
    bad = {"kind": "nope"}  
    errs = validate_doc_index_entry_1a(bad)  
    assert isinstance(errs, list) and len(errs) >= 1  