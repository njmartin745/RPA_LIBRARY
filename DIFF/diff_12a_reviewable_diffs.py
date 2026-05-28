"""  
DIFF-12A: Reviewable Diffs (Milestone 12.2.2)  
  
Single responsibility:  
- Provide deterministic, reviewable diffs for workflow/selector changes.  
- Canonicalize JSON (stable key ordering) to avoid noisy diffs from formatting/key order.  
  
This module is intentionally additive: it does not enforce policy automatically.  
CI/BUILD governance can call these helpers to require diff artifacts and/or  
block changes without reviewable diffs.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import List, Literal, Optional, Tuple  
import difflib  
import json  
  
  
__all__ = [  
    "DiffKind",  
    "DiffResult",  
    "read_text_file",  
    "normalize_newlines",  
    "canonicalize_text",  
    "unified_diff_text",  
    "diff_texts_reviewable",  
    "diff_files_reviewable",  
    "check_reviewable_diff_required",  
    "write_text_file",  
]  
  
  
DiffKind = Literal["workflow", "selectors", "json", "text"]  
  
  
@dataclass(frozen=True, slots=True)  
class DiffResult:  
    """  
    A deterministic diff output plus metadata useful for governance.  
    """  
    changed: bool  
    diff: str  
    before_canonical: str  
    after_canonical: str  
  
  
def read_text_file(path: str) -> str:  
    with open(path, "r", encoding="utf-8") as f:  
        return f.read()  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def normalize_newlines(text: str) -> str:  
    return text.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def _canonicalize_json(text: str) -> str:  
    """  
    Canonical JSON formatting:  
    - parse JSON  
    - dump with sort_keys=True + indent=2  
    - ensure trailing newline  
    """  
    obj = json.loads(text)  
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"  
  
  
def canonicalize_text(text: str, *, kind: DiffKind) -> str:  
    """  
    Deterministic canonicalization to produce reviewable diffs.  
    - workflow/selectors/json => canonical JSON (sorted keys)  
    - text => newline normalization only  
    """  
    t = normalize_newlines(text)  
    if kind in ("workflow", "selectors", "json"):  
        # Fail closed into text canonicalization if JSON parse fails is NOT desired  
        # for governance; but for robustness we fall back to text while still  
        # producing a diff. CI can separately enforce JSON validity.  
        try:  
            return _canonicalize_json(t)  
        except Exception:  
            # fallback  
            return t if t.endswith("\n") else (t + "\n")  
    return t if t.endswith("\n") else (t + "\n")  
  
  
def unified_diff_text(  
    before: str,  
    after: str,  
    *,  
    fromfile: str = "before",  
    tofile: str = "after",  
    context_lines: int = 3,  
) -> str:  
    """  
    Deterministic unified diff (LF newlines).  
    """  
    b = normalize_newlines(before).splitlines(keepends=True)  
    a = normalize_newlines(after).splitlines(keepends=True)  
    diff_lines = difflib.unified_diff(  
        b,  
        a,  
        fromfile=fromfile,  
        tofile=tofile,  
        n=context_lines,  
        lineterm="\n",  
    )  
    out = "".join(diff_lines)  
    return out if out.endswith("\n") or out == "" else (out + "\n")  
  
  
def diff_texts_reviewable(  
    before_text: str,  
    after_text: str,  
    *,  
    kind: DiffKind,  
    fromfile: str = "before",  
    tofile: str = "after",  
) -> DiffResult:  
    """  
    Create a reviewable diff from raw texts (canonicalizes first).  
    """  
    before_c = canonicalize_text(before_text, kind=kind)  
    after_c = canonicalize_text(after_text, kind=kind)  
    changed = before_c != after_c  
    diff = unified_diff_text(before_c, after_c, fromfile=fromfile, tofile=tofile) if changed else ""  
    return DiffResult(changed=changed, diff=diff, before_canonical=before_c, after_canonical=after_c)  
  
  
def diff_files_reviewable(  
    before_path: str,  
    after_path: str,  
    *,  
    kind: DiffKind,  
    fromfile: Optional[str] = None,  
    tofile: Optional[str] = None,  
) -> DiffResult:  
    """  
    Create a reviewable diff from two file paths.  
    """  
    before_text = read_text_file(before_path)  
    after_text = read_text_file(after_path)  
    return diff_texts_reviewable(  
        before_text,  
        after_text,  
        kind=kind,  
        fromfile=fromfile or before_path,  
        tofile=tofile or after_path,  
    )  
  
  
def check_reviewable_diff_required(result: DiffResult) -> List[str]:  
    """  
    Governance helper: If something changed, ensure diff is present and looks like a unified diff.  
  
    Returns a deterministic list of issues (empty list means "passes").  
    """  
    issues: List[str] = []  
  
    if result.changed and result.diff.strip() == "":  
        issues.append("Change detected but diff output is empty")  
  
    if result.changed:  
        # Basic unified diff signature checks  
        if not (result.diff.startswith("--- ") and "\n+++ " in result.diff):  
            issues.append("Diff does not appear to be a unified diff (missing ---/+++ headers)")  
  
    return issues  