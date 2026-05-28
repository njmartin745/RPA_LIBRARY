# WORKFLOWS/workflow_1a_loader.py  
"""  
WORKFLOW-1A — Workflow file loader + validator + normalizer  
  
Loads a workflow definition from JSON or YAML (YAML optional if PyYAML is available),  
validates basic structure + known actions, and normalizes common aliases into a  
canonical (workflow, cfg_out, steps_out) shape.  
  
Reads existing generated artifacts (DO NOT re-derive):  
- REGISTRY/action_registry.json (preferred for action allowlist)  
- SCHEMA/steps_schema.json (required-fields validation; fallback allowlist)  
  
Rules:  
- Pure helper: no logging/printing.  
- Raise ValueError with actionable messages.  
- Deterministic output.  
"""  
  
from __future__ import annotations  
  
import json  
from copy import deepcopy  
from pathlib import Path  
from typing import Any, Dict, List, Optional, Set, Tuple  
  
__all__ = [  
    "load_workflow_file",  
    "load_validate_normalize_workflow",  
    "normalize_workflow",  
    "validate_workflow",  
]  
  
  
def _read_text(p: Path) -> str:  
    return p.read_text(encoding="utf-8", errors="replace")  
  
  
def _looks_like_repo_root(p: Path) -> bool:  
    if not p.exists() or not p.is_dir():  
        return False  
    if (p / "SCHEMA" / "steps_schema.json").exists():  
        return True  
    if (p / "DOC" / "library_index.json").exists():  
        return True  
    if (p / "PIPE").is_dir() and (p / "ACT").is_dir():  
        return True  
    return False  
  
  
def _find_repo_root(start: Path) -> Path:  
    s = start.parent if start.is_file() else start  
    for cand in [s, *s.parents]:  
        if _looks_like_repo_root(cand):  
            return cand  
    return s  
  
  
def _safe_load_json(path: Path) -> Optional[Any]:  
    try:  
        return json.loads(_read_text(path))  
    except Exception:  
        return None  
  
  
def _require_artifact(path: Path, how_to_fix: str) -> Path:  
    if not path.exists():  
        raise ValueError(f"Missing required artifact: {path}\nGenerate it first:\n  {how_to_fix}")  
    return path  
  
  
def _load_schema(repo_root: Path) -> dict:  
    schema_path = repo_root / "SCHEMA" / "steps_schema.json"  
    if not schema_path.exists():  
        # allow alternate known name, but prefer steps_schema.json  
        alt = repo_root / "SCHEMA" / "schema_1a_steps.json"  
        if alt.exists():  
            schema_path = alt  
        else:  
            raise ValueError(  
                "Missing SCHEMA artifact.\n"  
                "Expected SCHEMA/steps_schema.json (or SCHEMA/schema_1a_steps.json).\n"  
                "Generate it first:\n"  
                "  python SCHEMA/schema_1a_generate.py\n"  
                "or run:\n"  
                "  python dev/dev_smoke_schema_1a.py"  
            )  
  
    obj = _safe_load_json(schema_path)  
    if not isinstance(obj, dict) or not isinstance(obj.get("supported_actions"), list):  
        raise ValueError(f"Invalid schema JSON (missing supported_actions): {schema_path}")  
    return {"path": schema_path, "obj": obj}  
  
  
def _load_registry(repo_root: Path) -> Optional[dict]:  
    reg_path = repo_root / "REGISTRY" / "action_registry.json"  
    if not reg_path.exists():  
        return None  
    obj = _safe_load_json(reg_path)  
    if not isinstance(obj, dict) or not isinstance(obj.get("actions"), list):  
        return None  
    return {"path": reg_path, "obj": obj}  
  
  
