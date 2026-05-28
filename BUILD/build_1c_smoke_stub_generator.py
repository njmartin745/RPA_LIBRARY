from __future__ import annotations  
  
import json  
import os  
from pathlib import Path  
from typing import Any  
  
__all__ = [  
    "generate_smoke_stub",  
    "load_workflow_metadata",  
]  
  
  
def _read_json(path: Path) -> Any:  
    return json.loads(path.read_text(encoding="utf-8"))  
  
  
def load_workflow_metadata(workflow_path: str | Path) -> dict:  
    """  
    Load a BUILD-1A workflow JSON and return metadata useful for stub generation.  
    """  
    wp = Path(workflow_path)  
    obj = _read_json(wp)  
    if not isinstance(obj, dict):  
        raise ValueError(f"Workflow JSON must be an object: {workflow_path}")  
  
    name = obj.get("name")  
    if not isinstance(name, str) or not name.strip():  
        raise ValueError(f"Workflow missing required string field 'name': {workflow_path}")  
  
    metadata = obj.get("metadata")  
    if not isinstance(metadata, dict):  
        metadata = {}  
  
    steps = obj.get("steps")  
    if not isinstance(steps, list):  
        steps = []  
  
    return {  
        "workflow_path": str(wp),  
        "workflow_name": name.strip(),  
        "metadata": metadata,  
        "step_count": len(steps),  
        "steps": steps,  
    }  
  
  
def _scan_todos(workflow_obj: dict) -> list[str]:  
    todos: list[str] = []  
  
    # notes-based TODOs  
    notes = workflow_obj.get("notes")  
    if isinstance(notes, list):  
        for n in notes:  
            if isinstance(n, str) and n.strip().upper().startswith("TODO:"):  
                todos.append(n.strip())  
  
    # step placeholders  
    steps = workflow_obj.get("steps")  
    if isinstance(steps, list):  
        for i, step in enumerate(steps):  
            if not isinstance(step, dict):  
                continue  
            # selector_ref placeholders  
            sr = step.get("selector_ref")  
            if isinstance(sr, str) and sr.strip().upper().startswith("TODO"):  
                todos.append(f"TODO: steps[{i}] selector_ref unresolved: {sr!r}")  
  
            # generic TODO values  
            for k, v in step.items():  
                if isinstance(v, str) and v.strip().upper().startswith("TODO"):  
                    todos.append(f"TODO: steps[{i}] field {k!r} unresolved: {v!r}")  
  
    # stable ordering / de-dup  
    return sorted(set(todos))  
  
  
