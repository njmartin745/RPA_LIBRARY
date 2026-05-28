# REGISTRY/registry_1a_generate.py  
"""  
REGISTRY-1A — Action/Step Registry Export (AI Capability Handshake)  
  
Authoritative registry mapping step actions to:  
- schema definition (required/optional fields)  
- implementation location (module path + option ID)  
- handler function name (if discoverable via static parsing)  
- available smoke tests  
  
Inputs (preferred):  
- DOC/library_index.json  
- SCHEMA/steps_schema.json  
- SCHEMA/steps_examples.json  
  
Outputs:  
- REGISTRY/action_registry.json  
- REGISTRY/action_registry.md  
  
Rules:  
- Do NOT execute project modules (no imports with side effects).  
- Prefer static parsing (ast) and existing generated artifacts.  
- Do not duplicate SCHEMA; reference it.  
- Output must be deterministic.  
"""  
  
from __future__ import annotations  
  
import ast  
import json  
import re  
from datetime import datetime, timezone  
from pathlib import Path  
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple  
  
__all__ = [  
    "generate_action_registry",  
    "main",  
]  
  
OPTION_ID_RE = re.compile(r"\b[A-Z]{2,10}-\d+[A-Z]\b")  
  
  
def _utc_now_iso() -> str:  
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")  
  
  
def _read_text(p: Path) -> str:  
    return p.read_text(encoding="utf-8", errors="replace")  
  
  
def _write_text(p: Path, s: str) -> None:  
    p.parent.mkdir(parents=True, exist_ok=True)  
    p.write_text(s, encoding="utf-8")  
  
  
