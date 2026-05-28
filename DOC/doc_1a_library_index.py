"""  
DOC-1A — Library Index Generator  
  
Generates:  
- DOC/LIBRARY_INDEX.md  
- DOC/library_index.json  
  
Constraints:  
- Must not import project modules (avoid side effects).  
- Only reads files from disk and parses using stdlib (ast, json, pathlib, etc).  
"""  
  
from __future__ import annotations  
  
import ast  
import json  
from dataclasses import dataclass  
from datetime import datetime, timezone  
from pathlib import Path  
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple  
  
  
__all__ = ["generate_library_index"]  
  
  
_EXCLUDE_DIRS = {  
    ".git",  
    ".hg",  
    ".svn",  
    "__pycache__",  
    ".mypy_cache",  
    ".pytest_cache",  
    ".ruff_cache",  
    ".venv",  
    "venv",  
    "env",  
    "node_modules",  
    "dist",  
    "build",  
}  
  
  
@dataclass(frozen=True)  
class ModuleInfo:  
    milestone: str  
    option_id: str  
    path: str  
    exports: List[str]  
    doc_summary: str  
    smoke_tests: List[str]  
  
  
def _read_text_if_exists(path: Path) -> str:  
    try:  
        if path.exists() and path.is_file():  
            return path.read_text(encoding="utf-8", errors="replace")  
    except Exception:  
        return ""  
    return ""  
  
  
def _parse_option_id(milestone: str, filename_stem: str) -> str:  
    """  
    Infer option id from filename pattern like:  
      cli_1a_run_pipeline -> CLI-1A  
      pipe_2e_run_summary -> PIPE-2E  
    If missing, fall back to "<MILESTONE>-??".  
    """  
    # Find first occurrence of _<digits><letter>_ or _<digits><letter> end  
    import re  
  
    m = re.search(r"_([0-9]+)([a-zA-Z])(?:_|$)", filename_stem)  
    if not m:  
        return f"{milestone}-??"  
    num = m.group(1)  
    letter = m.group(2).upper()  
    return f"{milestone}-{num}{letter}"  
  
  
def _safe_literal_eval(node: ast.AST) -> Any:  
    """  
    Evaluate only safe literals (strings, lists/tuples of strings).  
    """  
    if isinstance(node, ast.List):  
        return [_safe_literal_eval(elt) for elt in node.elts]  
    if isinstance(node, ast.Tuple):  
        return [_safe_literal_eval(elt) for elt in node.elts]  
    if isinstance(node, ast.Constant):  
        return node.value  
    raise ValueError("Unsupported literal structure")  
  
  
def _extract___all__(module_path: Path, tree: ast.AST) -> List[str]:  
    exports: List[str] = []  
    for node in ast.walk(tree):  
        if isinstance(node, ast.Assign):  
            for tgt in node.targets:  
                if isinstance(tgt, ast.Name) and tgt.id == "__all__":  
                    try:  
                        value = _safe_literal_eval(node.value)  
                        if isinstance(value, list) and all(isinstance(x, str) for x in value):  
                            exports = list(value)  
                            return exports  
                    except Exception:  
                        return []  
    return exports  
  
  
def _extract_doc_summary(tree: ast.AST) -> str:  
    doc = ast.get_docstring(tree)  
    if not doc:  
        return ""  
    first = doc.strip().splitlines()[0].strip()  
    return first  
  
  
def _iter_python_files(repo_root: Path) -> Sequence[Path]:  
    paths: List[Path] = []  
    for p in repo_root.rglob("*.py"):  
        parts = set(p.parts)  
        if any(x in _EXCLUDE_DIRS for x in parts):  
            continue  
        paths.append(p)  
    return paths  
  
  
def _iter_smoke_tests(repo_root: Path) -> List[Path]:  
    dev_dir = repo_root / "dev"  
    if not dev_dir.exists():  
        return []  
    return sorted(dev_dir.glob("dev_smoke_*.py"))  
  
  
def _smoke_option_id(smoke_path: Path) -> Optional[str]:  
    """  
    dev_smoke_cli_1c.py -> CLI-1C  
    dev_smoke_doc_1a.py -> DOC-1A  
    """  
    import re  
  
    stem = smoke_path.stem  # dev_smoke_cli_1c  
    # allow suffixes like: dev_smoke_doc_1a_library_index.py  
    m = re.match(r"dev_smoke_([a-zA-Z]+)_([0-9]+)([a-zA-Z])(?:_.*)?$", stem)  
    if not m:  
        return None  
    milestone = m.group(1).upper()  
    return f"{milestone}-{m.group(2)}{m.group(3).upper()}"  
  
  
