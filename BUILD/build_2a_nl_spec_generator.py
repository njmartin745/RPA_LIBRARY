"""  
BUILD-2A — Natural Language → Build Spec Generator  
  
Goal:  
- Accept plain-English process descriptions  
- Convert them into a structured spec that can be consumed by BUILD-1A (or passed  
  through as workflow steps directly)  
- Respect the supported STEP_GRAMMAR (no Selenium execution here)  
  
Notes:  
- This module is deterministic and rule-based (no LLM calls, no randomness).  
- It prefers `selector_ref` and emits placeholder selector hints for later capture.  
- IMPORTANT: Final emitted actions are filtered to what exists in REGISTRY, but  
  action names are normalized to canonical STEP_GRAMMAR vocabulary.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
import json  
from pathlib import Path  
import re  
from typing import Dict, List, Optional, Sequence, Set, Tuple  
  
from BUILD.build_2a_repeat_support import (  
    normalize_and_filter_steps_keep_repeat,  
    validate_steps_allow_repeat,  
)  
  
__all__ = [  
    "SUPPORTED_ACTIONS",  
    "nl_to_build_spec",  
    "validate_generated_steps",  
]  
  
  
# Internal scaffold vocabulary (may include actions that are later flattened/dropped)  
SUPPORTED_ACTIONS: Tuple[str, ...] = (  
    "open",  
    "click_selector",  
    "type_selector_secret",  
    "wait_for_selector",  
    "exec_js",  
    "exec_js_file",  
    "repeat",  
    "log",  
    "switch_back_to_main_tab",  
)  
  
# REQUIRED normalization map (aliases -> canonical)  
ACTION_MAP: Dict[str, str] = {  
    "click": "click_selector",  
    "wait_for_element": "wait_for_selector",  
    "javascript": "exec_js",  
}  
  
_VAR_RE = re.compile(r"\$\{[A-Z0-9_]+\}")  
_URL_RE = re.compile(r"(https?://[^\s]+)", re.IGNORECASE)  
_WS_RE = re.compile(r"\s+")  
  
# Simple quoted label matcher: click "Export Excel"  
_QUOTED_RE = re.compile(r"""["']([^"']+)["']""")  
  
  
@dataclass(frozen=True)  
class _SelectorHint:  
    selector_ref: str  
    hint: str  
  
  
def _norm_text(s: str) -> str:  
    return _WS_RE.sub(" ", (s or "").strip())  
  
  
def _split_sentences(text: str) -> List[str]:  
    text = _norm_text(text)  
    if not text:  
        return []  
    parts = re.split(r"[.\n;]+", text)  
    return [p.strip() for p in parts if p.strip()]  
  
  
def _extract_vars(text: str) -> List[str]:  
    return sorted(set(_VAR_RE.findall(text or "")))  
  
  
def _find_url_or_url_var(text: str) -> Optional[str]:  
    text = text or ""  
    m = _URL_RE.search(text)  
    if m:  
        return m.group(1)  
    for v in _extract_vars(text):  
        if v == "${URL}":  
            return v  
    return None  
  
  
def _slug_to_selector_ref(label: str) -> str:  
    label = (label or "").strip()  
    if not label:  
        return "UNKNOWN_TARGET"  
    up = re.sub(r"[^A-Za-z0-9]+", "_", label).strip("_").upper()  
    return up or "UNKNOWN_TARGET"  
  
  
def _mk_wait(selector_ref: str, name: Optional[str] = None) -> Dict:  
    step = {"action": "wait_for_selector", "selector_ref": selector_ref}  
    if name:  
        step["name"] = name  
    return step  
  
  
def _mk_click(selector_ref: str, name: Optional[str] = None) -> Dict:  
    step = {"action": "click_selector", "selector_ref": selector_ref}  
    if name:  
        step["name"] = name  
    return step  
  
  
def _mk_type_secret(selector_ref: str, secret: str, name: Optional[str] = None) -> Dict:  
    step = {  
        "action": "type_selector_secret",  
        "selector_ref": selector_ref,  
        "secret": secret,  
    }  
    if name:  
        step["name"] = name  
    return step  
  
  
def _extract_click_label(sentence: str) -> Optional[str]:  
    qm = _QUOTED_RE.search(sentence)  
    if qm:  
        return qm.group(1).strip()  
  
    m = re.search(r"\bclick\b\s+(.*)$", sentence, re.IGNORECASE)  
    if m:  
        raw = m.group(1).strip()  
        raw = re.sub(r"^(on|the)\s+", "", raw, flags=re.IGNORECASE).strip()  
        raw = re.split(r"\b(to|then|and)\b", raw, maxsplit=1, flags=re.IGNORECASE)[0].strip()  
        return raw or None  
  
    return None  
  
  
def _extract_wait_label(sentence: str) -> Optional[str]:  
    m = re.search(r"\bwait\s+for\b\s+(.*)$", sentence, re.IGNORECASE)  
    if not m:  
        return None  
    raw = m.group(1).strip()  
    raw = re.sub(r"^(the)\s+", "", raw, flags=re.IGNORECASE).strip()  
    raw = re.split(r"\b(to|then|and)\b", raw, maxsplit=1, flags=re.IGNORECASE)[0].strip()  
    return raw or None  
  
  
def _looks_like_login(sentence: str) -> bool:  
    return bool(re.search(r"\b(log\s*in|login|sign\s*in)\b", sentence, re.IGNORECASE))  
  
  
def _looks_like_download(sentence: str) -> bool:  
    return bool(re.search(r"\b(download|export)\b", sentence, re.IGNORECASE))  
  
  
def _mk_login_repeat_block(vars_in_text: Sequence[str]) -> Tuple[Dict, List[_SelectorHint]]:  
    """  
    Scaffolded login block.  
    NOTE: inner `log` steps are removed from final output; `repeat` is preserved.  
    """  
    hints: List[_SelectorHint] = []  
    username_var = "${USERNAME}" if "${USERNAME}" in vars_in_text else "${USERNAME}"  
    password_var = "${PASSWORD}" if "${PASSWORD}" in vars_in_text else "${PASSWORD}"  
  
    u_ref = "LOGIN_USERNAME"  
    p_ref = "LOGIN_PASSWORD"  
    s_ref = "LOGIN_SUBMIT"  
    post_ref = "POST_LOGIN_LANDMARK"  
  
    hints.extend(  
        [  
            _SelectorHint(u_ref, "Username/email input on login form"),  
            _SelectorHint(p_ref, "Password input on login form"),  
            _SelectorHint(s_ref, "Login/Sign in/Submit button"),  
            _SelectorHint(post_ref, "Any element that appears only after successful login"),  
        ]  
    )  
  
    steps = [  
        {"action": "log", "message": "Login (generated)"},  
        _mk_wait(u_ref, "Wait for username"),  
        _mk_type_secret(u_ref, username_var, "Enter username"),  
        _mk_wait(p_ref, "Wait for password"),  
        _mk_type_secret(p_ref, password_var, "Enter password"),  
        _mk_wait(s_ref, "Wait for submit"),  
        _mk_click(s_ref, "Submit login"),  
        _mk_wait(post_ref, "Wait for post-login landmark"),  
    ]  
  
    block = {  
        "action": "repeat",  
        "times": 1,  
        "name": "Login (guarded placeholder)",  
        "steps": steps,  
    }  
    return block, hints  
  
  
def _find_registry_path(start: Path) -> Path:  
    s = start  
    if s.is_file():  
        s = s.parent  
    for cand in [s, *s.parents]:  
        p = cand / "REGISTRY" / "action_registry.json"  
        if p.exists() and p.is_file():  
            return p  
    raise FileNotFoundError("Could not find REGISTRY/action_registry.json (walked parents).")  
  
  
def _load_allowed_actions_from_registry() -> Set[str]:  
    reg_path = _find_registry_path(Path(__file__).resolve())  
    obj = json.loads(reg_path.read_text(encoding="utf-8", errors="replace"))  
    actions = obj.get("actions")  
    if not isinstance(actions, list):  
        raise ValueError("REGISTRY/action_registry.json missing 'actions' list")  
    out: Set[str] = set()  
    for a in actions:  
        if isinstance(a, dict):  
            name = a.get("action")  
            if isinstance(name, str) and name.strip():  
                out.add(name.strip())  
    if not out:  
        raise ValueError("REGISTRY/action_registry.json contained zero action names")  
    return out  
  
  
def _normalize_action(action: str) -> str:  
    return ACTION_MAP.get(action, action)  
  
  
def _normalized_allowed_actions(allowed_raw: Set[str]) -> Set[str]:  
    # Normalize allowed action names using the same alias->canonical mapping.  
    return {ACTION_MAP.get(a, a) for a in allowed_raw}  
  
  
def _normalize_and_filter_steps_to_registry(steps: Sequence[Dict], allowed_raw: Set[str]) -> List[Dict]:  
    """  
    Normalize + filter steps while preserving `repeat` blocks.  
    (Delegates to BUILD-2A repeat support module.)  
    """  
    return normalize_and_filter_steps_keep_repeat(steps, allowed_raw, action_map=ACTION_MAP)  
  
  
def nl_to_build_spec(description: str, *, workflow_name: str = "NL Generated Workflow") -> Dict:  
    description = _norm_text(description)  
    sentences = _split_sentences(description)  
    vars_found = _extract_vars(description)  
  
    selector_hints: Dict[str, _SelectorHint] = {}  
    steps: List[Dict] = []  
  
    url = _find_url_or_url_var(description)  
    if url:  
        steps.append({"action": "open", "url": url})  
    elif re.search(r"\b(open|go\s+to|navigate)\b", description, re.IGNORECASE):  
        if "${URL}" not in vars_found:  
            vars_found = sorted(set(vars_found + ["${URL}"]))  
        steps.append({"action": "open", "url": "${URL}"})  
  
    if any(_looks_like_login(s) for s in sentences):  
        login_block, hints = _mk_login_repeat_block(vars_found)  
        steps.append(login_block)  
        for h in hints:  
            selector_hints[h.selector_ref] = h  
  
    for s in sentences:  
        s_norm = s.strip()  
        if not s_norm:  
            continue  
  
        if _looks_like_login(s_norm):  
            continue  
        if re.search(r"\b(open|go\s+to|navigate)\b", s_norm, re.IGNORECASE) and _find_url_or_url_var(  
            s_norm  
        ):  
            continue  
  
        wait_label = _extract_wait_label(s_norm)  
        if wait_label:  
            ref = _slug_to_selector_ref(wait_label)  
            steps.append(_mk_wait(ref, f"Wait for {wait_label}"))  
            selector_hints.setdefault(ref, _SelectorHint(ref, f"UI element: {wait_label}"))  
            continue  
  
        click_label = _extract_click_label(s_norm)  
        if click_label:  
            ref = _slug_to_selector_ref(click_label)  
            steps.append(_mk_click(ref, f"Click {click_label}"))  
            selector_hints.setdefault(ref, _SelectorHint(ref, f"Clickable element: {click_label}"))  
            continue  
  
        if _looks_like_download(s_norm):  
            ref = "EXPORT_DOWNLOAD"  
            steps.append(_mk_click(ref, "Click export/download control (placeholder)"))  
            selector_hints.setdefault(  
                ref, _SelectorHint(ref, "Export/Download control (e.g., 'Export Excel')")  
            )  
            continue  
  
        if re.search(r"\b(exec(ute)?\s+js|run\s+javascript)\b", s_norm, re.IGNORECASE):  
            steps.append(  
                {  
                    "action": "exec_js",  
                    "name": "Exec JS (placeholder)",  
                    "script": "return { ok: true, note: 'TODO: fill script' };",  
                }  
            )  
            continue  
  
        if re.search(r"\b(exec(ute)?\s+js\s+file|run\s+script\s+file)\b", s_norm, re.IGNORECASE):  
            steps.append(  
                {  
                    "action": "exec_js_file",  
                    "name": "Exec JS file (placeholder)",  
                    "path": "scripts/TODO.js",  
                }  
            )  
            continue  
  
        continue  
  
    hints_out = [  
        {"selector_ref": h.selector_ref, "hint": h.hint}  
        for h in sorted(selector_hints.values(), key=lambda x: x.selector_ref)  
    ]  
  
    allowed_raw = _load_allowed_actions_from_registry()  
  
    # REQUIRED: apply normalization mapping BEFORE validation and before returning steps  
    steps_out = _normalize_and_filter_steps_to_registry(steps, allowed_raw)  
  
    spec = {  
        "spec_version": "BUILD-2A",  
        "workflow_name": workflow_name,  
        "vars": sorted(set(vars_found)),  
        "selector_hints": hints_out,  
        "steps": steps_out,  
        "workflow": {"name": workflow_name, "steps": steps_out},  
    }  
  
    validate_generated_steps(steps_out)  
    return spec  
  
  
def validate_generated_steps(steps: Sequence[Dict]) -> None:  
    if steps is None:  
        raise ValueError("steps is None")  
  
    allowed_raw = _load_allowed_actions_from_registry()  
    validate_steps_allow_repeat(steps, allowed_raw, action_map=ACTION_MAP)  