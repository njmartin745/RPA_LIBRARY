# PLAN/plan_1a_step_planner.py  
"""  
PLAN-1A — Workflow Step Planner / Skeleton Generator  
  
Generates a valid steps.json skeleton from a high-level workflow intent using  
SCHEMA-1A outputs as the single source of truth.  
  
Outputs:  
- workflows/generated_steps.json  
- workflows/generated_plan.md  
  
Constraints:  
- Do NOT import/execute project modules with side effects.  
- Only use actions present in SCHEMA/steps_schema.json.  
- Prefer templates from SCHEMA/steps_examples.json when available.  
"""  
  
from __future__ import annotations  
  
import json  
import re  
from copy import deepcopy  
from dataclasses import dataclass  
from pathlib import Path  
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple  
  
__all__ = [  
    "load_schema_and_examples",  
    "plan_from_intent",  
    "write_plan_outputs",  
    "generate_workflow_skeleton",  
    "main",  
]  
  
URL_RE = re.compile(  
    r"(?P<url>(?:https?://)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?)"  
)  
  
# Nested step list keys that commonly appear in block actions (PIPE-style)  
NESTED_STEP_LIST_KEYS: Tuple[str, ...] = (  
    "steps",  
    "then",  
    "else",  
    "catch",  
    "finally",  
    "on_fail",  
    "on_error",  
)  
  
TYPE_ALIASES = {  
    "str": "string",  
    "string": "string",  
    "int": "int",  
    "integer": "int",  
    "bool": "bool",  
    "boolean": "bool",  
    "float": "float",  
    "number": "float",  
    "object": "object",  
    "dict": "object",  
    "list": "list",  
    "array": "list",  
    "any": "any",  
}  
  
  
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
    if any((p / d).is_dir() for d in ("ACT", "PIPE", "STATE", "ENTRY")) and (p / "SCHEMA").is_dir():  
        return True  
    return False  
  
  
def _find_repo_root(start: Path) -> Path:  
    s = start.parent if start.is_file() else start  
    for cand in [s, *s.parents]:  
        if _looks_like_repo_root(cand):  
            return cand  
    return s  
  
  
def _normalize_type(t: Optional[str]) -> str:  
    if not t:  
        return "any"  
    return TYPE_ALIASES.get(t.strip().lower(), t.strip().lower())  
  
  
@dataclass(frozen=True)  
class ActionSpec:  
    action: str  
    description: str  
    required_fields: List[str]  
    optional_fields: List[str]  
    field_types: Dict[str, str]  
    allowed_values: Dict[str, List[Any]]  
    examples: List[dict]  
  
  
