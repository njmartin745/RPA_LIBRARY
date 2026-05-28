from __future__ import annotations  
  
from typing import Any  
  
__all__ = [  
    "default_questions",  
    "run_intake",  
    "build_spec_from_answers",  
]  
  
_DETERMINISTIC_CREATED_AT_UTC = "1970-01-01T00:00:00Z"  
  
  
def default_questions() -> list[dict]:  
    """  
    Canonical BUILD-1B intake questions.  
  
    Each question dict is intentionally simple and terminal-friendly:  
      - id: stable key in answers dict  
      - prompt: user-facing prompt  
      - type: "str" | "bool" | "choice" | "text"  
      - required: bool  
      - default: Any  
      - choices: list[str] (for type == "choice")  
    """  
    return [  
        {  
            "id": "name",  
            "prompt": "Workflow name (filename-safe)",  
            "type": "str",  
            "required": True,  
            "default": "",  
        },  
        {  
            "id": "intent",  
            "prompt": "Workflow intent (short description)",  
            "type": "text",  
            "required": True,  
            "default": "",  
        },  
        {  
            "id": "entry_url",  
            "prompt": "Entry URL",  
            "type": "str",  
            "required": True,  
            "default": "",  
        },  
        {  
            "id": "headless",  
            "prompt": "Run headless by default?",  
            "type": "bool",  
            "required": False,  
            "default": True,  
        },  
        {  
            "id": "requires_login",  
            "prompt": "Requires login?",  
            "type": "bool",  
            "required": False,  
            "default": False,  
        },  
        {  
            "id": "input_mode",  
            "prompt": "Input mode",  
            "type": "choice",  
            "required": False,  
            "default": "none",  
            "choices": ["none", "excel", "csv"],  
        },  
        {  
            "id": "selectors_known",  
            "prompt": "Are selectors already known and registered (data/selectors.json)?",  
            "type": "bool",  
            "required": False,  
            "default": False,  
        },  
        {  
            "id": "downloads_expected",  
            "prompt": "Are downloads expected?",  
            "type": "bool",  
            "required": False,  
            "default": False,  
        },  
        {  
            "id": "download_dir",  
            "prompt": "Download directory (relative path)",  
            "type": "str",  
            "required": False,  
            "default": "downloads",  
        },  
        {  
            "id": "notes",  
            "prompt": "Notes / assumptions (free text)",  
            "type": "text",  
            "required": False,  
            "default": "",  
        },  
    ]  
  
  
def _coerce_bool(v: Any, *, default: bool | None = None) -> bool | None:  
    if isinstance(v, bool):  
        return v  
    if v is None:  
        return default  
    if isinstance(v, (int, float)):  
        return bool(v)  
    if isinstance(v, str):  
        s = v.strip().lower()  
        if s in ("y", "yes", "true", "t", "1", "on"):  
            return True  
        if s in ("n", "no", "false", "f", "0", "off"):  
            return False  
        if s == "" and default is not None:  
            return default  
    return default  
  
  
def _coerce_choice(v: Any, choices: list[str], *, default: str) -> str:  
    if isinstance(v, str):  
        s = v.strip()  
        if not s:  
            return default  
        # accept case-insensitive matches  
        for c in choices:  
            if s.lower() == c.lower():  
                return c  
    return default  
  
  
def _normalize_answers(raw: dict | None) -> dict:  
    raw = raw if isinstance(raw, dict) else {}  
    out: dict[str, Any] = {}  
  
    for q in default_questions():  
        qid = q["id"]  
        qtype = q["type"]  
        default = q.get("default")  
  
        v = raw.get(qid, default)  
  
        if qtype in ("str", "text"):  
            out[qid] = "" if v is None else str(v)  
        elif qtype == "bool":  
            out[qid] = _coerce_bool(v, default=bool(default)) if default is not None else _coerce_bool(v, default=None)  
            if out[qid] is None:  
                out[qid] = bool(default)  
        elif qtype == "choice":  
            out[qid] = _coerce_choice(v, list(q.get("choices", [])), default=str(default))  
        else:  
            out[qid] = v  
  
    # Basic cleanup  
    out["name"] = out.get("name", "").strip()  
    out["entry_url"] = out.get("entry_url", "").strip()  
    out["intent"] = out.get("intent", "").strip()  
  
    # Notes: keep as a single string here; BUILD-1A expects list[str] in spec  
    out["notes"] = out.get("notes", "").strip()  
  
    return out  
  
  
