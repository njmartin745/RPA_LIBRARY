# BUILD/build_1a_workflow_generator.py  
from __future__ import annotations  
  
import json  
from collections import Counter  
from dataclasses import dataclass  
from pathlib import Path  
from typing import Any  
  
__all__ = [  
    "generate_workflow",  
    "validate_spec",  
    "normalize_spec",  
    "suggest_missing_fields",  
]  
  
from BUILD.build_1c_action_normalizer import normalize_workflow_actions  
  
_DETERMINISTIC_CREATED_AT_UTC = "1970-01-01T00:00:00Z"  
  
  
@dataclass(frozen=True)  
class _Assets:  
    repo_root: Path  
    schema_path: Path | None  
    schema_obj: dict | None  
    registry_path: Path | None  
    registry_obj: dict | None  
    selectors_path: Path | None  
    selectors_obj: dict | None  
  
  
def _find_repo_root(start: Path) -> Path:  
    """  
    Locate repo root robustly even when called from dev/ or elsewhere.  
    Heuristic: must contain SCHEMA/ and REGISTRY/ directories.  
    """  
    start = start.resolve()  
    for p in [start, *start.parents]:  
        if (p / "SCHEMA").is_dir() and (p / "REGISTRY").is_dir():  
            return p  
    # Fallback: current working directory if it looks like a repo root  
    cwd = Path.cwd().resolve()  
    if (cwd / "SCHEMA").is_dir() and (cwd / "REGISTRY").is_dir():  
        return cwd  
    raise RuntimeError("BUILD-1A: Could not locate repo root containing SCHEMA/ and REGISTRY/.")  
  
  
def _read_json(path: Path) -> Any:  
    return json.loads(path.read_text(encoding="utf-8"))  
  
  
def _load_assets() -> _Assets:  
    repo_root = _find_repo_root(Path(__file__))  
  
    schema_path = None  
    for cand in (  
        repo_root / "SCHEMA" / "steps_schema.json",  
        repo_root / "SCHEMA" / "schema_1a_steps.json",  
    ):  
        if cand.exists():  
            schema_path = cand  
            break  
  
    registry_path = repo_root / "REGISTRY" / "action_registry.json"  
    if not registry_path.exists():  
        registry_path = None  
  
    selectors_path = repo_root / "data" / "selectors.json"  
    if not selectors_path.exists():  
        selectors_path = None  
  
    schema_obj = _read_json(schema_path) if schema_path else None  
    registry_obj = _read_json(registry_path) if registry_path else None  
    selectors_obj = _read_json(selectors_path) if selectors_path else None  
  
    # Normalize non-dict selector shapes to None (we only support dicts here)  
    if selectors_obj is not None and not isinstance(selectors_obj, dict):  
        selectors_obj = None  
  
    return _Assets(  
        repo_root=repo_root,  
        schema_path=schema_path,  
        schema_obj=schema_obj if isinstance(schema_obj, dict) else None,  
        registry_path=registry_path,  
        registry_obj=registry_obj if isinstance(registry_obj, dict) else None,  
        selectors_path=selectors_path,  
        selectors_obj=selectors_obj,  
    )  
  
  
def _extract_schema_version(schema_obj: dict | None) -> str | None:  
    if not schema_obj:  
        return None  
    for k in ("schema_version", "version"):  
        v = schema_obj.get(k)  
        if isinstance(v, str) and v.strip():  
            return v.strip()  
    v = schema_obj.get("$id")  
    if isinstance(v, str) and v.strip():  
        return v.strip()  
    return None  
  
  
def _allowed_actions(registry_obj: dict | None) -> set[str]:  
    if not registry_obj:  
        return set()  
  
    actions = registry_obj.get("actions")  
  
    if isinstance(actions, dict):  
        return {str(k) for k in actions.keys()}  
  
    if isinstance(actions, list):  
        out: set[str] = set()  
        for item in actions:  
            if isinstance(item, dict):  
                a = item.get("action") or item.get("name")  
                if isinstance(a, str) and a.strip():  
                    out.add(a.strip())  
        return out  
  
    blacklist = {"generated_at_utc", "generated_at", "version", "schema_version", "meta", "__meta__"}  
    return {str(k) for k in registry_obj.keys() if str(k) not in blacklist}  
  
  