def load_schema_and_examples(repo_root: Optional[Path] = None) -> Dict[str, Any]:  
    """  
    Loads:  
      - SCHEMA/steps_schema.json  
      - SCHEMA/steps_examples.json (optional but preferred)  
  
    Returns:  
      {  
        "schema_path": "...",  
        "examples_path": "...|None",  
        "actions": {action: ActionSpec(...)},  
      }  
    """  
    repo_root = repo_root or _find_repo_root(Path(__file__).resolve())  
    schema_path = repo_root / "SCHEMA" / "steps_schema.json"  
    if not schema_path.exists():  
        raise FileNotFoundError(f"Missing schema output: {schema_path}")  
  
    schema_obj = json.loads(_read_text(schema_path))  
    if not isinstance(schema_obj, dict) or not isinstance(schema_obj.get("supported_actions"), list):  
        raise ValueError("Invalid SCHEMA/steps_schema.json shape")  
  
    examples_path = repo_root / "SCHEMA" / "steps_examples.json"  
    examples_by_action: Dict[str, List[dict]] = {}  
    if examples_path.exists():  
        try:  
            ex_obj = json.loads(_read_text(examples_path))  
            if isinstance(ex_obj, dict) and isinstance(ex_obj.get("examples_by_action"), dict):  
                for k, v in ex_obj["examples_by_action"].items():  
                    if isinstance(k, str) and isinstance(v, list):  
                        examples_by_action[k] = [x for x in v if isinstance(x, dict)]  
        except Exception:  
            examples_by_action = {}  
  
    actions: Dict[str, ActionSpec] = {}  
    for entry in schema_obj["supported_actions"]:  
        if not isinstance(entry, dict):  
            continue  
        a = entry.get("action")  
        if not isinstance(a, str) or not a.strip():  
            continue  
  
        req = entry.get("required_fields") or []  
        opt = entry.get("optional_fields") or []  
        ftypes = entry.get("field_types") or {}  
        allowed = entry.get("allowed_values") or {}  
  
        req = [x for x in req if isinstance(x, str)]  
        opt = [x for x in opt if isinstance(x, str)]  
        ftypes = {k: _normalize_type(v) for k, v in ftypes.items() if isinstance(k, str) and isinstance(v, str)}  
        allowed_norm: Dict[str, List[Any]] = {}  
        for k, v in allowed.items():  
            if not isinstance(k, str):  
                continue  
            allowed_norm[k] = v if isinstance(v, list) else [v]  
  
        ex = examples_by_action.get(a) or []  
        if isinstance(entry.get("examples"), list):  
            # merge schema-embedded examples as fallback  
            ex2 = [x for x in entry["examples"] if isinstance(x, dict)]  
            if not ex:  
                ex = ex2  
            else:  
                # append unique  
                seen = {json.dumps(x, sort_keys=True, ensure_ascii=False) for x in ex}  
                for x in ex2:  
                    sig = json.dumps(x, sort_keys=True, ensure_ascii=False)  
                    if sig not in seen:  
                        ex.append(x)  
                        seen.add(sig)  
  
        actions[a] = ActionSpec(  
            action=a,  
            description=str(entry.get("description") or ""),  
            required_fields=req,  
            optional_fields=opt,  
            field_types=ftypes,  
            allowed_values=allowed_norm,  
            examples=ex,  
        )  
  
    return {  
        "schema_path": str(schema_path),  
        "examples_path": str(examples_path) if examples_path.exists() else None,  
        "actions": actions,  
        "raw_schema": schema_obj,  
    }  
  
  
def _extract_url(intent: str) -> Optional[str]:  
    m = URL_RE.search(intent or "")  
    if not m:  
        return None  
    url = m.group("url")  
    if url and not url.startswith(("http://", "https://")):  
        url = "https://" + url  
    return url  
  
  
def _choose_action(actions: Set[str], preferred: Sequence[str]) -> Optional[str]:  
    for p in preferred:  
        if p in actions:  
            return p  
    return None  
  
  
def _rank_actions_by_keyword(actions: Dict[str, ActionSpec], keywords: Sequence[str]) -> List[str]:  
    keys = [k.lower() for k in keywords if k]  
    scored: List[Tuple[int, str]] = []  
    for a, spec in actions.items():  
        hay = f"{a} {spec.description}".lower()  
        score = sum(1 for k in keys if k in hay)  
        scored.append((score, a))  
    scored.sort(key=lambda x: (-x[0], x[1]))  
    return [a for _, a in scored]  
  
  
def _placeholder_for_field(field: str, ftype: str, *, url: Optional[str], allowed: Optional[List[Any]]) -> Any:  
    # Prefer allowed values if present  
    if allowed:  
        return allowed[0]  
  
    ftype = _normalize_type(ftype)  
    f_upper = field.upper()  
  
    if field in {"url", "href", "page", "target_url"}:  
        return url or "https://TODO_URL"  
    if field in {"selector", "css", "xpath", "query"}:  
        return "TODO_SELECTOR"  
    if field in {"by", "selector_by", "locate_by"}:  
        return "css"  
    if field in {"text", "value", "input", "keys"}:  
        return "TODO_TEXT"  
    if field in {"path", "file", "download_path", "out_path", "save_as"}:  
        return "TODO_PATH"  
    if field in {"js_file", "script_file"}:  
        return "TODO_SCRIPT.js"  
    if field in {"code", "js", "script"}:  
        return "/* TODO_JS */ return true;"  
    if field in {"seconds", "secs"}:  
        return 2  
    if field in {"ms", "millis", "milliseconds"}:  
        return 1000  
    if field in {"timeout", "timeout_seconds"}:  
        return 30  
  
    if ftype == "string":  
        return f"TODO_{f_upper}"  
    if ftype == "int":  
        return 1  
    if ftype == "float":  
        return 1.0  
    if ftype == "bool":  
        return True  
    if ftype == "object":  
        return {}  
    if ftype == "list":  
        return []  
    return f"TODO_{f_upper}"  
  
  
