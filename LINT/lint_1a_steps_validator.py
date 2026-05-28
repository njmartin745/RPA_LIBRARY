# LINT/lint_1a_steps_validator.py  
"""  
LINT-1A — Step Validation Engine  
  
Validates step definitions (steps.json) against SCHEMA/steps_schema.json (SCHEMA-1A)  
*before execution*.  
  
Constraints:  
- Do NOT import/execute project modules with side effects.  
- Use SCHEMA output as the authority; do not re-derive schema from ACT/PIPE.  
"""  
  
from __future__ import annotations  
  
import json  
from dataclasses import dataclass  
from pathlib import Path  
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple  
  
__all__ = [  
    "load_steps_schema",  
    "validate_steps_data",  
    "validate_steps_file",  
    "format_report_text",  
]  
  
# Keys that commonly contain nested step lists for PIPE-2B style block actions  
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
  
  
def _looks_like_repo_root(p: Path) -> bool:  
    if not p.exists() or not p.is_dir():  
        return False  
    if (p / "SCHEMA" / "steps_schema.json").exists():  
        return True  
    if (p / "SCHEMA").is_dir() and any((p / d).is_dir() for d in ("ACT", "PIPE", "STATE", "ENTRY")):  
        return True  
    if (p / "DOC" / "library_index.json").exists():  
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
  
  
def _is_int_not_bool(x: Any) -> bool:  
    return isinstance(x, int) and not isinstance(x, bool)  
  
  
def _check_type(value: Any, expected: str) -> bool:  
    expected = _normalize_type(expected)  
    if expected == "any":  
        return True  
    if expected == "string":  
        return isinstance(value, str)  
    if expected == "bool":  
        return isinstance(value, bool)  
    if expected == "int":  
        return _is_int_not_bool(value)  
    if expected == "float":  
        # allow int for float, but not bool  
        return (isinstance(value, float) or _is_int_not_bool(value))  
    if expected == "object":  
        return isinstance(value, dict)  
    if expected == "list":  
        return isinstance(value, list)  
    # unknown schema type => do not hard-fail  
    return True  
  
  
@dataclass(frozen=True)  
class ActionSchema:  
    action: str  
    required_fields: List[str]  
    optional_fields: List[str]  
    field_types: Dict[str, str]  
    allowed_values: Dict[str, List[Any]]  
    raw: Dict[str, Any]  
  
  
def load_steps_schema(  
    schema_path: Optional[Path] = None,  
    repo_root: Optional[Path] = None,  
) -> Dict[str, Any]:  
    """  
    Loads SCHEMA/steps_schema.json and returns:  
      {  
        "schema_version": ...,  
        "generated_at": ...,  
        "actions": { action_name: ActionSchema(...) },  
        "raw": <entire schema json>  
      }  
    """  
    if repo_root is None:  
        repo_root = _find_repo_root(Path(__file__).resolve())  
  
    if schema_path is None:  
        schema_path = repo_root / "SCHEMA" / "steps_schema.json"  
  
    if not schema_path.exists():  
        raise FileNotFoundError(f"Schema not found: {schema_path}")  
  
    obj = json.loads(_read_text(schema_path))  
    if not isinstance(obj, dict):  
        raise ValueError("steps_schema.json must be a JSON object")  
  
    supported = obj.get("supported_actions")  
    if not isinstance(supported, list):  
        raise ValueError("steps_schema.json missing supported_actions list")  
  
    actions: Dict[str, ActionSchema] = {}  
    for entry in supported:  
        if not isinstance(entry, dict):  
            continue  
        a = entry.get("action")  
        if not isinstance(a, str) or not a.strip():  
            continue  
        req = entry.get("required_fields") or []  
        opt = entry.get("optional_fields") or []  
        ftypes = entry.get("field_types") or {}  
        allowed = entry.get("allowed_values") or {}  
  
        if not isinstance(req, list):  
            req = []  
        if not isinstance(opt, list):  
            opt = []  
        if not isinstance(ftypes, dict):  
            ftypes = {}  
        if not isinstance(allowed, dict):  
            allowed = {}  
  
        # normalize  
        req_s = [x for x in req if isinstance(x, str)]  
        opt_s = [x for x in opt if isinstance(x, str)]  
        ftypes_s = {k: _normalize_type(v) for k, v in ftypes.items() if isinstance(k, str) and isinstance(v, str)}  
  
        allowed_s: Dict[str, List[Any]] = {}  
        for k, v in allowed.items():  
            if not isinstance(k, str):  
                continue  
            if isinstance(v, list):  
                allowed_s[k] = v  
            else:  
                allowed_s[k] = [v]  
  
        actions[a] = ActionSchema(  
            action=a,  
            required_fields=req_s,  
            optional_fields=opt_s,  
            field_types=ftypes_s,  
            allowed_values=allowed_s,  
            raw=entry,  
        )  
  
    return {  
        "schema_version": obj.get("schema_version"),  
        "generated_at": obj.get("generated_at"),  
        "actions": actions,  
        "raw": obj,  
        "schema_path": str(schema_path),  
    }  
  
  
def _ensure_steps_list(steps_obj: Any) -> Tuple[Optional[List[Any]], Optional[str]]:  
    """  
    Accepts either:  
      - a list of step dicts  
      - an object like {"steps": [ ... ]}  
    """  
    if isinstance(steps_obj, list):  
        return steps_obj, None  
    if isinstance(steps_obj, dict) and isinstance(steps_obj.get("steps"), list):  
        return steps_obj["steps"], None  
    return None, "steps.json must be a list of steps or an object with a top-level 'steps' list"  
  
  