def _write_json(p: Path, obj: Any) -> None:  
    _write_text(p, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")  
  
  
def _looks_like_repo_root(p: Path) -> bool:  
    if not p.exists() or not p.is_dir():  
        return False  
    if (p / "SCHEMA" / "steps_schema.json").exists():  
        return True  
    if (p / "DOC" / "library_index.json").exists():  
        return True  
    if (p / "REGISTRY").is_dir() and (p / "SCHEMA").is_dir():  
        return True  
    if any((p / d).is_dir() for d in ("ACT", "PIPE", "STATE", "ENTRY")) and (p / "SCHEMA").is_dir():  
        return True  
    return False  
  
  
def _find_repo_root(start: Path) -> Path:  
    s = start.parent if start.is_file() else start  
    for cand in [s, *s.parents]:  
        if _looks_like_repo_root(cand):  
            return cand  
    return s  
  
  
def _as_posix_rel(repo_root: Path, p: Path) -> str:  
    try:  
        return p.resolve().relative_to(repo_root.resolve()).as_posix()  
    except Exception:  
        return p.as_posix()  
  
  
def _safe_load_json(p: Path) -> Optional[dict]:  
    try:  
        obj = json.loads(_read_text(p))  
        return obj if isinstance(obj, dict) else None  
    except Exception:  
        return None  
  
  
def _load_schema(repo_root: Path) -> dict:  
    schema_path = repo_root / "SCHEMA" / "steps_schema.json"  
    if not schema_path.exists():  
        raise FileNotFoundError(f"Missing schema artifact: {schema_path}")  
    schema_obj = _safe_load_json(schema_path)  
    if not schema_obj or not isinstance(schema_obj.get("supported_actions"), list):  
        raise ValueError("Invalid SCHEMA/steps_schema.json shape (missing supported_actions list)")  
    return {"path": schema_path, "obj": schema_obj}  
  
  
def _load_examples(repo_root: Path) -> Dict[str, List[dict]]:  
    ex_path = repo_root / "SCHEMA" / "steps_examples.json"  
    ex_obj = _safe_load_json(ex_path) if ex_path.exists() else None  
    out: Dict[str, List[dict]] = {}  
    if ex_obj and isinstance(ex_obj.get("examples_by_action"), dict):  
        for k, v in ex_obj["examples_by_action"].items():  
            if isinstance(k, str) and isinstance(v, list):  
                out[k] = [x for x in v if isinstance(x, dict)]  
    return out  
  
  
def _load_doc_index(repo_root: Path) -> Optional[dict]:  
    p = repo_root / "DOC" / "library_index.json"  
    return _safe_load_json(p) if p.exists() else None  
  
  
def _build_doc_maps(doc_index: Optional[dict]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:  
    """  
    Returns:  
      - module_path -> option_ids[]  
      - module_path -> smoke_test_paths[]  (tests that validate that module)  
    """  
    module_to_option_ids: Dict[str, List[str]] = {}  
    module_to_smokes: Dict[str, List[str]] = {}  
  
    if not doc_index:  
        return module_to_option_ids, module_to_smokes  
  
    modules = doc_index.get("modules")  
    if isinstance(modules, list):  
        for m in modules:  
            if not isinstance(m, dict):  
                continue  
            path = m.get("path")  
            if not isinstance(path, str):  
                continue  
            opt_ids = m.get("option_ids")  
            if isinstance(opt_ids, list):  
                cleaned = sorted({x for x in opt_ids if isinstance(x, str) and OPTION_ID_RE.search(x)})  
                if cleaned:  
                    module_to_option_ids[path] = cleaned  
  
    smoke_tests = doc_index.get("smoke_tests")  
    if isinstance(smoke_tests, list):  
        for s in smoke_tests:  
            if not isinstance(s, dict):  
                continue  
            spath = s.get("path")  
            validates = s.get("validates")  
            if not isinstance(spath, str) or not isinstance(validates, list):  
                continue  
            for v in validates:  
                if isinstance(v, str):  
                    module_to_smokes.setdefault(v, []).append(spath)  
  
    # determinism  
    for k in list(module_to_smokes.keys()):  
        module_to_smokes[k] = sorted(set(module_to_smokes[k]))  
  
    return module_to_option_ids, module_to_smokes  
  
  
def _infer_option_id_from_module_text(module_text: str) -> Optional[str]:  
    m = OPTION_ID_RE.search(module_text or "")  
    return m.group(0) if m else None  
  
  
def _safe_ast_parse(path: Path) -> Optional[ast.Module]:  
    try:  
        return ast.parse(_read_text(path), filename=str(path))  
    except Exception:  
        return None  
  
  
def _find_handler_name_in_module(tree: ast.Module, action: str) -> Optional[str]:  
    """  
    Static handler discovery (best-effort), deterministic preference order:  
      - act_<action>  
      - action_<action>  
      - do_<action>  
      - handle_<action>  
    """  
    if not action:  
        return None  
  
    candidates = [  
        f"act_{action}",  
        f"action_{action}",  
        f"do_{action}",  
        f"handle_{action}",  
    ]  
  
    found: Set[str] = set()  
    for node in tree.body:  
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):  
            found.add(node.name)  
  
    for c in candidates:  
        if c in found:  
            return c  
    return None  
  
  
def _render_registry_md(reg: dict) -> str:  
    actions = reg.get("actions") or []  
    lines: List[str] = []  
    lines.append("# Action Registry (REGISTRY-1A)")  
    lines.append("")  
    lines.append(f"- Generated: `{reg.get('generated_at')}`")  
    lines.append(f"- Schema version: `{reg.get('schema_version')}`")  
    lines.append(f"- Action count: `{len(actions)}`")  
    lines.append("")  
    lines.append("## Actions")  
    lines.append("")  
  
    for a in actions:  
        if not isinstance(a, dict):  
            continue  
        name = a.get("action")  
        impl = a.get("implemented_by") or {}  
        mod = impl.get("module")  
        opt = impl.get("option_id")  
        handler = a.get("handler")  
        req = a.get("required_fields") or []  
        optf = a.get("optional_fields") or []  
        smokes = a.get("smoke_tests") or []  
  
        lines.append(f"### `{name}`")  
        lines.append("")  
        lines.append(f"- Implemented by: `{mod}`" + (f" (`{opt}`)" if opt else ""))  
        lines.append(f"- Handler: `{handler}`" if handler else "- Handler: _(unknown)_")  
        lines.append(f"- Required fields: {', '.join(f'`{x}`' for x in req) if req else '_(none)_'}")  
        lines.append(f"- Optional fields: {', '.join(f'`{x}`' for x in optf) if optf else '_(none)_'}")  
        if smokes:  
            lines.append(f"- Smoke tests ({len(smokes)}):")  
            for s in smokes:  
                lines.append(f"  - `{s}`")  
        else:  
            lines.append("- Smoke tests: _(none discovered)_")  
        lines.append("")  
  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def generate_action_registry(  
    repo_root: Optional[Path] = None,  
    out_dir: Optional[Path] = None,  
) -> dict:  
    repo_root = repo_root or _find_repo_root(Path(__file__).resolve())  
    if not _looks_like_repo_root(repo_root):  
        repo_root = _find_repo_root(repo_root)  
  
    out_dir = out_dir or (repo_root / "REGISTRY")  
    out_dir.mkdir(parents=True, exist_ok=True)  
  
    schema = _load_schema(repo_root)  
    schema_obj = schema["obj"]  
    examples_by_action = _load_examples(repo_root)  
    doc_index = _load_doc_index(repo_root)  
    module_to_option_ids, module_to_smokes = _build_doc_maps(doc_index)  
  
    schema_version = schema_obj.get("schema_version")  
  
    actions_out: List[dict] = []  
  
    supported_actions = schema_obj.get("supported_actions") or []  
    # Deterministic ordering by action name  
    supported_actions_sorted = sorted(  
        [a for a in supported_actions if isinstance(a, dict) and isinstance(a.get("action"), str)],  
        key=lambda x: x["action"],  
    )  
  
    for entry in supported_actions_sorted:  
        action = entry["action"]  
  
        implemented_by = entry.get("implemented_by") if isinstance(entry.get("implemented_by"), dict) else {}  
        module_path = implemented_by.get("module") if isinstance(implemented_by.get("module"), str) else None  
        option_id = implemented_by.get("option_id") if isinstance(implemented_by.get("option_id"), str) else None  
  
        # Backfill option_id from DOC index if needed  
        if module_path and not option_id:  
            opt_ids = module_to_option_ids.get(module_path) or []  
            option_id = opt_ids[0] if opt_ids else None  
  
        handler: Optional[str] = None  
        if module_path:  
            mod_fs_path = (repo_root / module_path)  
            if mod_fs_path.exists() and mod_fs_path.is_file() and mod_fs_path.suffix == ".py":  
                tree = _safe_ast_parse(mod_fs_path)  
                if tree is not None:  
                    handler = _find_handler_name_in_module(tree, action)  
                # last-ditch: infer option id from text if still missing  
                if not option_id:  
                    option_id = _infer_option_id_from_module_text(_read_text(mod_fs_path))  
  
        required_fields = entry.get("required_fields") if isinstance(entry.get("required_fields"), list) else []  
        optional_fields = entry.get("optional_fields") if isinstance(entry.get("optional_fields"), list) else []  
        required_fields = sorted([x for x in required_fields if isinstance(x, str)])  
        optional_fields = sorted([x for x in optional_fields if isinstance(x, str)])  
  
        # Examples: prefer steps_examples.json, then schema-embedded examples  
        examples = examples_by_action.get(action)  
        if examples is None:  
            examples = entry.get("examples") if isinstance(entry.get("examples"), list) else []  
            examples = [x for x in examples if isinstance(x, dict)]  
        else:  
            examples = [x for x in examples if isinstance(x, dict)]  
  
        # Smoke tests from DOC index mapping  
        smoke_tests: List[str] = []  
        if module_path:  
            smoke_tests = module_to_smokes.get(module_path) or []  
        smoke_tests = sorted(set([s for s in smoke_tests if isinstance(s, str)]))  
  
        actions_out.append(  
            {  
                "action": action,  
                "implemented_by": {"module": module_path, "option_id": option_id},  
                "handler": handler,  
                "required_fields": required_fields,  
                "optional_fields": optional_fields,  
                "examples": examples,  
                "smoke_tests": smoke_tests,  
            }  
        )  
  
    reg = {  
        "generated_at": _utc_now_iso(),  
        "schema_version": schema_version,  
        "schema_source": _as_posix_rel(repo_root, Path(schema["path"])),  
        "actions": actions_out,  
    }  
  
    json_path = out_dir / "action_registry.json"  
    md_path = out_dir / "action_registry.md"  
    _write_json(json_path, reg)  
    _write_text(md_path, _render_registry_md(reg))  
    return reg  
  
  
def main(argv: Optional[List[str]] = None) -> int:  
    _ = argv  
    repo_root = _find_repo_root(Path(__file__).resolve())  
    reg = generate_action_registry(repo_root=repo_root)  
    out_dir = repo_root / "REGISTRY"  
    print(f"[REGISTRY-1A] Wrote: {(out_dir / 'action_registry.json').as_posix()}")  
    print(f"[REGISTRY-1A] Wrote: {(out_dir / 'action_registry.md').as_posix()}")  
    print(f"[REGISTRY-1A] Actions: {len(reg.get('actions', []))}")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  