def _filter_to_schema_fields(step: dict, spec: ActionSpec) -> dict:  
    allowed_fields = set(spec.required_fields or []) | set(spec.optional_fields or [])  
    allowed_fields.add("action")  
    return {k: v for k, v in step.items() if isinstance(k, str) and k in allowed_fields}  
  
  
def _build_step_from_example_or_scratch(spec: ActionSpec, *, url: Optional[str], todos: List[str]) -> dict:  
    # Prefer example template if available  
    base: dict = {}  
    if spec.examples:  
        base = deepcopy(spec.examples[0])  
        if not isinstance(base, dict):  
            base = {}  
    base["action"] = spec.action  
  
    # Filter to only schema-known fields to avoid unknown-field lint warnings  
    base = _filter_to_schema_fields(base, spec)  
  
    # Ensure required fields exist  
    for f in spec.required_fields or []:  
        if f == "action":  
            continue  
        if f not in base:  
            allowed = spec.allowed_values.get(f)  
            base[f] = _placeholder_for_field(  
                f,  
                spec.field_types.get(f, "any"),  
                url=url,  
                allowed=allowed,  
            )  
            if isinstance(base[f], str) and base[f].startswith("TODO_"):  
                todos.append(f"{spec.action}: provide value for '{f}'")  
            if f in {"url", "href", "page", "target_url"} and (url is None):  
                todos.append(f"{spec.action}: provide URL")  
  
    # Fix obvious TODO defaults for url if we have one  
    for f in ("url", "href", "page", "target_url"):  
        if f in base and isinstance(base[f], str) and base[f] in {"https://TODO_URL"} and url:  
            base[f] = url  
  
    # If the example includes nested blocks, keep them as-is (but ensure lists are list-of-dict)  
    for nk in NESTED_STEP_LIST_KEYS:  
        if nk in base and isinstance(base[nk], list):  
            base[nk] = [x for x in base[nk] if isinstance(x, dict)]  
  
    return base  
  
  
def plan_from_intent(intent: str, schema_bundle: Dict[str, Any]) -> Dict[str, Any]:  
    """  
    Returns:  
      {  
        "intent": "...",  
        "phases": [...],  
        "assumed_actions": [...],  
        "missing_info": [...],  
        "steps": [ ... ]  
      }  
    """  
    actions: Dict[str, ActionSpec] = schema_bundle["actions"]  
    action_names: Set[str] = set(actions.keys())  
  
    url = _extract_url(intent)  
    intent_l = (intent or "").lower()  
  
    assumed_actions: List[str] = []  
    phases: List[str] = []  
    todos: List[str] = []  
    steps: List[dict] = []  
  
    # Heuristic: navigation/open  
    wants_open = any(k in intent_l for k in ("open ", "go to", "goto", "navigate", "visit ", "browse "))  
    if wants_open or url:  
        nav_action = _choose_action(action_names, ["get", "goto", "navigate", "open", "nav"])  
        if nav_action is None:  
            # fallback: pick highest match to navigation keywords  
            ranked = _rank_actions_by_keyword(actions, ["navigate", "open", "url", "get"])  
            nav_action = ranked[0] if ranked else None  
        if nav_action:  
            assumed_actions.append(nav_action)  
            phases.append(f"Navigate/open ({nav_action})")  
            steps.append(_build_step_from_example_or_scratch(actions[nav_action], url=url, todos=todos))  
        else:  
            todos.append("No navigation-like action found in schema; cannot plan 'open' step")  
  
    # Heuristic: wait  
    wants_wait = any(k in intent_l for k in ("wait", "pause", "sleep", "page load", "page to load"))  
    if wants_wait:  
        wait_action = _choose_action(action_names, ["wait", "sleep", "pause"])  
        if wait_action is None:  
            ranked = _rank_actions_by_keyword(actions, ["wait", "sleep", "delay"])  
            wait_action = ranked[0] if ranked else None  
        if wait_action:  
            assumed_actions.append(wait_action)  
            phases.append(f"Wait/delay ({wait_action})")  
            steps.append(_build_step_from_example_or_scratch(actions[wait_action], url=url, todos=todos))  
        else:  
            todos.append("No wait-like action found in schema; cannot plan 'wait' step")  
  
    # If nothing matched, still produce a skeleton using a minimal-required action (schema-safe)  
    if not steps and actions:  
        # choose action with fewest non-action required fields  
        best = None  
        best_count = 10**9  
        for a, spec in actions.items():  
            req = [f for f in (spec.required_fields or []) if f != "action"]  
            if len(req) < best_count:  
                best = spec  
                best_count = len(req)  
        if best:  
            assumed_actions.append(best.action)  
            phases.append(f"Fallback minimal step ({best.action})")  
            steps.append(_build_step_from_example_or_scratch(best, url=url, todos=todos))  
            todos.append("Refine intent-to-action mapping: fallback used")  
  
    # De-dup todos while preserving order  
    seen: Set[str] = set()  
    missing_info: List[str] = []  
    for t in todos:  
        if t not in seen:  
            missing_info.append(t)  
            seen.add(t)  
  
    return {  
        "intent": intent,  
        "phases": phases,  
        "assumed_actions": assumed_actions,  
        "missing_info": missing_info,  
        "steps": steps,  
    }  
  
  
