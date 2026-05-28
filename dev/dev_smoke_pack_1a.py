# dev/dev_smoke_pack_1a.py  
from __future__ import annotations  
  
import json  
import os  
import shutil  
import subprocess  
import sys  
import tempfile  
from pathlib import Path  
  
  
def _find_repo_root(start: Path) -> Path:  
    start = start.resolve()  
    for p in [start, *start.parents]:  
        if (p / "CLI" / "cli_pack_1a.py").exists():  
            return p  
    raise RuntimeError("Could not locate repo root containing CLI/cli_pack_1a.py")  
  
  
def _with_repo_pythonpath(env: dict, project_root: Path) -> dict:  
    env = dict(env)  
    py_path = env.get("PYTHONPATH", "")  
    env["PYTHONPATH"] = str(project_root) + (os.pathsep + py_path if py_path else "")  
    return env  
  
  
def _run_cmd(*, cwd: Path, argv: list[str], project_root: Path) -> subprocess.CompletedProcess:  
    env = _with_repo_pythonpath(os.environ, project_root)  
    return subprocess.run(  
        argv,  
        cwd=str(cwd),  
        env=env,  
        stdout=subprocess.PIPE,  
        stderr=subprocess.PIPE,  
        text=True,  
    )  
  
  
def _run_cli(*, cwd: Path, args: list[str], project_root: Path) -> subprocess.CompletedProcess:  
    return _run_cmd(cwd=cwd, argv=[sys.executable, "-m", "CLI.cli_pack_1a", *args], project_root=project_root)  
  
  
def _copy_if_exists(src: Path, dst: Path) -> bool:  
    if src.exists() and src.is_file():  
        dst.parent.mkdir(parents=True, exist_ok=True)  
        shutil.copy2(src, dst)  
        return True  
    return False  
  
  
def _ensure_schema_artifacts(*, project_root: Path, temp_root: Path) -> None:  
    """  
    Fix for: RUN-1A failing with  
      Missing SCHEMA artifact. Expected SCHEMA/steps_schema.json (or SCHEMA/schema_1a_steps.json).  
  
    Diagnosis:  
    Some runners change CWD to the workflow file's directory. If the workflow lives under temp_root/workflows/,  
    relative lookups for SCHEMA/* can end up under temp_root/workflows/SCHEMA/ instead of temp_root/SCHEMA/.  
  
    Resolution:  
    Seed schema artifacts into BOTH:  
      - temp_root/SCHEMA/  
      - temp_root/workflows/SCHEMA/  
    """  
    schema_root = temp_root / "SCHEMA"  
    schema_wf = temp_root / "workflows" / "SCHEMA"  
    schema_root.mkdir(parents=True, exist_ok=True)  
    schema_wf.mkdir(parents=True, exist_ok=True)  
  
    # 1) Try copying from the real repo  
    copied_any = False  
    copied_any |= _copy_if_exists(project_root / "SCHEMA" / "steps_schema.json", schema_root / "steps_schema.json")  
    copied_any |= _copy_if_exists(project_root / "SCHEMA" / "schema_1a_steps.json", schema_root / "schema_1a_steps.json")  
  
    # 2) If repo artifacts aren't present for some reason, generate them into temp_root (writes to temp_root/SCHEMA)  
    if not copied_any:  
        gen = _run_cmd(  
            cwd=temp_root,  
            argv=[sys.executable, "-m", "SCHEMA.schema_1a_generate"],  
            project_root=project_root,  
        )  
        if gen.returncode != 0:  
            raise RuntimeError(  
                "Failed to generate SCHEMA artifacts in temp repo.\n"  
                f"STDOUT:\n{gen.stdout}\nSTDERR:\n{gen.stderr}"  
            )  
  
    # 3) Validate existence in temp_root/SCHEMA  
    ok_root = (schema_root / "steps_schema.json").exists() or (schema_root / "schema_1a_steps.json").exists()  
    if not ok_root:  
        raise RuntimeError(  
            "SCHEMA artifacts still missing in temp repo after seeding.\n"  
            f"Looked for:\n- {schema_root/'steps_schema.json'}\n- {schema_root/'schema_1a_steps.json'}"  
        )  
  
    # 4) Duplicate into temp_root/workflows/SCHEMA to survive runners that chdir(workflow_dir)  
    if (schema_root / "steps_schema.json").exists():  
        shutil.copy2(schema_root / "steps_schema.json", schema_wf / "steps_schema.json")  
    if (schema_root / "schema_1a_steps.json").exists():  
        shutil.copy2(schema_root / "schema_1a_steps.json", schema_wf / "schema_1a_steps.json")  
  
  
def _ensure_minimal_data(*, temp_root: Path) -> None:  
    """  
    Create minimal data/selectors.json in BOTH temp_root/data and temp_root/workflows/data  
    for the same 'runner chdir to workflow dir' reason.  
    """  
    (temp_root / "data").mkdir(parents=True, exist_ok=True)  
    (temp_root / "workflows" / "data").mkdir(parents=True, exist_ok=True)  
  
    selectors = {"example": {"h1": "h1"}}  
    (temp_root / "data" / "selectors.json").write_text(json.dumps(selectors, indent=2) + "\n", encoding="utf-8")  
    (temp_root / "workflows" / "data" / "selectors.json").write_text(  
        json.dumps(selectors, indent=2) + "\n", encoding="utf-8"  
    )  
  
  