def _build_action_allowlist(repo_root: Path) -> Tuple[Set[str], str]:  
    """  
    Returns (allowed_actions, source_label).  
    Prefer REGISTRY-1A if present; otherwise fallback to SCHEMA-1A.  
    """  
    reg = _load_registry(repo_root)  
    if reg is not None:  
        allowed = set()  
        for a in reg["obj"].get("actions") or []:  
            if isinstance(a, dict) and isinstance(a.get("action"), str):  
                allowed.add(a["action"])  
        return allowed, "REGISTRY/action_registry.json"  
  
    schema = _load_schema(repo_root)  
    allowed = set()  
    for a in schema["obj"].get("supported_actions") or []:  
        if isinstance(a, dict) and isinstance(a.get("action"), str):  
            allowed.add(a["action"])  
    return allowed, str(Path(schema["path"]).relative_to(repo_root).as_posix())  
  
  
def _build_required_fields_map(schema_obj: dict) -> Dict[str, Set[str]]:  
    req_map: Dict[str, Set[str]] = {}  
    for a in schema_obj.get("supported_actions") or []:  
        if not isinstance(a, dict):  
            continue  
        name = a.get("action")  
        if not isinstance(name, str) or not name:  
            continue  
        req = a.get("required_fields") or []  
        if not isinstance(req, list):  
            req = []  
        req_map[name] = {x for x in req if isinstance(x, str) and x != "action"}  
    return req_map  
  
  
def load_workflow_file(path: Path) -> dict:  
    """  
    Loads workflow from JSON or YAML (YAML optional).  
  
    Preference order:  
    1) try JSON parse always  
    2) if JSON fails, try YAML only if PyYAML available (and file looks like YAML by extension)  
    """  
    if not path.exists():  
        raise ValueError(f"Workflow file not found: {path}")  
  
    text = _read_text(path)  
  
    # Prefer JSON first  
    try:  
        obj = json.loads(text)  
        if not isinstance(obj, dict):  
            raise ValueError("Workflow root must be a JSON object")  
        return obj  
    except Exception as json_err:  
        # YAML optional  
        if path.suffix.lower() not in (".yml", ".yaml"):  
            raise ValueError(  
                f"Failed to parse workflow as JSON: {path}\n"  
                f"Error: {json_err}\n"  
                f"If this is YAML, rename to .yaml/.yml and install PyYAML."  
            )  
  
        try:  
            import yaml  # type: ignore  
        except Exception:  
            raise ValueError(  
                f"Failed to parse workflow as JSON: {path}\n"  
                f"Error: {json_err}\n"  
                "YAML support requires PyYAML.\n"  
                "Install:\n"  
                "  pip install pyyaml\n"  
                "Or provide workflow as JSON."  
            )  
  
        try:  
            obj = yaml.safe_load(text)  
        except Exception as yaml_err:  
            raise ValueError(f"Failed to parse workflow as YAML: {path}\nError: {yaml_err}")  
  
        if not isinstance(obj, dict):  
            raise ValueError("Workflow root must be an object/dict")  
        return obj  
  
  
def _normalize_worklist(workflow_obj: dict) -> Tuple[Optional[dict], Dict[str, Any]]:  
    """  
    Normalizes worklist configuration into cfg keys without duplicating PIPE-1B logic.  
    Accepts:  
      - workflow['worklist'] = {path, sheet, id_column}  
      - top-level PIPE-ish keys: worklist_path, worklist_sheet, id_column, worklist_id_column  
    Produces:  
      - worklist_norm dict (or None)  
      - cfg fragment dict with canonical keys  
    """  
    wl = workflow_obj.get("worklist")  
    wl_norm: Dict[str, Any] = {}  
    cfg: Dict[str, Any] = {}  
  
    # Top-level keys (PIPE-ish)  
    if isinstance(workflow_obj.get("worklist_path"), str):  
        cfg["worklist_path"] = workflow_obj["worklist_path"]  
        wl_norm["path"] = workflow_obj["worklist_path"]  
    if isinstance(workflow_obj.get("worklist_sheet"), str):  
        cfg["worklist_sheet"] = workflow_obj["worklist_sheet"]  
        wl_norm["sheet"] = workflow_obj["worklist_sheet"]  
    if isinstance(workflow_obj.get("id_column"), str):  
        cfg["id_column"] = workflow_obj["id_column"]  
        cfg["worklist_id_column"] = workflow_obj["id_column"]  
        wl_norm["id_column"] = workflow_obj["id_column"]  
    if isinstance(workflow_obj.get("worklist_id_column"), str) and "id_column" not in cfg:  
        cfg["worklist_id_column"] = workflow_obj["worklist_id_column"]  
        wl_norm["id_column"] = workflow_obj["worklist_id_column"]  
  
    # worklist dict  
    if wl is None:  
        return (wl_norm or None), cfg  
  
    if not isinstance(wl, dict):  
        raise ValueError("workflow.worklist must be an object/dict if present")  
  
    if isinstance(wl.get("path"), str):  
        wl_norm["path"] = wl["path"]  
        cfg["worklist_path"] = wl["path"]  
    if isinstance(wl.get("sheet"), str):  
        wl_norm["sheet"] = wl["sheet"]  
        cfg["worklist_sheet"] = wl["sheet"]  
    if isinstance(wl.get("id_column"), str):  
        wl_norm["id_column"] = wl["id_column"]  
        cfg["id_column"] = wl["id_column"]  
        cfg["worklist_id_column"] = wl["id_column"]  
  
    return (wl_norm or None), cfg  
  
  