def write_plan_outputs(  
    plan: Dict[str, Any],  
    *,  
    repo_root: Optional[Path] = None,  
    out_dir: Optional[Path] = None,  
) -> Dict[str, str]:  
    """  
    Writes:  
      - workflows/generated_steps.json  
      - workflows/generated_plan.md  
  
    Returns paths:  
      {"steps_path": "...", "plan_path": "..."}  
    """  
    repo_root = repo_root or _find_repo_root(Path(__file__).resolve())  
    out_dir = out_dir or (repo_root / "workflows")  
    out_dir.mkdir(parents=True, exist_ok=True)  
  
    steps_path = out_dir / "generated_steps.json"  
    plan_path = out_dir / "generated_plan.md"  
  
    _write_json(steps_path, plan.get("steps") or [])  
  
    # Plan markdown  
    lines: List[str] = []  
    lines.append("# Generated Workflow Plan")  
    lines.append("")  
    lines.append("## Intent")  
    lines.append("")  
    lines.append(f"- {plan.get('intent')}")  
    lines.append("")  
    lines.append("## Interpreted phases")  
    lines.append("")  
    phases = plan.get("phases") or []  
    if phases:  
        for i, ph in enumerate(phases, 1):  
            lines.append(f"{i}. {ph}")  
    else:  
        lines.append("_(none)_")  
    lines.append("")  
    lines.append("## Assumed actions")  
    lines.append("")  
    acts = plan.get("assumed_actions") or []  
    if acts:  
        for a in acts:  
            lines.append(f"- `{a}`")  
    else:  
        lines.append("_(none)_")  
    lines.append("")  
    lines.append("## Missing information checklist")  
    lines.append("")  
    miss = plan.get("missing_info") or []  
    if miss:  
        for m in miss:  
            lines.append(f"- [ ] {m}")  
    else:  
        lines.append("- [ ] Review selectors/credentials/paths as needed")  
    lines.append("")  
  
    _write_text(plan_path, "\n".join(lines))  
  
    return {"steps_path": str(steps_path), "plan_path": str(plan_path)}  
  
  
def generate_workflow_skeleton(  
    intent: str,  
    *,  
    repo_root: Optional[Path] = None,  
) -> Dict[str, Any]:  
    """  
    High-level helper:  
      - loads schema + examples  
      - creates plan  
      - writes outputs under workflows/  
    Returns:  
      {"plan": <plan dict>, "paths": {...}}  
    """  
    repo_root = repo_root or _find_repo_root(Path(__file__).resolve())  
    bundle = load_schema_and_examples(repo_root=repo_root)  
    plan = plan_from_intent(intent, bundle)  
    paths = write_plan_outputs(plan, repo_root=repo_root)  
    return {"plan": plan, "paths": paths}  
  
  
def main(argv: Optional[List[str]] = None) -> int:  
    import argparse  
  
    p = argparse.ArgumentParser(prog="plan_1a_step_planner", description="Generate steps.json skeleton from intent.")  
    p.add_argument("intent", nargs="+", help="High-level workflow description")  
    args = p.parse_args(argv)  
  
    intent = " ".join(args.intent).strip()  
    res = generate_workflow_skeleton(intent)  
    paths = res["paths"]  
    print("[PLAN-1A] Wrote:")  
    print(f"  {paths['steps_path']}")  
    print(f"  {paths['plan_path']}")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  