def _extract_import_module_names(py_text: str) -> List[str]:  
    """  
    Parse smoke test imports deterministically (no execution).  
    Returns module names like:  
      - "DOC.doc_1a_library_index"  
      - "PIPE.pipe_1d_step_executor"  
    """  
    try:  
        tree = ast.parse(py_text)  
    except Exception:  
        return []  
  
    mods: List[str] = []  
    for node in ast.walk(tree):  
        if isinstance(node, ast.Import):  
            for alias in node.names:  
                if isinstance(alias.name, str) and alias.name:  
                    mods.append(alias.name)  
        elif isinstance(node, ast.ImportFrom):  
            if isinstance(node.module, str) and node.module:  
                mods.append(node.module)  
  
    # stable de-dupe  
    return sorted(set(mods))  
  
  
def _resolve_module_to_path(repo_root: Path, module_name: str) -> Optional[Path]:  
    """  
    Best-effort: "DOC.doc_1a_library_index" -> <root>/DOC/doc_1a_library_index.py  
    """  
    module_name = (module_name or "").strip()  
    if not module_name:  
        return None  
    rel = Path(*module_name.split("."))  
    cand = (repo_root / rel).with_suffix(".py")  
    if cand.exists() and cand.is_file():  
        return cand  
    return None  
  
  
def _smoke_option_ids_from_imports(repo_root: Path, smoke_path: Path) -> Set[str]:  
    text = _read_text_if_exists(smoke_path)  
    out: Set[str] = set()  
    for mod in _extract_import_module_names(text):  
        p = _resolve_module_to_path(repo_root, mod)  
        if not p:  
            continue  
        rel = p.relative_to(repo_root)  
        milestone = rel.parts[0].upper() if rel.parts else "ROOT"  
        out.add(_parse_option_id(milestone, p.stem))  
    return out  
  
  
def _build_smoke_map(repo_root: Path) -> Dict[str, List[str]]:  
    smokes = _iter_smoke_tests(repo_root)  
    out: Dict[str, List[str]] = {}  
    for s in smokes:  
        rel_smoke = str(s.relative_to(repo_root))  
  
        option_ids: Set[str] = set()  
        # 1) filename heuristic (fast, legacy)  
        oid = _smoke_option_id(s)  
        if oid:  
            option_ids.add(oid)  
        # 2) import-based mapping (correct for suffix smoke tests and multi-module smokes)  
        option_ids |= _smoke_option_ids_from_imports(repo_root, s)  
  
        for oid2 in sorted(option_ids):  
            out.setdefault(oid2, []).append(rel_smoke)  
  
    # stable de-dupe + sort per option id  
    for k in list(out.keys()):  
        out[k] = sorted(set(out[k]))  
    return out  
  
  