def _normalize_step_aliases(step: Dict[str, Any]) -> Dict[str, Any]:  
    """  
    Normalizes common aliases into canonical keys expected by typical step runners,  
    without changing ACT modules.  
  
    Implemented (conservative):  
    - if step has {"by": "...", "value": "..."} and lacks selector fields:  
        value -> selector  
        by -> selector_strategy  
    - if step has selector_strategy but lacks by: copy to by  
    - if step has by but lacks selector_strategy: copy to selector_strategy  
    - if step has css/xpath/text at top-level: pick css->xpath->text as selector  
    """  
    out = dict(step)  
  
    # by/value -> selector/selector_strategy  
    if "value" in out and "selector" not in out:  
        if isinstance(out.get("value"), str) and out["value"].strip():  
            out["selector"] = out["value"]  
    if "by" in out and "selector_strategy" not in out:  
        if isinstance(out.get("by"), str) and out["by"].strip():  
            out["selector_strategy"] = out["by"]  
  
    # keep by <-> selector_strategy in sync (non-destructive)  
    if "selector_strategy" in out and "by" not in out:  
        if isinstance(out.get("selector_strategy"), str) and out["selector_strategy"].strip():  
            out["by"] = out["selector_strategy"]  
    if "by" in out and "selector_strategy" not in out:  
        if isinstance(out.get("by"), str) and out["by"].strip():  
            out["selector_strategy"] = out["by"]  
  
    # css/xpath/text leaf fields -> selector  
    if "selector" not in out:  
        for k in ("css", "xpath", "text"):  
            v = out.get(k)  
            if isinstance(v, str) and v.strip():  
                out["selector"] = v  
                out.setdefault("selector_strategy", k)  
                out.setdefault("by", k)  
                break  
  
    return out  
  
  