def _action_meta(registry_obj: dict | None, action: str) -> dict | None:  
    if not registry_obj:  
        return None  
  
    actions = registry_obj.get("actions")  
  
    if isinstance(actions, dict):  
        meta = actions.get(action)  
        return meta if isinstance(meta, dict) else None  
  
    if isinstance(actions, list):  
        for item in actions:  
            if not isinstance(item, dict):  
                continue  
            a = item.get("action") or item.get("name")  
            if a == action:  
                return item  
        return None  
  
    meta = registry_obj.get(action)  
    return meta if isinstance(meta, dict) else None  
  
  
def _required_fields_for_action(meta: dict | None) -> list[str]:  
    if not meta:  
        return []  
    for k in ("required", "required_fields", "requires"):  
        v = meta.get(k)  
        if isinstance(v, list):  
            return [str(x) for x in v if isinstance(x, (str, int, float))]  
    # Sometimes registries use "args": {"url": {"required": true}, ...}  
    args = meta.get("args")  
    if isinstance(args, dict):  
        req: list[str] = []  
        for name, spec in args.items():  
            if isinstance(spec, dict) and spec.get("required") is True:  
                req.append(str(name))  
        return req  
    return []  
  
  
def normalize_spec(spec: dict) -> dict:  
    """  
    Normalize user-provided build spec. Deterministic (no timestamps generated here).  
    Also normalizes legacy action aliases in spec.steps (e.g., 'get' -> 'open').  
    """  
    if not isinstance(spec, dict):  
        return {}  
  
    out = dict(spec)  
  
    name = out.get("name")  
    out["name"] = str(name).strip() if name is not None else ""  
  
    out.setdefault("intent", "")  
    out.setdefault("entry_url", "")  
    out["headless"] = bool(out.get("headless", True))  
  
    inputs = out.get("inputs")  
    if not isinstance(inputs, dict):  
        inputs = {"mode": "none"}  
    inputs.setdefault("mode", "none")  
    out["inputs"] = inputs  
  
    outputs = out.get("outputs")  
    out["outputs"] = outputs if isinstance(outputs, dict) else {}  
  
    notes = out.get("notes")  
    if notes is None:  
        notes = []  
    if not isinstance(notes, list):  
        notes = [str(notes)]  
    out["notes"] = [str(x) for x in notes]  
  
    steps = out.get("steps")  
    if steps is None:  
        steps = []  
    if not isinstance(steps, list):  
        steps = []  
    norm_steps: list[dict] = []  
    for s in steps:  
        if isinstance(s, dict):  
            step = dict(s)  
            if "action" in step and step["action"] is not None:  
                step["action"] = str(step["action"]).strip()  
            norm_steps.append(step)  
    out["steps"] = norm_steps  
  
    # Optional explicit flag to allow raw selector inlining  
    out["allow_inline_selectors"] = bool(out.get("allow_inline_selectors", False))  
  
    # Normalize legacy action names inside steps (and nested repeat.steps)  
    out = normalize_workflow_actions(out)  
  
    return out  
  
  
def validate_spec(spec: dict) -> list[str]:  
    """  
    Return a list of validation errors (empty => valid enough to generate).  
    Uses REGISTRY + SCHEMA availability as part of validation.  
    """  
    errors: list[str] = []  
    s = normalize_spec(spec)  
  
    if not s.get("name"):  
        errors.append("Missing required field: spec.name")  
  
    name = s.get("name", "")  
    # keep filename safe-ish  
    if name and any(c in name for c in r'\/:*?"<>|'):  
        errors.append(f"Invalid spec.name for filename on Windows: {name!r}")  
  
    steps = s.get("steps", [])  
    if not isinstance(steps, list):  
        errors.append("spec.steps must be a list")  
  
    assets = _load_assets()  
    if assets.registry_obj is None:  
        errors.append("Missing REGISTRY/action_registry.json (required by BUILD-1A).")  
        allowed = set()  
    else:  
        allowed = _allowed_actions(assets.registry_obj)  
  
    for i, step in enumerate(steps):  
        if not isinstance(step, dict):  
            errors.append(f"steps[{i}] must be an object")  
            continue  
        action = step.get("action")  
        if not isinstance(action, str) or not action.strip():  
            errors.append(f"steps[{i}] missing required field: action")  
            continue  
        if allowed and action not in allowed:  
            errors.append(f"steps[{i}].action={action!r} is not in action registry")  
  
        meta = _action_meta(assets.registry_obj, action) if assets.registry_obj else None  
        for req in _required_fields_for_action(meta):  
            if req not in step or step.get(req) in (None, "", [], {}):  
                errors.append(f"steps[{i}] missing required field for action {action!r}: {req}")  
  
    mode = s.get("inputs", {}).get("mode", "none")  
    if mode not in ("none", "excel", "csv"):  
        errors.append("inputs.mode must be one of: none | excel | csv")  
  
    # We intentionally do NOT fail spec for missing selectors; we emit TODOs during generation.  
    return errors  
  
  