def generate_library_index(repo_root: Optional[str] = None) -> Dict[str, str]:  
    """  
    Generate DOC/LIBRARY_INDEX.md and DOC/library_index.json.  
  
    Returns:  
      {"md_path": "...", "json_path": "..."}  
    """  
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parents[1]  
    doc_dir = root / "DOC"  
    doc_dir.mkdir(parents=True, exist_ok=True)  
  
    lib_map = _read_text_if_exists(root / "LIBRARY_MAP.md")  
    naming = _read_text_if_exists(root / "NAMING_CONVENTIONS.md")  
  
    smoke_map = _build_smoke_map(root)  
  
    modules: List[ModuleInfo] = []  
    for p in _iter_python_files(root):  
        rel = p.relative_to(root)  
        if rel.parts and rel.parts[0] in ("dev", "DOC"):  
            # dev scripts are indexed as smoke tests separately; DOC generator itself is included below too.  
            pass  
  
        milestone = rel.parts[0] if rel.parts else "ROOT"  
        milestone = milestone.upper()  
  
        try:  
            text = p.read_text(encoding="utf-8", errors="replace")  
            tree = ast.parse(text)  
        except Exception:  
            # Skip unparseable python files (but still could list them; keep simple)  
            continue  
  
        option_id = _parse_option_id(milestone, p.stem)  
        exports = _extract___all__(p, tree)  
        doc_summary = _extract_doc_summary(tree)  
        smokes = smoke_map.get(option_id, [])  
  
        modules.append(  
            ModuleInfo(  
                milestone=milestone,  
                option_id=option_id,  
                path=str(rel),  
                exports=exports,  
                doc_summary=doc_summary,  
                smoke_tests=smokes,  
            )  
        )  
  
    modules.sort(key=lambda m: (m.milestone, m.option_id, m.path))  
  
    generated_at = datetime.now(timezone.utc).isoformat()  
  
    # -------- JSON output --------  
    json_obj: Dict[str, Any] = {  
        "generated_at": generated_at,  
        "modules": [  
            {  
                "milestone": m.milestone,  
                "option_id": m.option_id,  
                "path": m.path,  
                "exports": m.exports,  
                "smoke_tests": m.smoke_tests,  
            }  
            for m in modules  
        ],  
    }  
  
    json_path = doc_dir / "library_index.json"  
    json_path.write_text(json.dumps(json_obj, indent=2, sort_keys=True), encoding="utf-8")  
  
    # -------- MD output --------  
    md_lines: List[str] = []  
    md_lines.append("# LIBRARY_INDEX")  
    md_lines.append("")  
    md_lines.append(f"Generated at (UTC): `{generated_at}`")  
    md_lines.append("")  
  
    if lib_map.strip():  
        md_lines.append("## Reference: LIBRARY_MAP.md")  
        md_lines.append("")  
        md_lines.append("_Included for convenience; authoritative source remains the file itself._")  
        md_lines.append("")  
        md_lines.append("```text")  
        md_lines.append(lib_map.rstrip())  
        md_lines.append("```")  
        md_lines.append("")  
  
    if naming.strip():  
        md_lines.append("## Reference: NAMING_CONVENTIONS.md")  
        md_lines.append("")  
        md_lines.append("_Included for convenience; authoritative source remains the file itself._")  
        md_lines.append("")  
        md_lines.append("```text")  
        md_lines.append(naming.rstrip())  
        md_lines.append("```")  
        md_lines.append("")  
  
    md_lines.append("## Summary")  
    md_lines.append("")  
    md_lines.append("| Milestone | Option ID | Module path |")  
    md_lines.append("|---|---|---|")  
    for m in modules:  
        md_lines.append(f"| {m.milestone} | {m.option_id} | `{m.path}` |")  
    md_lines.append("")  
  
    md_lines.append("## Modules")  
    md_lines.append("")  
    for m in modules:  
        md_lines.append(f"### `{m.path}`")  
        md_lines.append("")  
        md_lines.append(f"- **Milestone:** `{m.milestone}`")  
        md_lines.append(f"- **Option ID:** `{m.option_id}`")  
        md_lines.append(  
            f"- **Exports (`__all__`):** {', '.join(f'`{x}`' for x in m.exports) if m.exports else '_(none or not parseable)_'}"  
        )  
        md_lines.append(f"- **Doc summary:** {m.doc_summary if m.doc_summary else '_(none)_'}")  
        md_lines.append(  
            f"- **Smoke tests:** {', '.join(f'`{x}`' for x in m.smoke_tests) if m.smoke_tests else '_(none found)_'}"  
        )  
        md_lines.append("")  
  
    md_lines.append("## How to run smoke tests")  
    md_lines.append("")  
    md_lines.append("Standard pattern:")  
    md_lines.append("")  
    md_lines.append("```bash")  
    md_lines.append("python dev/dev_smoke_<milestone>_<option>.py")  
    md_lines.append("# examples:")  
    md_lines.append("python dev/dev_smoke_cli_1a.py")  
    md_lines.append("python dev/dev_smoke_pipe_2e.py")  
    md_lines.append("```")  
    md_lines.append("")  
  
    md_lines.append("## Add new module checklist")  
    md_lines.append("")  
    md_lines.append("- Pick the correct **milestone folder** (e.g., `CLI/`, `PIPE/`, `AUTH/`).")  
    md_lines.append("- Use the **Option ID naming pattern** in the filename (e.g., `cli_1d_...py` => `CLI-1D`).")  
    md_lines.append("- Define `__all__` explicitly for the new module.")  
    md_lines.append("- Add/extend a `dev/dev_smoke_<milestone>_<option>.py` smoke test.")  
    md_lines.append("- Keep modules additive; avoid breaking existing imports/contracts.")  
    md_lines.append(  
        "- If replacing/deprecating, follow your repo’s archive policy (retain old modules or provide compatible shims)."  
    )  
    md_lines.append("")  
  
    md_path = doc_dir / "LIBRARY_INDEX.md"  
    md_path.write_text("\n".join(md_lines), encoding="utf-8")  
  
    return {"md_path": str(md_path), "json_path": str(json_path)}  