def _seed_workflow_json(project_root: Path) -> dict:  
    """  
    Deterministic smoke behavior:  
      - By default, do NOT consume any locally-generated .dev_tmp workflows, because they may  
        contain legacy/unsupported actions and will cause schema validation to fail.  
      - If you explicitly want to test packing/running a seeded workflow, set:  
          RPA_DEV_SMOKE_PACK_USE_SEEDED_WORKFLOW=1  
        In that mode we still sanitize steps to allowed actions only, and we guarantee at least  
        one step exists (schema requires non-empty steps).  
    """  
    use_seeded = os.environ.get("RPA_DEV_SMOKE_PACK_USE_SEEDED_WORKFLOW", "").strip().lower() in {  
        "1",  
        "true",  
        "yes",  
        "y",  
        "on",  
    }  
  
    # Always-valid minimal workflow for dry-run smoke (schema requires non-empty steps).  
    default = {"name": "one", "steps": [{"action": "open", "url": "about:blank"}]}  
  
    if not use_seeded:  
        return default  
  
    allowed_actions = {  
        "open",  
        "click_selector",  
        "type_selector_secret",  
        "wait_for_selector",  
        "exec_js",  
        "exec_js_file",  
        "repeat",  
        "log",  
        "switch_back_to_main_tab",  
    }  
  
    candidates = [  
        project_root / ".dev_tmp" / "workflow_1a_smoke.json",  
        project_root / ".dev_tmp" / "run_1a_smoke_workflow.json",  
    ]  
  
    for p in candidates:  
        if not (p.exists() and p.is_file()):  
            continue  
  
        try:  
            obj = json.loads(p.read_text(encoding="utf-8"))  
        except Exception:  
            continue  
  
        if not isinstance(obj, dict):  
            continue  
  
        steps = obj.get("steps", [])  
        if not isinstance(steps, list):  
            return default  
  
        sanitized: list[dict] = []  
        for step in steps:  
            if not isinstance(step, dict):  
                continue  
  
            action = step.get("action")  
  
            # Small legacy compatibility: "click" -> "click_selector" if it has selector info.  
            if action == "click":  
                if ("selector" in step) or ("selector_ref" in step):  
                    new_step = dict(step)  
                    new_step["action"] = "click_selector"  
                    action = "click_selector"  
                    step = new_step  
                else:  
                    continue  
  
            if action in allowed_actions:  
                sanitized.append(step)  
  
        if not sanitized:  
            return default  
  
        return {"name": obj.get("name", "one"), "steps": sanitized}  
  
    return default  
  
def main() -> int:  
    project_root = _find_repo_root(Path(__file__))  
  
    with tempfile.TemporaryDirectory() as td:  
        root = Path(td)  
  
        # Temp repo skeleton  
        (root / "workflows").mkdir(parents=True, exist_ok=True)  
        (root / "reports").mkdir(parents=True, exist_ok=True)  
        (root / "artifacts").mkdir(parents=True, exist_ok=True)  
        (root / "downloads").mkdir(parents=True, exist_ok=True)  
        (root / "history").mkdir(parents=True, exist_ok=True)  
  
        # Some modules prefer this file to exist  
        (root / "history" / "run_history.jsonl").write_text("", encoding="utf-8")  
  
        # Seed schema + data (in both root and workflows/ subtrees)  
        _ensure_schema_artifacts(project_root=project_root, temp_root=root)  
        _ensure_minimal_data(temp_root=root)  
  
        # Create a temp workflow file.  
        # Put it at the temp repo root to avoid runner chdir(workflow_dir) breaking relative paths.  
        wf_obj = _seed_workflow_json(project_root)  
        (root / "workflow.json").write_text(json.dumps(wf_obj, indent=2) + "\n", encoding="utf-8")  
  
        # Also place a copy under workflows/ for compatibility with any tooling assumptions  
        (root / "workflows" / "one.json").write_text(json.dumps(wf_obj, indent=2) + "\n", encoding="utf-8")  
  
        # 1) doctor  
        r1 = _run_cli(cwd=root, args=["doctor"], project_root=project_root)  
        assert r1.returncode == 0, (  
            f"doctor failed rc={r1.returncode}\nSTDOUT:\n{r1.stdout}\nSTDERR:\n{r1.stderr}"  
        )  
  
        # 2) history (use temp history file explicitly)  
        r2 = _run_cli(  
            cwd=root,  
            args=["history", "--history-path", "history/run_history.jsonl", "--limit", "50"],  
            project_root=project_root,  
        )  
        assert r2.returncode == 0, (  
            f"history failed rc={r2.returncode}\nSTDOUT:\n{r2.stdout}\nSTDERR:\n{r2.stderr}"  
        )  
  
        # 3) run (dry-run allowed)  
        r3 = _run_cli(cwd=root, args=["run", "workflow.json", "--dry-run"], project_root=project_root)  
        assert r3.returncode == 0, (  
            f"run failed rc={r3.returncode}\nSTDOUT:\n{r3.stdout}\nSTDERR:\n{r3.stderr}"  
        )  
  
        print("PASS: PACK-1A")  
        print("---- doctor ----")  
        print(r1.stdout.strip())  
        print("---- history ----")  
        print(r2.stdout.strip())  
        print("---- run ----")  
        print(r3.stdout.strip())  
        return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  