def suggest_missing_fields(spec: dict) -> dict:  
    """  
    Return suggestions (not enforced) based on registry-required fields.  
    """  
    s = normalize_spec(spec)  
    assets = _load_assets()  
    suggestions: dict[str, Any] = {"steps": []}  
  
    for step in s.get("steps", []):  
        if not isinstance(step, dict):  
            continue  
        action = step.get("action")  
        if not isinstance(action, str) or not action:  
            suggestions["steps"].append({"action": "TODO_ACTION"})  
            continue  
  
        meta = _action_meta(assets.registry_obj, action) if assets.registry_obj else None  
        reqs = _required_fields_for_action(meta)  
        missing = [k for k in reqs if k not in step or step.get(k) in (None, "", [], {})]  
        suggestions["steps"].append({"action": action, "missing_required_fields": missing})  
  
    return suggestions  
  
  
def _selector_pairs_from_entry(entry: Any) -> list[tuple[str, str]]:  
    """  
    Turn a selectors.json entry into normalized (by, locator) pairs.  
    Supports a few common shapes.  
    """  
    pairs: list[tuple[str, str]] = []  
    if isinstance(entry, dict):  
        if isinstance(entry.get("by"), str) and isinstance(entry.get("locator"), str):  
            pairs.append((entry["by"].strip().lower(), entry["locator"]))  
        # simple one-liners: {"css": "h1"} or {"xpath": "..."}  
        for k in ("css", "xpath", "id", "name"):  
            v = entry.get(k)  
            if isinstance(v, str) and v.strip():  
                pairs.append((k, v))  
    return pairs  
  
  
def _build_selector_index(selectors_obj: dict | None) -> dict[tuple[str, str], str]:  
    """  
    Map (by, locator) -> selector_ref  
    """  
    idx: dict[tuple[str, str], str] = {}  
    if not selectors_obj:  
        return idx  
    for ref, entry in selectors_obj.items():  
        for pair in _selector_pairs_from_entry(entry):  
            idx[pair] = str(ref)  
    return idx  
  
  
def _selector_pairs_from_step(step: dict) -> list[tuple[str, str]]:  
    pairs: list[tuple[str, str]] = []  
    if isinstance(step.get("by"), str) and isinstance(step.get("locator"), str):  
        pairs.append((step["by"].strip().lower(), str(step["locator"])))  
    for k in ("css", "xpath", "id", "name"):  
        v = step.get(k)  
        if isinstance(v, str) and v.strip():  
            pairs.append((k, v))  
    return pairs  
  
  
def _prefer_selector_ref(  
    step: dict,  
    *,  
    selector_index: dict[tuple[str, str], str],  
    allow_inline_selectors: bool,  
    step_index: int,  
) -> tuple[dict, list[str], list[str]]:  
    """  
    Enforce: prefer selector_ref, avoid raw selectors unless explicitly allowed.  
    If raw selector is present but no selector_ref and no match found, replace with TODO selector_ref + TODO note.  
    """  
    todos: list[str] = []  
    warnings: list[str] = []  
  
    if not isinstance(step, dict):  
        return step, todos, warnings  
  
    if isinstance(step.get("selector_ref"), str) and step["selector_ref"].strip():  
        # Optional: warn if selector_ref is not present in selectors registry  
        return step, todos, warnings  
  
    raw_pairs = _selector_pairs_from_step(step)  
    if not raw_pairs:  
        return step, todos, warnings  
  
    # If user explicitly allows raw selectors, keep them as-is.  
    if allow_inline_selectors or bool(step.get("allow_inline_selectors", False)):  
        warnings.append(f"steps[{step_index}]: raw selector kept (allow_inline_selectors=True).")  
        return step, todos, warnings  
  
    # Attempt to map to an existing selector_ref  
    for pair in raw_pairs:  
        if pair in selector_index:  
            new_step = dict(step)  
            new_step["selector_ref"] = selector_index[pair]  
            for k in ("by", "locator", "css", "xpath", "id", "name"):  
                new_step.pop(k, None)  
            return new_step, todos, warnings  
  
    # No match -> replace with TODO selector_ref placeholder  
    new_step = dict(step)  
    todo_ref = f"TODO_SELECTOR_{step_index}"  
    new_step["selector_ref"] = todo_ref  
    for k in ("by", "locator", "css", "xpath", "id", "name"):  
        new_step.pop(k, None)  
  
    todos.append(  
        f"steps[{step_index}]: needs selector. Create a selector entry in data/selectors.json and replace "  
        f"{todo_ref!r} with the real selector_ref."  
    )  
    return new_step, todos, warnings  
  
  