def _err(path: str, message: str, code: str = "LINT") -> dict:  
    return {"path": path, "code": code, "message": message}  
  
  
def validate_steps_data(  
    steps_obj: Any,  
    schema: Dict[str, Any],  
    *,  
    strict_unknown_fields: bool = False,  
) -> Dict[str, Any]:  
    """  
    Returns report:  
      {  
        "valid": bool,  
        "errors": [ {path, code, message}, ... ],  
        "warnings": [ {path, code, message}, ... ]  
      }  
    """  
    actions: Dict[str, ActionSchema] = schema.get("actions") or {}  
    errors: List[dict] = []  
    warnings: List[dict] = []  
  
    steps, err_msg = _ensure_steps_list(steps_obj)  
    if steps is None:  
        errors.append(_err("$", err_msg or "Invalid steps format", code="FORMAT"))  
        return {"valid": False, "errors": errors, "warnings": warnings}  
  
    def validate_step(step: Any, path: str) -> None:  
        if not isinstance(step, dict):  
            errors.append(_err(path, "Step must be an object/dict", code="STEP_TYPE"))  
            return  
  
        action = step.get("action")  
        if not isinstance(action, str) or not action.strip():  
            errors.append(_err(path, "Missing or invalid 'action' (must be string)", code="ACTION_MISSING"))  
            return  
  
        if action not in actions:  
            errors.append(_err(path + ".action", f"Unknown action '{action}' (not in schema)", code="ACTION_UNKNOWN"))  
            return  
  
        ainfo = actions[action]  
        required = set(ainfo.required_fields or [])  
        optional = set(ainfo.optional_fields or [])  
        allowed_fields = required | optional  
  
        # required fields present  
        for f in sorted(required):  
            if f not in step:  
                errors.append(_err(path, f"Missing required field '{f}' for action '{action}'", code="REQUIRED"))  
  
        # unknown fields  
        for k in step.keys():  
            if not isinstance(k, str):  
                warnings.append(_err(path, "Non-string key present in step object", code="KEY_TYPE"))  
                continue  
            if k in allowed_fields:  
                continue  
            msg = f"Unknown field '{k}' for action '{action}'"  
            if strict_unknown_fields:  
                errors.append(_err(path + f".{k}", msg, code="UNKNOWN_FIELD"))  
            else:  
                warnings.append(_err(path + f".{k}", msg, code="UNKNOWN_FIELD"))  
  
        # type checks + allowed values  
        for k, v in step.items():  
            if not isinstance(k, str):  
                continue  
            # Only validate declared fields to avoid false positives on unknown/meta fields  
            if k not in allowed_fields:  
                continue  
  
            expected_type = ainfo.field_types.get(k, "any")  
            if not _check_type(v, expected_type):  
                errors.append(  
                    _err(  
                        path + f".{k}",  
                        f"Field '{k}' expected type '{expected_type}' but got '{type(v).__name__}'",  
                        code="TYPE",  
                    )  
                )  
                continue  
  
            allowed_vals = ainfo.allowed_values.get(k)  
            if allowed_vals is not None:  
                # allow list-valued field: all items must be allowed  
                if isinstance(v, list):  
                    for idx, item in enumerate(v):  
                        if item not in allowed_vals:  
                            errors.append(  
                                _err(  
                                    path + f".{k}[{idx}]",  
                                    f"Value '{item}' not allowed for field '{k}' (allowed: {allowed_vals})",  
                                    code="ALLOWED",  
                                )  
                            )  
                else:  
                    if v not in allowed_vals:  
                        errors.append(  
                            _err(  
                                path + f".{k}",  
                                f"Value '{v}' not allowed for field '{k}' (allowed: {allowed_vals})",  
                                code="ALLOWED",  
                            )  
                        )  
  
        # validate nested steps lists for block-like actions (PIPE-2B)  
        for nk in NESTED_STEP_LIST_KEYS:  
            if nk in step and isinstance(step.get(nk), list):  
                for j, child in enumerate(step[nk]):  
                    validate_step(child, f"{path}.{nk}[{j}]")  
  
    for i, step in enumerate(steps):  
        validate_step(step, f"$[{i}]")  
  
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}  
  
  
def validate_steps_file(  
    steps_path: Path,  
    *,  
    schema_path: Optional[Path] = None,  
    repo_root: Optional[Path] = None,  
    strict_unknown_fields: bool = False,  
) -> Dict[str, Any]:  
    schema = load_steps_schema(schema_path=schema_path, repo_root=repo_root)  
    steps_obj = json.loads(_read_text(steps_path))  
    return validate_steps_data(steps_obj, schema, strict_unknown_fields=strict_unknown_fields)  
  
  
def format_report_text(report: Dict[str, Any]) -> str:  
    """  
    Human-readable summary (CLI helper uses JSON output, but this is handy for logs).  
    """  
    valid = bool(report.get("valid"))  
    errors = report.get("errors") or []  
    warnings = report.get("warnings") or []  
    lines: List[str] = []  
    lines.append("VALID" if valid else "INVALID")  
    lines.append(f"errors={len(errors)} warnings={len(warnings)}")  
    for e in errors:  
        lines.append(f"ERROR {e.get('path')}: {e.get('message')}")  
    for w in warnings:  
        lines.append(f"WARN  {w.get('path')}: {w.get('message')}")  
    return "\n".join(lines)  