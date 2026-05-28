"""  
BUILD-2G: Directory/tree-level workflow grammar gating.  
  
Single responsibility:  
- Find workflow JSON files under a directory (deterministic order).  
- Batch assert/sanitize them using BUILD-2F.  
  
This is additive and does not modify existing builders.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from pathlib import Path  
from typing import Iterable, List, Optional, Sequence, Tuple  
  
from BUILD.build_2d_step_grammar_gate import ALLOWED_ACTIONS, GrammarViolation  
from BUILD.build_2f_workflow_file_grammar_gate import (  
    WorkflowFileGateResult,  
    gate_workflow_file_assert,  
    gate_workflow_file_sanitize,  
)  
  
__all__ = [  
    "WorkflowTreeGateResult",  
    "list_workflow_json_files",  
    "gate_workflow_tree_assert",  
    "gate_workflow_tree_sanitize",  
]  
  
  
@dataclass(frozen=True)  
class WorkflowTreeGateResult:  
    root_dir: str  
    file_results: Tuple[WorkflowFileGateResult, ...]  
  
    @property  
    def total_files(self) -> int:  
        return len(self.file_results)  
  
    @property  
    def total_violations(self) -> int:  
        return sum(len(r.violations) for r in self.file_results)  
  
  
def list_workflow_json_files(  
    root_dir: str | Path,  
    *,  
    recursive: bool = True,  
) -> List[Path]:  
    """  
    Deterministically lists *.json files under root_dir.  
    """  
    root = Path(root_dir)  
    if not root.exists():  
        return []  
    if root.is_file():  
        return [root] if root.suffix.lower() == ".json" else []  
  
    pattern = "**/*.json" if recursive else "*.json"  
    files = [p for p in root.glob(pattern) if p.is_file()]  
    return sorted(files, key=lambda p: str(p).lower())  
  
  
def gate_workflow_tree_assert(  
    root_dir: str | Path,  
    *,  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
    recursive: bool = True,  
) -> WorkflowTreeGateResult:  
    """  
    Asserts every workflow JSON file under root_dir has only supported actions.  
    Raises ValueError on first failure (from gate_workflow_file_assert).  
    """  
    files = list_workflow_json_files(root_dir, recursive=recursive)  
    results: List[WorkflowFileGateResult] = []  
    for p in files:  
        results.append(gate_workflow_file_assert(p, allowed_actions=allowed_actions))  
    return WorkflowTreeGateResult(root_dir=str(Path(root_dir)), file_results=tuple(results))  
  
  
def _map_output_path(src: Path, src_root: Path, dst_root: Path) -> Path:  
    rel = src.relative_to(src_root)  
    return dst_root / rel  
  
  
def gate_workflow_tree_sanitize(  
    root_dir: str | Path,  
    *,  
    allowed_actions: Sequence[str] = ALLOWED_ACTIONS,  
    recursive: bool = True,  
    in_place: bool = True,  
    output_dir: Optional[str | Path] = None,  
    drop_empty_repeat: bool = True,  
    indent: int = 2,  
    sort_keys: bool = True,  
) -> WorkflowTreeGateResult:  
    """  
    Sanitizes every workflow JSON file under root_dir.  
  
    Writing behavior:  
    - If output_dir is set, writes sanitized copies to output_dir preserving relative paths,  
      and does NOT overwrite originals (in_place is ignored).  
    - Else if in_place=True, overwrites files in root_dir.  
    - Else, performs sanitize in-memory only (no writes).  
  
    Returns per-file results (including violations).  
    """  
    src_root = Path(root_dir)  
    dst_root = Path(output_dir) if output_dir is not None else None  
  
    files = list_workflow_json_files(src_root, recursive=recursive)  
    results: List[WorkflowFileGateResult] = []  
  
    for src in files:  
        out_path = None  
        if dst_root is not None:  
            out_path = _map_output_path(src, src_root=src_root, dst_root=dst_root)  
            out_path.parent.mkdir(parents=True, exist_ok=True)  
  
        res = gate_workflow_file_sanitize(  
            src,  
            allowed_actions=allowed_actions,  
            in_place=(False if dst_root is not None else in_place),  
            output_path=out_path,  
            drop_empty_repeat=drop_empty_repeat,  
            indent=indent,  
            sort_keys=sort_keys,  
        )  
        results.append(res)  
  
    return WorkflowTreeGateResult(root_dir=str(src_root), file_results=tuple(results))  