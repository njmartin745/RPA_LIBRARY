# HEAL/heal_1a_patch_workflow.py  
"""  
HEAL-1A — Auto-fix Suggestion Applier (workflow patch generator)  
  
Pure utility:  
- No Selenium calls  
- File I/O allowed for reading workflow + writing patch outputs  
- Deterministic rule-based patching driven by REASON-1A diagnosis object  
  
Public API:  
  apply_diagnosis_patch(workflow_path, *, diagnosis, output_dir="workflows", selector_patch_path=None) -> dict  
"""  
  
from __future__ import annotations  
  
import json  
import re  
from copy import deepcopy  
from pathlib import Path  
from typing import Any, Dict, List, Optional, Tuple  
  
__all__ = [  
    "apply_diagnosis_patch",  
]  
  
  
# -------------------------  
# IO helpers  
# -------------------------  
def _read_text(p: Path) -> str:  
    return p.read_text(encoding="utf-8", errors="replace")  
  
  
def _write_text(p: Path, s: str) -> None:  
    p.parent.mkdir(parents=True, exist_ok=True)  
    p.write_text(s, encoding="utf-8")  
  
  
def _write_json(p: Path, obj: Any) -> None:  
    _write_text(p, json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n")  
  
  
def _load_workflow(path: Path) -> dict:  
    if not path.exists():  
        raise ValueError(f"workflow_path not found: {path}")  
  
    ext = path.suffix.lower().lstrip(".")  
    raw = _read_text(path)  
  
    if ext in {"json"}:  
        data = json.loads(raw)  
    elif ext in {"yml", "yaml"}:  
        # Optional YAML support (only if PyYAML is installed).  
        try:  
            import yaml  # type: ignore  
        except Exception as e:  
            raise ValueError(f"YAML workflow provided but PyYAML is not installed: {e}")  
        data = yaml.safe_load(raw)  
    else:  
        raise ValueError(f"Unsupported workflow file extension: .{ext} (supported: .json, .yml/.yaml if PyYAML installed)")  
  
    if not isinstance(data, dict):  
        raise ValueError("Workflow must be a JSON/YAML object at top level")  
    if "steps" not in data or not isinstance(data["steps"], list):  
        raise ValueError("Workflow must contain a top-level 'steps' list")  
  
    return data  
  
  
def _sanitize_name(s: str) -> str:  
    s2 = (s or "").strip()  
    s2 = s2.replace(" ", "_")  
    s2 = re.sub(r"[^A-Za-z0-9_\-]+", "", s2)  
    return s2 or "workflow"  
  
  
def _workflow_name(workflow: dict, fallback_path: Path) -> str:  
    for k in ("name", "workflow_name", "id"):  
        v = workflow.get(k)  
        if isinstance(v, str) and v.strip():  
            return _sanitize_name(v)  
    return _sanitize_name(fallback_path.stem)  
  
  
def _infer_step_index(diagnosis: dict, steps_len: int) -> Optional[int]:  
    # Prefer explicit fields if present  
    for k in ("step_index", "failing_step_index", "index"):  
        v = diagnosis.get(k)  
        if isinstance(v, int) and 0 <= v < steps_len:  
            return v  
    # Then REASON-1A notes.inputs_used.step_index  
    notes = diagnosis.get("notes")  
    if isinstance(notes, dict):  
        iu = notes.get("inputs_used")  
        if isinstance(iu, dict):  
            v = iu.get("step_index")  
            if isinstance(v, int) and 0 <= v < steps_len:  
                return v  
    return None  
  
  
def _step_action(step: dict) -> str:  
    a = step.get("action")  
    return a.strip() if isinstance(a, str) else ""  
  
  
def _find_action_with_substring(steps: List[dict], needle: str) -> Optional[str]:  
    needle_l = needle.lower()  
    for s in steps:  
        if not isinstance(s, dict):  
            continue  
        a = _step_action(s)  
        if a and needle_l in a.lower():  
            return a  
    return None  
  
  
def _load_selector_patch_map(selector_patch_path: Optional[Path]) -> Dict[str, str]:  
    """  
    Minimal supported format (deterministic; no guessing):  
      {  
        "selector_ref_patches": {  
          "old.path": "new.path"  
        }  
      }  
    Also accepts top-level "patches" with same shape.  
    """  
    if selector_patch_path is None:  
        return {}  
    p = selector_patch_path  
    if not p.exists():  
        return {}  
    try:  
        obj = json.loads(_read_text(p))  
    except Exception:  
        return {}  
    if not isinstance(obj, dict):  
        return {}  
    m = obj.get("selector_ref_patches") or obj.get("patches") or {}  
    if not isinstance(m, dict):  
        return {}  
    out: Dict[str, str] = {}  
    for k, v in m.items():  
        if isinstance(k, str) and isinstance(v, str) and k.strip() and v.strip():  
            out[k.strip()] = v.strip()  
    return out  
  
  
# -------------------------  
# Patch rules  
# -------------------------  
def _patch_timeout(step: dict, edits: List[str]) -> None:  
    if "timeout" in step and isinstance(step["timeout"], (int, float)):  
        old = float(step["timeout"])  
        if old < 0:  
            old = 0.0  
        if old >= 60:  
            new = old  # do not reduce; cap only upward  
        else:  
            new = min(60.0, max(old, 1.0) * 1.5)  
        step["timeout"] = int(round(new))  
        edits.append(f"Adjusted timeout from {int(round(old))} -> {step['timeout']} (cap=60, +50% if under cap).")  
    else:  
        step["timeout"] = 20  
        edits.append("Injected timeout=20 (default).")  
  
  
def _insert_step(steps: List[dict], idx: int, new_step: dict) -> None:  
    if idx < 0:  
        idx = 0  
    if idx > len(steps):  
        idx = len(steps)  
    steps.insert(idx, new_step)  
  
  
def _apply_patch_rules(  
    workflow: dict,  
    *,  
    diagnosis: dict,  
    selector_patch_map: Dict[str, str],  
) -> Tuple[dict, List[dict], List[str]]:  
    patched = deepcopy(workflow)  
    steps = patched["steps"]  
    if not isinstance(steps, list):  
        raise ValueError("workflow['steps'] must be a list")  
  
    steps_dicts: List[dict] = [s for s in steps if isinstance(s, dict)]  
    # Keep original list but enforce dicts for patching  
    if len(steps_dicts) != len(steps):  
        raise ValueError("All steps must be dict objects for patching")  
  
    category = diagnosis.get("category")  
    if not isinstance(category, str) or not category.strip():  
        category = "UNKNOWN"  
    category = category.strip().upper()  
  
    step_index = _infer_step_index(diagnosis, len(steps_dicts))  
  
    edits: List[dict] = []  
    todos: List[str] = []  
  
    def add_edit(where: str, desc: str) -> None:  
        edits.append({"where": where, "edit": desc})  
  
    # --- TIMEOUT ---  
    if category == "TIMEOUT":  
        if step_index is None:  
            # Deterministic fallback: patch first step that already has timeout, else last step  
            idx = None  
            for i, s in enumerate(steps_dicts):  
                if "timeout" in s:  
                    idx = i  
                    break  
            if idx is None:  
                idx = max(0, len(steps_dicts) - 1)  
            step_index_local = idx  
            todos.append("No step_index provided in diagnosis; applied timeout patch to a best-effort step.")  
        else:  
            step_index_local = step_index  
  
        s = steps_dicts[step_index_local]  
        e: List[str] = []  
        _patch_timeout(s, e)  
        add_edit(f"step[{step_index_local}]", f"TIMEOUT patch: {', '.join(e)}")  
  
    # --- SELECTOR_NOT_FOUND ---  
    elif category == "SELECTOR_NOT_FOUND":  
        if step_index is None:  
            todos.append("SELECTOR_NOT_FOUND: missing step_index; no selector_ref could be patched deterministically.")  
        else:  
            s = steps_dicts[step_index]  
            sel_ref = s.get("selector_ref")  
            if isinstance(sel_ref, str) and sel_ref.strip():  
                new_ref = selector_patch_map.get(sel_ref.strip())  
                if new_ref:  
                    s["selector_ref"] = new_ref  
                    add_edit(f"step[{step_index}]", f"Replaced selector_ref '{sel_ref}' -> '{new_ref}' using selector_patch_path map.")  
                else:  
                    todos.append(  
                        f"SELECTOR_NOT_FOUND: selector_ref='{sel_ref}' has no mapping in selector_patch_path. "  
                        "Recapture selector (CAPTURE-1A) and update registry, then supply a mapping."  
                    )  
            else:  
                todos.append(  
                    "SELECTOR_NOT_FOUND: failing step has no selector_ref field. "  
                    "Do not guess raw selectors; update workflow to use selector_ref or recapture."  
                )  
  
    # --- IFRAME_CONTEXT ---  
    elif category == "IFRAME_CONTEXT":  
        if step_index is None:  
            todos.append("IFRAME_CONTEXT: missing step_index; cannot insert a frame switch deterministically.")  
        else:  
            # If workflow already has a frame-switch action somewhere, reuse its name; otherwise insert TODO step.  
            frame_action = _find_action_with_substring(steps_dicts, "switch_to_frame")  
            insert_idx = step_index  
  
            # Avoid inserting if immediately preceded by a frame switch action already  
            if insert_idx - 1 >= 0:  
                prev = steps_dicts[insert_idx - 1]  
                if "switch_to_frame" in _step_action(prev).lower():  
                    todos.append("IFRAME_CONTEXT: previous step already appears to switch frames; verify correct iframe and switching back.")  
                    frame_action = None  
  
            if frame_action:  
                new_step = {  
                    "action": frame_action,  
                    "frame": 0,  
                    "meta": {"heal_note": "Inserted by HEAL-1A before failing step; verify correct frame index/name."},  
                }  
                _insert_step(steps_dicts, insert_idx, new_step)  
                patched["steps"] = steps_dicts  
                add_edit(f"insert@{insert_idx}", f"Inserted guarded frame switch step using action='{frame_action}'.")  
            else:  
                new_step = {  
                    "action": "TODO_IFRAME_SWITCH",  
                    "meta": {  
                        "heal_note": "HEAL-1A could not confirm a supported frame-switch action. "  
                        "Replace this TODO with your schema-supported switch_to_frame step."  
                    },  
                }  
                _insert_step(steps_dicts, insert_idx, new_step)  
                patched["steps"] = steps_dicts  
                add_edit(f"insert@{insert_idx}", "Inserted TODO_IFRAME_SWITCH placeholder step before failing step.")  
  
    # --- DOWNLOAD ---  
    elif category == "DOWNLOAD":  
        # Only insert if a download_wait action is already known in this workflow; otherwise TODO note only.  
        if step_index is None:  
            todos.append("DOWNLOAD: missing step_index; cannot target insertion deterministically.")  
        else:  
            wait_action = _find_action_with_substring(steps_dicts, "download_wait")  
            failing_action = _step_action(steps_dicts[step_index]).lower()  
            looks_like_validation = ("val." in failing_action) or ("validate" in failing_action) or ("file" in failing_action)  
  
            if wait_action and looks_like_validation:  
                new_step = {  
                    "action": wait_action,  
                    "timeout": 30,  
                    "meta": {"heal_note": "Inserted by HEAL-1A before validation to wait for download completion."},  
                }  
                _insert_step(steps_dicts, step_index, new_step)  
                patched["steps"] = steps_dicts  
                add_edit(f"insert@{step_index}", f"Inserted download_wait step using action='{wait_action}' before validation.")  
            else:  
                todos.append(  
                    "DOWNLOAD: Could not safely insert a download_wait step (no known 'download_wait' action found in workflow, "  
                    "or failing step did not look like a validation step). Add a schema-supported download wait before validation."  
                )  
  
    # --- CLICK_INTERCEPTED / STALE_ELEMENT ---  
    elif category in {"CLICK_INTERCEPTED", "STALE_ELEMENT"}:  
        if step_index is None:  
            todos.append(f"{category}: missing step_index; cannot insert guard deterministically.")  
        else:  
            # Only insert a guard if a guard-like action already exists in workflow; else TODO note only.  
            guard_action = _find_action_with_substring(steps_dicts, "wait_clickable") or _find_action_with_substring(steps_dicts, "guard")  
            if guard_action:  
                new_step = {  
                    "action": guard_action,  
                    "selector_ref": steps_dicts[step_index].get("selector_ref"),  
                    "timeout": 10,  
                    "meta": {"heal_note": f"Inserted by HEAL-1A before step[{step_index}] for {category}."},  
                }  
                _insert_step(steps_dicts, step_index, new_step)  
                patched["steps"] = steps_dicts  
                add_edit(f"insert@{step_index}", f"Inserted guard step using action='{guard_action}' before failing step.")  
            else:  
                todos.append(  
                    f"{category}: No existing guard/wait_clickable action found in workflow to reuse. "  
                    "Add a schema-supported guard step (e.g., wait until clickable) before click, or add retries per your schema."  
                )  
  
    else:  
        todos.append(f"No patch rules implemented for category '{category}' (safe fallback).")  
  
    return patched, edits, todos  
  
  
def _render_patch_md(  
    *,  
    original_path: Path,  
    workflow_name: str,  
    diagnosis: dict,  
    edits: List[dict],  
    todos: List[str],  
    patch_json_path: Path,  
) -> str:  
    cat = diagnosis.get("category")  
    conf = diagnosis.get("confidence")  
    if not isinstance(cat, str):  
        cat = "UNKNOWN"  
    if not isinstance(conf, (int, float)):  
        conf = "n/a"  
  
    lines: List[str] = []  
    lines.append(f"# Workflow Patch Report — {workflow_name}")  
    lines.append("")  
    lines.append("## Inputs")  
    lines.append(f"- Original workflow: `{original_path.as_posix()}`")  
    lines.append(f"- Diagnosis category: `{str(cat)}`")  
    lines.append(f"- Diagnosis confidence: `{conf}`")  
    lines.append("")  
    lines.append("## Outputs")  
    lines.append(f"- Patched workflow JSON: `{patch_json_path.as_posix()}`")  
    lines.append("")  
    lines.append("## Applied edits")  
    if edits:  
        for i, e in enumerate(edits, start=1):  
            where = e.get("where", "?")  
            desc = e.get("edit", "")  
            lines.append(f"{i}. **{where}** — {desc}")  
    else:  
        lines.append("- (none)")  
    lines.append("")  
    lines.append("## TODOs / Missing info")  
    if todos:  
        for t in todos:  
            lines.append(f"- {t}")  
    else:  
        lines.append("- (none)")  
    lines.append("")  
    lines.append("## Rollback")  
    lines.append("- To rollback, use the original workflow file unchanged.")  
    lines.append("- This patch generator does not modify runtime modules; it only writes patch drafts.")  
    lines.append("")  
    return "\n".join(lines)  
  
  
def apply_diagnosis_patch(  
    workflow_path: str | Path,  
    *,  
    diagnosis: dict,  
    output_dir: str | Path = "workflows",  
    selector_patch_path: str | Path | None = None,  
) -> dict:  
    if not isinstance(diagnosis, dict):  
        raise ValueError("diagnosis must be a dict")  
  
    wf_path = Path(workflow_path)  
    out_dir = Path(output_dir)  
    sel_patch_p = Path(selector_patch_path) if selector_patch_path is not None else None  
  
    workflow = _load_workflow(wf_path)  
    wf_name = _workflow_name(workflow, wf_path)  
  
    selector_patch_map = _load_selector_patch_map(sel_patch_p)  
  
    patched, edits, todos = _apply_patch_rules(workflow, diagnosis=diagnosis, selector_patch_map=selector_patch_map)  
  
    patch_json_path = out_dir / f"{wf_name}__patch.json"  
    patch_md_path = out_dir / f"{wf_name}__patch.md"  
  
    _write_json(patch_json_path, patched)  
    md = _render_patch_md(  
        original_path=wf_path,  
        workflow_name=wf_name,  
        diagnosis=diagnosis,  
        edits=edits,  
        todos=todos,  
        patch_json_path=patch_json_path,  
    )  
    _write_text(patch_md_path, md)  
  
    return {  
        "workflow_name": wf_name,  
        "original_path": str(wf_path),  
        "patch_json_path": str(patch_json_path),  
        "patch_md_path": str(patch_md_path),  
        "category": str(diagnosis.get("category") or "UNKNOWN"),  
        "confidence": float(diagnosis.get("confidence") or 0.0) if isinstance(diagnosis.get("confidence"), (int, float)) else None,  
        "edits": edits,  
        "todos": todos,  
    }  