def _validate_required_answers(ans: dict) -> list[str]:  
    errors: list[str] = []  
    for q in default_questions():  
        if not q.get("required"):  
            continue  
        qid = q["id"]  
        v = ans.get(qid)  
        if isinstance(v, str) and not v.strip():  
            errors.append(f"Missing required answer: {qid}")  
        elif v is None:  
            errors.append(f"Missing required answer: {qid}")  
  
    # Filename-safe-ish on Windows  
    name = ans.get("name", "")  
    if name and any(c in name for c in r'\/:*?"<>|'):  
        errors.append(f"Invalid workflow name for filename on Windows: {name!r}")  
  
    # Input mode allowed values  
    if ans.get("input_mode") not in ("none", "excel", "csv"):  
        errors.append("Invalid input_mode (must be one of: none | excel | csv)")  
  
    return errors  
  
  
def run_intake(*, answers: dict | None = None, interactive: bool = False) -> dict:  
    """  
    Collect + validate answers. If interactive=True, prompts via input().  
  
    Returns a normalized answers dict.  
    Raises ValueError if required answers are missing/invalid.  
    """  
    normalized = _normalize_answers(answers)  
  
    if interactive:  
        for q in default_questions():  
            qid = q["id"]  
            prompt = q["prompt"]  
            qtype = q["type"]  
            default = q.get("default")  
            choices = q.get("choices")  
  
            current = normalized.get(qid, default)  
            suffix = ""  
            if qtype == "choice" and isinstance(choices, list):  
                suffix = f" ({'/'.join(choices)})"  
            if default not in (None, ""):  
                suffix = f"{suffix} [default: {default}]"  
  
            raw = input(f"{prompt}{suffix}: ").strip()  
  
            if raw == "":  
                # keep current/default  
                continue  
  
            if qtype in ("str", "text"):  
                normalized[qid] = raw  
            elif qtype == "bool":  
                normalized[qid] = bool(_coerce_bool(raw, default=bool(default)))  
            elif qtype == "choice":  
                normalized[qid] = _coerce_choice(raw, list(choices or []), default=str(default))  
            else:  
                normalized[qid] = raw  
  
        normalized = _normalize_answers(normalized)  
  
    errors = _validate_required_answers(normalized)  
    if errors:  
        raise ValueError("BUILD-1B intake validation failed: " + "; ".join(errors))  
  
    return normalized  
  
  
def build_spec_from_answers(answers: dict) -> dict:  
    """  
    Transform questionnaire answers into a BUILD-1A compatible spec.  
    Adds TODO placeholders in notes where details are unknown.  
    Deterministic output (no runtime timestamps).  
    """  
    warnings: list[str] = []  
    todos: list[str] = []  
  
    try:  
        ans = run_intake(answers=answers, interactive=False)  
    except ValueError as e:  
        return {  
            "ok": False,  
            "answers": _normalize_answers(answers),  
            "spec": {},  
            "warnings": [],  
            "todos": [],  
            "errors": [str(e)],  
        }  
  
    # Minimal deterministic step list: always start with entry navigation.  
    steps = []  
    if ans.get("entry_url"):  
        steps.append({"action": "get", "url": ans["entry_url"]})  
    else:  
        todos.append("Provide entry_url so the workflow can start with a GET step.")  
  
    if ans.get("requires_login"):  
        todos.append("Login required: add AUTH steps (or navigation + credential entry + submit) once selectors are known.")  
  
    if not ans.get("selectors_known"):  
        todos.append("Selectors unknown: create selector refs in data/selectors.json and reference them via selector_ref in steps.")  
  
    input_mode = ans.get("input_mode", "none")  
    if input_mode in ("excel", "csv"):  
        todos.append(f"Input mode {input_mode!r}: wire INPUT/LOOP via PIPE configuration (do not hardcode loops here).")  
  
    downloads_expected = bool(ans.get("downloads_expected"))  
    outputs: dict[str, Any] = {"downloads": downloads_expected}  
    if downloads_expected:  
        outputs["download_dir"] = ans.get("download_dir") or "downloads"  
        todos.append("Downloads expected: add download_wait / wait_for_download steps once download behavior is defined.")  
  
    notes_list: list[str] = []  
    if ans.get("notes"):  
        notes_list.append(str(ans["notes"]).strip())  
  
    # Attach TODOs into notes for visibility (BUILD-1A will also keep them if passed as notes)  
    for t in todos:  
        notes_list.append(f"TODO: {t}")  
  
    spec = {  
        "name": ans["name"],  
        "intent": ans.get("intent", ""),  
        "entry_url": ans.get("entry_url", ""),  
        "headless": bool(ans.get("headless", True)),  
        "inputs": {"mode": input_mode},  
        "steps": steps,  
        "outputs": outputs,  
        "notes": notes_list,  
        # keep deterministic  
        "created_at_utc": _DETERMINISTIC_CREATED_AT_UTC,  
    }  
  
    # Very light warnings (non-fatal)  
    if not steps:  
        warnings.append("No steps generated (missing entry_url).")  
  
    return {  
        "ok": True,  
        "answers": ans,  
        "spec": spec,  
        "warnings": warnings,  
        "todos": todos,  
    }  