def generate_workflow(  
    spec: dict,  
    *,  
    output_dir: str | Path = "workflows",  
    overwrite: bool = False,  
) -> dict:  
    assets = _load_assets()  
    s = normalize_spec(spec)  
  
    errors = validate_spec(s)  
    warnings: list[str] = []  
    todos: list[str] = []  
  
    schema_version = _extract_schema_version(assets.schema_obj)  
  
    created_at_utc = s.get("created_at_utc")  
    if not isinstance(created_at_utc, str) or not created_at_utc.strip():  
        created_at_utc = _DETERMINISTIC_CREATED_AT_UTC  
        warnings.append(  
            f"created_at_utc not provided; using deterministic placeholder {created_at_utc!r}. "  
            "Provide spec.created_at_utc to override."  
        )  
  
    selector_index = _build_selector_index(assets.selectors_obj)  
    allow_inline_selectors = bool(s.get("allow_inline_selectors", False))  
  
    # Build steps (schema/registry-driven constraint: do not invent actions)  
    normalized_steps: list[dict] = []  
    actions_used: Counter[str] = Counter()  
  
    for i, step in enumerate(s.get("steps", [])):  
        if not isinstance(step, dict):  
            continue  
        action = step.get("action", "")  
        if isinstance(action, str) and action:  
            actions_used[action] += 1  
  
        # Selector policy: prefer selector_ref  
        step2, step_todos, step_warnings = _prefer_selector_ref(  
            step,  
            selector_index=selector_index,  
            allow_inline_selectors=allow_inline_selectors,  
            step_index=i,  
        )  
        todos.extend(step_todos)  
        warnings.extend(step_warnings)  
  
        normalized_steps.append(step2)  
  
    # Inputs mode wiring note (per intake rules)  
    mode = s.get("inputs", {}).get("mode", "none")  
    if mode in ("excel", "csv"):  
        todos.append(  
            f"inputs.mode={mode!r}: BUILD-1A does not emit manifest/loop steps. "  
            "Wire INPUT/LOOP via PIPE configuration or add workflow-level worklist config as needed."  
        )  
  
    workflow_obj: dict[str, Any] = {  
        "name": s.get("name", ""),  
        "intent": s.get("intent", ""),  
        "entry_url": s.get("entry_url", ""),  
        "headless": bool(s.get("headless", True)),  
        "inputs": s.get("inputs", {}),  
        "outputs": s.get("outputs", {}),  
        "notes": list(s.get("notes", [])),  
        "metadata": {  
            "created_at_utc": created_at_utc,  
            "generator": "BUILD-1A",  
            "schema_version": schema_version,  
        },  
        "steps": normalized_steps,  
    }  
  
    # Attach TODOs as notes (but keep them separate in the return payload too)  
    if todos:  
        workflow_obj["notes"] = workflow_obj.get("notes", []) + [f"TODO: {t}" for t in todos]  
  
    # Final safety: normalize any legacy actions that made it through  
    workflow_obj = normalize_workflow_actions(workflow_obj)  
  
    out_dir = Path(output_dir)  
    out_dir.mkdir(parents=True, exist_ok=True)  
    out_path = out_dir / f"{workflow_obj['name']}.json"  
  
    if out_path.exists() and not overwrite:  
        errors.append(f"Refusing to overwrite existing workflow: {str(out_path)} (overwrite=False)")  
  
    ok = len(errors) == 0  
    if ok:  
        out_path.write_text(  
            json.dumps(workflow_obj, indent=2, sort_keys=True) + "\n",  
            encoding="utf-8",  
        )  
  
    # Deterministic summary ordering  
    actions_used_dict = {k: actions_used[k] for k in sorted(actions_used.keys())}  
  
    return {  
        "ok": ok,  
        "workflow_path": str(out_path),  
        "warnings": warnings,  
        "todos": todos,  
        "errors": errors,  
        "summary": {  
            "step_count": len(normalized_steps),  
            "actions_used": actions_used_dict,  
        },  
    }  