# AGENT/agent_1a_context_pack.py  
"""  
AGENT-1A — Agent Context Pack Exporter (single pasteable bundle)  
  
Reads existing generated artifacts (DO NOT re-derive) and produces:  
- DOC/AGENT_PACKET.md   (human + LLM paste bundle)  
- DOC/agent_packet.json (machine bundle; includes paths, exports, actions)  
  
Inputs (required):  
- DOC/library_index.json  
- SCHEMA/steps_schema.json (or other SCHEMA-1A schema output filenames)  
  
Inputs (optional):  
- SCHEMA/steps_examples.json  
- REGISTRY/action_registry.json  
- data/selectors.json  
  
Rules:  
- No side-effect imports of project modules.  
- Prefer pure helpers; no printing/logging here.  
- Deterministic output ordering.  
"""  
  
from __future__ import annotations  
  
import json  
from datetime import datetime, timezone  
from pathlib import Path  
from typing import Any, Dict, List, Optional, Sequence, Tuple  
  
__all__ = [  
    "generate_agent_context_pack",  
    "main",  
]  
  
  
def _utc_now_iso() -> str:  
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")  
  
  
def _read_text(p: Path) -> str:  
    return p.read_text(encoding="utf-8", errors="replace")  
  
  
def _write_text(p: Path, s: str) -> None:  
    p.parent.mkdir(parents=True, exist_ok=True)  
    p.write_text(s, encoding="utf-8")  
  
  