def normalize_workflow(workflow_obj: dict) -> Tuple[dict, dict, List[dict]]:  
    """  
    Returns:  
      (workflow_norm, cfg_out, steps_out)  
  
    - workflow_norm: deterministic normalized subset of top-level keys  
    - cfg_out: defaults merged with normalized worklist cfg fragment + vars seed  
    - steps_out: normalized step dicts (aliases normalized)  
    """  
    if not isinstance(workflow_obj, dict):  
        raise ValueError("Workflow must be an object/dict")  
  
    name = workflow_obj.get("name")  
    if not isinstance(name, str) or not name.strip():  
        raise ValueError("workflow.name is required and must be a non-empty string")  
  
    version = workflow_obj.get("version")  
    if version is not None and not isinstance(version, str):  
        raise ValueError("workflow.version must be a string if present")  
  
    desc = workflow_obj.get("description")  
    if desc is not None and not isinstance(desc, str):  
        raise ValueError("workflow.description must be a string if present")  
  
    defaults = workflow_obj.get("defaults") or {}  
    if not isinstance(defaults, dict):  
        raise ValueError("workflow.defaults must be an object/dict if present")  
  
    vars_seed = workflow_obj.get("vars")  
    if vars_seed is not None and not isinstance(vars_seed, dict):  
        raise ValueError("workflow.vars must be an object/dict if present")  
  
    steps = workflow_obj.get("steps")  
    if not isinstance(steps, list):  
        raise ValueError("workflow.steps is required and must be a list of step objects")  
    if not steps:  
        raise ValueError("workflow.steps must be non-empty")  
  
    # worklist normalization  
    worklist_norm, worklist_cfg = _normalize_worklist(workflow_obj)  
  
    # cfg_out = defaults merged with worklist cfg, plus vars seed (pass-through)  
    cfg_out: Dict[str, Any] = deepcopy(defaults)  
    cfg_out.update(worklist_cfg)  
    if isinstance(vars_seed, dict):  
        cfg_out.setdefault("vars_seed", deepcopy(vars_seed))  
  
    steps_out: List[dict] = []  
    for i, s in enumerate(steps):  
        if not isinstance(s, dict):  
            raise ValueError(f"workflow.steps[{i}] must be an object/dict")  
        steps_out.append(_normalize_step_aliases(s))  
  
    workflow_norm = {  
        "name": name.strip(),  
        "version": (version.strip() if isinstance(version, str) else None),  
        "description": (desc if isinstance(desc, str) else None),  
        "worklist": worklist_norm,  
        "defaults": deepcopy(defaults),  
        "vars": deepcopy(vars_seed) if isinstance(vars_seed, dict) else None,  
    }  
  
    return workflow_norm, cfg_out, steps_out  
  
  
def validate_workflow(  
    workflow_norm: dict,  
    steps_out: List[dict],  
    *,  
    repo_root: Optional[Path] = None,  
) -> None:  
    """  
    Validates:  
    - steps are list[dict] and each step has action  
    - action known via REGISTRY (preferred) OR SCHEMA allowlist  
    - required fields present per SCHEMA when available  
    """  
    repo_root = repo_root or _find_repo_root(Path(__file__).resolve())  
  
    allowed_actions, allowlist_src = _build_action_allowlist(repo_root)  
    schema = _load_schema(repo_root)  
    req_map = _build_required_fields_map(schema["obj"])  
  
    for i, step in enumerate(steps_out):  
        if not isinstance(step, dict):  
            raise ValueError(f"steps_out[{i}] must be a dict (normalizer produced invalid step)")  
  
        action = step.get("action")  
        if not isinstance(action, str) or not action.strip():  
            raise ValueError(f"workflow.steps[{i}] missing required string field 'action'")  
  
        action = action.strip()  
        if action not in allowed_actions:  
            raise ValueError(  
                f"workflow.steps[{i}].action '{action}' is not recognized (source: {allowlist_src}).\n"  
                "Regenerate artifacts if needed:\n"  
                "  python SCHEMA/schema_1a_generate.py\n"  
                "  python REGISTRY/registry_1a_generate.py"  
            )  
  
        # Required field presence check (when schema has metadata for action)  
        req = req_map.get(action)  
        if req:  
            missing = [f for f in sorted(req) if f not in step]  
            if missing:  
                raise ValueError(  
                    f"workflow.steps[{i}] action '{action}' missing required fields: {missing}\n"  
                    f"Tip: consult SCHEMA/steps_schema.json for '{action}'."  
                )  
  
    # workflow_norm sanity (already checked in normalize)  
    if not isinstance(workflow_norm.get("name"), str) or not workflow_norm["name"]:  
        raise ValueError("Normalized workflow missing name (internal error)")  
  
  
def load_validate_normalize_workflow(  
    workflow_path: Path,  
    *,  
    repo_root: Optional[Path] = None,  
) -> Tuple[dict, dict, List[dict]]:  
    """  
    Convenience entry:  
      - load file (JSON/YAML)  
      - normalize  
      - validate actions + required fields  
  
    Returns (workflow_norm, cfg_out, steps_out)  
    """  
    repo_root = repo_root or _find_repo_root(workflow_path)  
    wf_obj = load_workflow_file(workflow_path)  
    workflow_norm, cfg_out, steps_out = normalize_workflow(wf_obj)  
    validate_workflow(workflow_norm, steps_out, repo_root=repo_root)  
    return workflow_norm, cfg_out, steps_out  