def _smoke_stub_text(*, workflow_rel: str, workflow_name: str, todos: list[str]) -> str:  
    todo_block = ""  
    if todos:  
        todo_lines = "\n".join([f"#   - {t}" for t in todos])  
        todo_block = f"\n# TODOs detected in workflow:\n{todo_lines}\n"  
  
    return f"""\
# Auto-generated smoke stub by BUILD-1C
# Workflow name: {workflow_name}
# Workflow path (relative to this stub): {workflow_rel}
{todo_block}
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _find_project_root(start: Path) -> Path:
    start = start.resolve()
    for p in [start, *start.parents]:
        if (p / "RUN").is_dir() and (p / "CLI").is_dir():
            return p
    # fallback: repo root is one level up from dev/ in typical layout
    return start.parents[1] if len(start.parents) > 1 else start


def _import_run_workflow():
    # Try a few likely module paths (kept defensive to avoid coupling).
    candidates = [
        ("RUN.run_1a_runner", "run_workflow"),
        ("RUN.run_1a", "run_workflow"),
        ("RUN.run_1a_workflow_runner", "run_workflow"),
    ]
    last_err = None
    for mod, sym in candidates:
        try:
            m = __import__(mod, fromlist=[sym])
            fn = getattr(m, sym)
            return fn
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise ImportError(f"Could not import RUN-1A run_workflow() from expected modules. Last error: {{last_err}}")


def _call_run_workflow(run_workflow, workflow_obj: dict, workflow_path: Path, cfg: dict):
    # Try common calling conventions without requiring signature knowledge.
    tried = []
    for kwargs in (
        {{"workflow": workflow_obj, "cfg": cfg}},
        {{"workflow": workflow_obj, "config": cfg}},
        {{"workflow_obj": workflow_obj, "cfg": cfg}},
        {{"workflow_path": str(workflow_path), "cfg": cfg}},
        {{"workflow_path": str(workflow_path), "config": cfg}},
    ):
        try:
            return run_workflow(**kwargs)
        except TypeError as e:
            tried.append(str(e))
    # Try positional fallbacks
    try:
        return run_workflow(workflow_obj, cfg)
    except TypeError as e:
        tried.append(str(e))
    try:
        return run_workflow(str(workflow_path), cfg)
    except TypeError as e:
        tried.append(str(e))

    raise TypeError("Unable to call run_workflow() with known conventions. Errors: " + " | ".join(tried))


def main() -> int:
    here = Path(__file__).resolve()
    project_root = _find_project_root(here)
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    workflow_path = (here.parent / r\"\"\"{workflow_rel}\"\"\").resolve()

    if not workflow_path.exists(): 
        print("FAIL: smoke stub cannot find workflow file:", workflow_path)
        return 2

    workflow_obj = json.loads(workflow_path.read_text(encoding="utf-8"))

    # Minimal config template (edit as needed).
    # DRY_RUN=0 can be used to force real execution if your RUN-1A supports it.
    cfg = {{
        "dry_run": (os.environ.get("DRY_RUN", "1") != "0"),
        "headless": True,
        "downloads_dir": "downloads",
        "artifacts_dir": "artifacts",
        "reports_dir": "reports",
    }}

    try:
        run_workflow = _import_run_workflow()
        result = _call_run_workflow(run_workflow, workflow_obj, workflow_path, cfg)
    except Exception as e:  # noqa: BLE001
        print("FAIL: RUN-1A execution raised exception")
        print(repr(e))
        return 1

    ok = True
    if isinstance(result, dict) and "ok" in result:
        ok = bool(result.get("ok"))

    if ok:
        print("PASS: SMOKE", "{workflow_name}")
        if isinstance(result, dict):
            print("summary:", result.get("summary", result))
        return 0

    print("FAIL: SMOKE", "{workflow_name}")
    if isinstance(result, dict):
        print("result:", result)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
"""


def generate_smoke_stub(  
    workflow_path: str | Path,  
    *,  
    output_dir: str | Path = ".",  
    overwrite: bool = False,  
) -> dict:  
    wp = Path(workflow_path)  
    meta = load_workflow_metadata(wp)  
  
    workflow_name = meta["workflow_name"]  
    out_dir = Path(output_dir)  
    out_dir.mkdir(parents=True, exist_ok=True)  
  
    smoke_path = out_dir / f"dev_smoke_{workflow_name}.py"  
    if smoke_path.exists() and not overwrite:  
        return {  
            "ok": False,  
            "smoke_path": str(smoke_path),  
            "workflow_name": workflow_name,  
            "warnings": [],  
            "todos": [],  
            "errors": [f"Refusing to overwrite existing file: {str(smoke_path)} (overwrite=False)"],  
        }  
  
    workflow_obj = _read_json(wp)  
    if not isinstance(workflow_obj, dict):  
        return {  
            "ok": False,  
            "smoke_path": str(smoke_path),  
            "workflow_name": workflow_name,  
            "warnings": [],  
            "todos": [],  
            "errors": ["Workflow JSON must be an object/dict."],  
        }  
  
    todos = _scan_todos(workflow_obj)  
    warnings: list[str] = []  
  
    # Prefer a relative path from stub -> workflow for portability  
    try:  
        workflow_rel = os.path.relpath(str(wp.resolve()), start=str(out_dir.resolve()))  
    except Exception:  
        workflow_rel = str(wp)  
  
    text = _smoke_stub_text(workflow_rel=workflow_rel, workflow_name=workflow_name, todos=todos)  
    smoke_path.write_text(text, encoding="utf-8")  
  
    return {  
        "ok": True,  
        "smoke_path": str(smoke_path),  
        "workflow_name": workflow_name,  
        "warnings": warnings,  
        "todos": todos,  
    }  