def _write_json(p: Path, obj: Any) -> None:  
    _write_text(p, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")  
  
  
def _safe_load_json(path: Path) -> Optional[Any]:  
    try:  
        return json.loads(_read_text(path))  
    except Exception:  
        return None  
  
  
def _looks_like_repo_root(p: Path) -> bool:  
    if not p.exists() or not p.is_dir():  
        return False  
    if (p / "SCHEMA" / "steps_schema.json").exists():  
        return True  
    if (p / "DOC" / "library_index.json").exists():  
        return True  
    if (p / "ACT").is_dir() and (p / "PIPE").is_dir() and (p / "SCHEMA").is_dir():  
        return True  
    return False  
  
  
def _find_repo_root(start: Path) -> Path:  
    s = start.parent if start.is_file() else start  
    for cand in [s, *s.parents]:  
        if _looks_like_repo_root(cand):  
            return cand  
    return s  
  
  
def _require_file(path: Path, how_to_fix: str) -> Path:  
    if not path.exists():  
        raise FileNotFoundError(f"Missing required artifact: {path}\nGenerate it first:\n  {how_to_fix}")  
    return path  
  
  
def _find_schema_path(repo_root: Path) -> Path:  
    candidates = [  
        repo_root / "SCHEMA" / "steps_schema.json",  
        repo_root / "SCHEMA" / "schema_1a_steps.json",  
        repo_root / "SCHEMA" / "steps_schema_1a.json",  
    ]  
    for p in candidates:  
        if p.exists():  
            return p  
    raise FileNotFoundError(  
        "Missing required SCHEMA artifact.\n"  
        "Expected one of:\n  - SCHEMA/steps_schema.json\n  - SCHEMA/schema_1a_steps.json\n"  
        "Generate it first:\n  python SCHEMA/schema_1a_generate.py\n"  
        "or run:\n  python dev/dev_smoke_schema_1a.py"  
    )  
  
  
def _discover_smoke_tests(repo_root: Path) -> List[str]:  
    # Deterministic listing of existing smoke tests (filesystem scan is safe and side-effect free)  
    tests: List[str] = []  
    dev_dir = repo_root / "dev"  
    if dev_dir.exists():  
        tests.extend([p.as_posix() for p in sorted(dev_dir.glob("dev_smoke_*.py")) if p.is_file()])  
    tests.extend([p.as_posix() for p in sorted(repo_root.glob("dev_smoke_*.py")) if p.is_file()])  
    # convert to repo-relative-ish strings where possible  
    def relish(s: str) -> str:  
        try:  
            return Path(s).resolve().relative_to(repo_root.resolve()).as_posix()  
        except Exception:  
            return s  
    return sorted({relish(s) for s in tests})  
  
  
def _selector_summary(repo_root: Path) -> Dict[str, Any]:  
    sel_path = repo_root / "data" / "selectors.json"  
    if not sel_path.exists():  
        return {"present": False, "path": str(sel_path)}  
  
    obj = _safe_load_json(sel_path)  
    if not isinstance(obj, dict):  
        return {"present": True, "path": str(sel_path), "error": "selectors.json is not a JSON object"}  
  
    groups = sorted([k for k in obj.keys() if isinstance(k, str)])  
    # count leaf entries (dicts that contain css/xpath/text)  
    leaf_count = 0  
    dotted_ids: List[str] = []  
  
    def walk(node: Any, prefix: str) -> None:  
        nonlocal leaf_count  
        if isinstance(node, dict):  
            # heuristic leaf  
            if any(k in node for k in ("css", "xpath", "text")) and all(  
                isinstance(node.get(k), (str, type(None))) for k in ("css", "xpath", "text")  
            ):  
                leaf_count += 1  
                dotted_ids.append(prefix)  
                return  
            for k, v in node.items():  
                if isinstance(k, str):  
                    walk(v, f"{prefix}.{k}" if prefix else k)  
  
    walk(obj, "")  
    dotted_ids = sorted(dotted_ids)  
  
    return {  
        "present": True,  
        "path": str(sel_path),  
        "group_count": len(groups),  
        "groups": groups,  
        "leaf_count": leaf_count,  
        "selector_ids_sample": dotted_ids[:50],  
    }  
  
  
def _format_agent_packet_md(packet: Dict[str, Any]) -> str:  
    repo = packet.get("repo_overview") or {}  
    paths = packet.get("paths") or {}  
    actions = packet.get("actions") or []  
    modules = packet.get("modules") or []  
    smoke_map = packet.get("smoke_test_mapping") or []  
    selector = packet.get("selector_summary") or {}  
    canonical = packet.get("canonical_e2e_run") or {}
    
  
    lines: List[str] = []  
    lines.append("# AGENT_PACKET (AGENT-1A)")  
    lines.append("")  
    lines.append(f"- Generated: `{packet.get('generated_at')}`")  
    lines.append(f"- Schema version: `{packet.get('schema_version')}`")  
    lines.append("")  
    lines.append("## Repo overview")  
    lines.append("")  
    lines.append(f"- Top-level packages: {', '.join(f'`{p}`' for p in (repo.get('top_level_packages') or []))}")  
    lines.append(f"- Module count: `{repo.get('module_count')}`")  
    lines.append(f"- Smoke test count (from DOC index): `{repo.get('smoke_test_count')}`")  
    lines.append("")  
    lines.append("## Key artifacts")  
    lines.append("")  
    for k in ("library_index_json", "steps_schema_json", "steps_examples_json", "action_registry_json"):  
        v = paths.get(k)  
        if v:  
            lines.append(f"- {k}: `{v}`")  
    lines.append("")  
    lines.append("## How to run (common commands)")  
    lines.append("")  
    # Keep these conservative and grounded in existing files  
    lines.append("- Smoke tests (recommended):")  
    for t in (packet.get("smoke_tests_discovered") or [])[:20]:  
        lines.append(f"  - `python {t}`")  
    if (packet.get("smoke_tests_discovered") or []) and len(packet["smoke_tests_discovered"]) > 20:  
        lines.append("  - _(more available; see dev/)_")  
    lines.append("")  
    lines.append("- Regenerate artifacts:")  
    lines.append("  - `python SCHEMA/schema_1a_generate.py`")  
    lines.append("  - `python DOC/doc_1a_library_index.py`")  
    if paths.get("action_registry_json"):  
        lines.append("  - `python REGISTRY/registry_1a_generate.py`")  
    lines.append("")  
    # Known helpers if present  
    if packet.get("known_entrypoints"):  
        lines.append("- Entry points:")  
        for e in packet["known_entrypoints"]:  
            lines.append(f"  - `{e}`")  
        lines.append("")  
  
    lines.append("## Action inventory (from SCHEMA)")  
    lines.append("")  
    lines.append(f"- Action count: `{len(actions)}`")  
    for a in actions[:80]:  
        name = a.get("action")  
        req = a.get("required_fields") or []  
        impl = a.get("implemented_by") or {}  
        mod = impl.get("module")  
        lines.append(f"- `{name}`" + (f" — `{mod}`" if mod else ""))  
        if req:  
            lines.append(f"  - required: {', '.join(f'`{x}`' for x in req)}")  
    if len(actions) > 80:  
        lines.append("- _(truncated; see DOC/agent_packet.json for full list)_")  
    lines.append("")  
  
    lines.append("## Public module exports (from DOC index)")  
    lines.append("")  
    # Group by package  
    by_pkg: Dict[str, List[dict]] = {}  
    for m in modules:  
        if isinstance(m, dict):  
            by_pkg.setdefault(m.get("package") or "", []).append(m)  
    for pkg in sorted([p for p in by_pkg.keys() if p]):  
        lines.append(f"### {pkg}")  
        for m in sorted(by_pkg[pkg], key=lambda x: x.get("path", "")):  
            exports = m.get("exports") or []  
            exp = ", ".join(f"`{e}`" for e in exports) if exports else "_(no `__all__`)_"  
            lines.append(f"- `{m.get('path')}` — exports: {exp}")  
        lines.append("")  
    lines.append("")  
  
    lines.append("## Smoke-test mapping (from DOC index)")  
    lines.append("")  
    if smoke_map:  
        for sm in smoke_map:  
            sp = sm.get("path")  
            vals = sm.get("validates") or []  
            lines.append(f"- `{sp}`")  
            for v in vals:  
                lines.append(f"  - validates: `{v}`")  
    else:  
        lines.append("_(none found in DOC/library_index.json)_")  
    lines.append("")  
  
    if canonical:
        lines.append("## Canonical End-to-End Run")
        lines.append("")
        lines.append(f"- Name: **{canonical.get('name')}**")
        lines.append(f"- Entry point: `{canonical.get('entrypoint')}`")
        lines.append(f"- Smoke test: `{canonical.get('smoke_test')}`")
        lines.append("")
        lines.append(canonical.get("description", ""))
        lines.append("")
        lines.append("### Readiness Criteria")
        for c in canonical.get("readiness_criteria", []):
            lines.append(f"- {c}")
        lines.append("")
            
    lines.append("## Selector inventory summary")  
    lines.append("")  
    if selector.get("present"):  
        lines.append(f"- selectors.json: `{selector.get('path')}`")  
        if selector.get("error"):  
            lines.append(f"- error: `{selector.get('error')}`")  
        else:  
            lines.append(f"- groups: `{selector.get('group_count')}`")  
            lines.append(f"- selector leaf entries: `{selector.get('leaf_count')}`")  
            groups = selector.get("groups") or []  
            if groups:  
                lines.append(f"- group names: {', '.join(f'`{g}`' for g in groups)}")  
    else:  
        lines.append(f"- selectors.json not present at `{selector.get('path')}`")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def generate_agent_context_pack(  
    repo_root: Optional[Path] = None,  
    *,  
    out_md_path: Optional[Path] = None,  
    out_json_path: Optional[Path] = None,  
) -> Dict[str, Any]:  
    repo_root = repo_root or _find_repo_root(Path(__file__).resolve())  
  
    # Required artifacts  
    lib_index_path = _require_file(  
        repo_root / "DOC" / "library_index.json",  
        "python DOC/doc_1a_library_index.py\nor\n  python dev/dev_smoke_doc_1a_library_index.py",  
    )  
    schema_path = _find_schema_path(repo_root)  
  
    lib_index = _safe_load_json(lib_index_path)  
    if not isinstance(lib_index, dict):  
        raise ValueError(f"Invalid JSON object: {lib_index_path}")  
  
    schema_obj = _safe_load_json(schema_path)  
    if not isinstance(schema_obj, dict) or not isinstance(schema_obj.get("supported_actions"), list):  
        raise ValueError(f"Invalid schema JSON (missing supported_actions): {schema_path}")  
  
    examples_path = repo_root / "SCHEMA" / "steps_examples.json"  
    examples_obj = _safe_load_json(examples_path) if examples_path.exists() else None  
  
    registry_path = repo_root / "REGISTRY" / "action_registry.json"  
    registry_obj = _safe_load_json(registry_path) if registry_path.exists() else None  
  
    modules = lib_index.get("modules") if isinstance(lib_index.get("modules"), list) else []

    # Smoke tests are indexed per-module in DOC/library_index.json (canonical)
    # Derive a deterministic, de-duplicated view here (do NOT re-derive tests)
    smoke_tests_from_modules: List[str] = sorted({
        t
        for m in modules
        if isinstance(m, dict)
        for t in (m.get("smoke_tests") or [])
        if isinstance(t, str)
    })

    smoke_test_mapping = [
        {
            "path": t,
            "validates": [
                m.get("path")
                for m in modules
                if isinstance(m, dict) and t in (m.get("smoke_tests") or [])
            ],
        }
        for t in smoke_tests_from_modules
    ]

    # Actions from SCHEMA (canonical)  
    supported = schema_obj.get("supported_actions") or []  
    actions_out: List[dict] = []  
    for e in sorted(  
        [x for x in supported if isinstance(x, dict) and isinstance(x.get("action"), str)],  
        key=lambda x: x["action"],  
    ):  
        actions_out.append(  
            {  
                "action": e.get("action"),  
                "description": e.get("description"),  
                "implemented_by": e.get("implemented_by") if isinstance(e.get("implemented_by"), dict) else None,  
                "required_fields": sorted([x for x in (e.get("required_fields") or []) if isinstance(x, str)]),  
                "optional_fields": sorted([x for x in (e.get("optional_fields") or []) if isinstance(x, str)]),  
                "field_types": e.get("field_types") if isinstance(e.get("field_types"), dict) else None,  
                "allowed_values": e.get("allowed_values") if isinstance(e.get("allowed_values"), dict) else None,  
            }  
        )  
  
    # Known entry points (best-effort, filesystem-based, deterministic)  
    known_entrypoints: List[str] = []  
    if (repo_root / "CLI" / "cli_1a_run_pipeline.py").exists():  
        known_entrypoints.append("python CLI/cli_1a_run_pipeline.py --help")  
    if (repo_root / "LINT" / "lint_steps.py").exists():  
        known_entrypoints.append("python LINT/lint_steps.py path/to/steps.json")  

    # Canonical End-to-End (E2E) Run
    # This is a derived declaration based on existing repo artifacts.
    # No configuration or side effects; purely descriptive.
    canonical_e2e_run: Optional[Dict[str, Any]] = None

    prod_smoke = repo_root / "dev" / "dev_smoke_12_6_1_prod_smoke_pipeline.py"
    pipe_runner = repo_root / "PIPE" / "pipe_1e_runner.py"

    if prod_smoke.exists() and pipe_runner.exists():
        canonical_e2e_run = {
            "name": "Production Smoke Pipeline",
            "kind": "prod_smoke",
            "entrypoint": "PIPE/pipe_1e_runner.py",
            "smoke_test": "dev/dev_smoke_12_6_1_prod_smoke_pipeline.py",
            "description": (
                "Canonical end-to-end run validating workflow execution, "
                "artifact generation, and production readiness gates."
            ),
            "readiness_criteria": [
                "workflow grammar gates pass",
                "pipeline execution completes",
                "release manifest is generated",
                "bundle fingerprint is generated",
                "DOCTOR gates pass",
                "GUARD gates pass",
            ],
        }

    packet = {  
        "generated_at": _utc_now_iso(),  
        "schema_version": schema_obj.get("schema_version"),  
        "repo_overview": {  
            "top_level_packages": lib_index.get("top_level_packages") or [],  
            "module_count": len(modules),  
            "smoke_test_count": len(smoke_tests_from_modules),
        },  
        "paths": {  
            "library_index_json": "DOC/library_index.json",  
            "steps_schema_json": str(schema_path.relative_to(repo_root)).replace("\\", "/")  
            if schema_path.is_absolute()  
            else str(schema_path),  
            "steps_examples_json": "SCHEMA/steps_examples.json" if examples_path.exists() else None,  
            "action_registry_json": "REGISTRY/action_registry.json" if registry_path.exists() else None,  
        },  
        "modules": [  
            {  
                "package": m.get("package"),  
                "path": m.get("path"),  
                "dotted": m.get("dotted"),  
                "exports": m.get("exports") if isinstance(m.get("exports"), list) else [],  
                "doc": m.get("doc"),  
            }  
            for m in modules  
            if isinstance(m, dict)  
        ],  
        "smoke_test_mapping": smoke_test_mapping,
        "smoke_tests_discovered": _discover_smoke_tests(repo_root),  
        "actions": actions_out,  
        "examples": examples_obj if isinstance(examples_obj, dict) else None,  
        "registry": registry_obj if isinstance(registry_obj, dict) else None,  
        "selector_summary": _selector_summary(repo_root),  
        "known_entrypoints": known_entrypoints,
        "canonical_e2e_run": canonical_e2e_run, 
    }  
  
    # Write outputs  
    out_md_path = out_md_path or (repo_root / "DOC" / "AGENT_PACKET.md")  
    out_json_path = out_json_path or (repo_root / "DOC" / "agent_packet.json")  
  
    _write_json(out_json_path, packet)  
    _write_text(out_md_path, _format_agent_packet_md(packet))  
    return packet  
  
  
def main(argv: Optional[List[str]] = None) -> int:  
    _ = argv  
    repo_root = _find_repo_root(Path(__file__).resolve())  
    generate_agent_context_pack(repo_root=repo_root)  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  