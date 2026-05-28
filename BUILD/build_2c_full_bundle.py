"""  
BUILD-2C — Full Automation Bundle Generator (orchestration only)  
  
Pipeline (explicit imports, no dynamic resolution required):  
1) BUILD-2A: NL -> spec  
2) BUILD-2B: optimize spec  
3) BUILD-1A: spec -> workflow JSON  
4) BUILD-1C: workflow -> smoke test stub  
5) optional: run via RUN-1A  
  
Constraints:  
- No Selenium logic here  
- No duplication of submodule logic (this is an orchestrator)  
- Deterministic outputs (stable filenames derived from description)  
"""  
  
from __future__ import annotations  
  
import copy  
import re  
from pathlib import Path  
from typing import Any, Dict, Optional  
  
from BUILD.build_1a_workflow_generator import generate_workflow  
from BUILD.build_1c_smoke_stub_generator import generate_smoke_stub  
from BUILD.build_2a_nl_spec_generator import nl_to_build_spec  
from BUILD.build_2b_plan_optimizer import optimize_spec  
  
__all__ = ["build_from_nl"]  
  
  
def _ensure_path(p: str | Path) -> Path:  
    return p if isinstance(p, Path) else Path(p)  
  
  
def _slugify(s: str) -> str:  
    s = (s or "").strip().lower()  
    s = re.sub(r"[^a-z0-9]+", "_", s)  
    s = re.sub(r"_+", "_", s).strip("_")  
    return s or "bundle"  
  
  
def _spec_to_build_1a_spec(*, spec_any: Any, bundle_name: str, description: str) -> Dict[str, Any]:  
    """  
    Minimal adapter: BUILD-2A/2B spec -> BUILD-1A expected spec shape.  
  
    BUILD-1A generate_workflow() expects (at least):  
      - name (string)  
      - steps (list[dict])  
    """  
    spec: Dict[str, Any] = spec_any if isinstance(spec_any, dict) else {}  
  
    steps = spec.get("steps")  
    if not isinstance(steps, list):  
        # fallback to wrapper  
        wf = spec.get("workflow")  
        if isinstance(wf, dict) and isinstance(wf.get("steps"), list):  
            steps = wf["steps"]  
        else:  
            steps = []  
  
    notes: list[str] = []  
    selector_hints = spec.get("selector_hints")  
    if isinstance(selector_hints, list) and selector_hints:  
        notes.append("Generated selector_hints (map these in your SELECTOR registry / selectors.json as needed):")  
        for h in selector_hints:  
            if isinstance(h, dict):  
                ref = h.get("selector_ref")  
                hint = h.get("hint")  
                if isinstance(ref, str) and isinstance(hint, str):  
                    notes.append(f"- {ref}: {hint}")  
  
    vars_found = spec.get("vars")  
    if isinstance(vars_found, list) and vars_found:  
        # keep deterministic ordering  
        vv = [str(x) for x in vars_found if isinstance(x, (str, int, float))]  
        vv = sorted(set(vv))  
        notes.append("Generated vars (provide these via your runtime cfg/VAR layer): " + ", ".join(vv))  
  
    # Best-effort entry_url (first open.url if present)  
    entry_url = ""  
    for st in steps:  
        if isinstance(st, dict) and st.get("action") == "open":  
            u = st.get("url")  
            if isinstance(u, str):  
                entry_url = u  
            break  
  
    return {  
        "name": bundle_name,  
        "intent": description,  
        "entry_url": entry_url,  
        "headless": True,  
        "inputs": {"mode": "none"},  
        "outputs": {},  
        "notes": notes,  
        "steps": steps,  
        "allow_inline_selectors": False,  
    }  
  
  
def build_from_nl(  
    description: str,  
    *,  
    output_dir: str | Path = ".",  
    run_after_build: bool = False,  
    cfg: dict | None = None,  
) -> dict:  
    cfg2: Dict[str, Any] = copy.deepcopy(cfg or {})  
    out_dir = _ensure_path(output_dir)  
    out_dir.mkdir(parents=True, exist_ok=True)  
  
    bundle_name = str(cfg2.get("bundle_name") or _slugify(description))  
  
    workflows_dir = _ensure_path(cfg2.get("workflows_dir", out_dir / "WORKFLOWS"))  
    dev_dir = _ensure_path(cfg2.get("dev_dir", out_dir / "dev"))  
    workflows_dir.mkdir(parents=True, exist_ok=True)  
    dev_dir.mkdir(parents=True, exist_ok=True)  
  
    run_id: Optional[str] = None  
    workflow_path: Optional[str] = None  
    smoke_test_path: Optional[str] = None  
  
    spec: Any = None  
    optimized: Any = None  
    optimizations: list[Any] = []  
    todos: list[Any] = []  
    steps_n = 0  
  
    def _fail(stage: str, e: Exception) -> dict:  
        print(f"[BUILD-2C] stage={stage} FAILED: {type(e).__name__}: {e}")  
        return {  
            "ok": False,  
            "workflow_path": workflow_path,  
            "smoke_test_path": smoke_test_path,  
            "run_id": run_id,  
            "summary": {  
                "steps": steps_n,  
                "optimizations": optimizations,  
                "todos": todos,  
                "error_stage": stage,  
                "error": f"{type(e).__name__}: {e}",  
            },  
        }  
  
    print(f"[BUILD-2C] start bundle_name={bundle_name} output_dir={out_dir}")  
  
    # ----------------  
    # BUILD-2A: spec  
    # ----------------  
    try:  
        print("[BUILD-2C] stage=spec (BUILD-2A)")  
        # nl_to_build_spec signature: (description: str, *, workflow_name: str=...)  
        spec = nl_to_build_spec(description, workflow_name=bundle_name)  
    except Exception as e:  
        return _fail("spec", e)  
  
    # --------------------  
    # BUILD-2B: optimize  
    # --------------------  
    try:  
        print("[BUILD-2C] stage=optimize (BUILD-2B)")  
        optimized = optimize_spec(spec if isinstance(spec, dict) else {})  
    except Exception as e:  
        return _fail("optimize", e)  
  
    # summary extraction (best effort)  
    try:  
        if isinstance(optimized, dict):  
            optimizations = optimized.get("optimizations") or optimized.get("changes") or optimized.get("optimizations_applied") or []  
            # BUILD-1A produces todos; BUILD-2B may not.  
            maybe_todos = optimized.get("todos") or []  
            todos = maybe_todos if isinstance(maybe_todos, list) else []  
    except Exception:  
        optimizations = []  
        todos = []  
  
    # -------------------------  
    # BUILD-1A: workflow JSON  
    # -------------------------  
    try:  
        print("[BUILD-2C] stage=workflow_json (BUILD-1A)")  
        spec_1a = _spec_to_build_1a_spec(spec_any=optimized, bundle_name=bundle_name, description=description)  
  
        wf_res = generate_workflow(  
            spec_1a,  
            output_dir=str(workflows_dir),  
            overwrite=True,  # keep CLI runs repeatable for same description  
        )  
        if not isinstance(wf_res, dict):  
            raise RuntimeError("BUILD-2C: BUILD-1A returned non-dict result.")  
        if wf_res.get("ok") is not True:  
            errs = wf_res.get("errors")  
            raise RuntimeError(f"BUILD-2C: BUILD-1A failed: {errs}")  
        workflow_path = wf_res.get("workflow_path")  
        if not isinstance(workflow_path, str) or not workflow_path:  
            raise RuntimeError("BUILD-2C: could not determine workflow_path from BUILD-1A output.")  
  
        wf_todos = wf_res.get("todos")  
        if isinstance(wf_todos, list):  
            todos = list(todos) + wf_todos  
  
    except Exception as e:  
        return _fail("workflow_json", e)  
  
    # ------------------------  
    # BUILD-1C: smoke test  
    # ------------------------  
    try:  
        print("[BUILD-2C] stage=smoke_test (BUILD-1C)")  
        st_res = generate_smoke_stub(  
            workflow_path,  
            output_dir=str(dev_dir),  
            overwrite=True,  # keep CLI runs repeatable  
        )  
        if not isinstance(st_res, dict):  
            raise RuntimeError("BUILD-2C: BUILD-1C returned non-dict result.")  
        if st_res.get("ok") is not True:  
            errs = st_res.get("errors")  
            raise RuntimeError(f"BUILD-2C: BUILD-1C failed: {errs}")  
  
        # generator uses "smoke_path"  
        sp = st_res.get("smoke_path") or st_res.get("smoke_test_path") or st_res.get("path")  
        if not isinstance(sp, str) or not sp:  
            raise RuntimeError("BUILD-2C: could not determine smoke_test_path from BUILD-1C output.")  
        smoke_test_path = sp  
  
        st_todos = st_res.get("todos")  
        if isinstance(st_todos, list):  
            todos = list(todos) + st_todos  
  
    except Exception as e:  
        return _fail("smoke_test", e)  
  
    # steps count best-effort  
    try:  
        if isinstance(optimized, dict) and isinstance(optimized.get("steps"), list):  
            steps_n = len(optimized["steps"])  
        elif isinstance(spec, dict) and isinstance(spec.get("steps"), list):  
            steps_n = len(spec["steps"])  
    except Exception:  
        steps_n = 0  
  
    # deterministic todos/optimizations normalization  
    try:  
        if not isinstance(optimizations, list):  
            optimizations = []  
        if not isinstance(todos, list):  
            todos = []  
        # stable de-dup and stable order  
        optimizations = [x for x in optimizations]  
        todos = sorted(set(str(x) for x in todos if x is not None))  
    except Exception:  
        optimizations = []  
        todos = []  
  
    # ------------------------  
    # optional run (RUN-1A)  
    # ------------------------  
    if run_after_build:  
        print("[BUILD-2C] stage=run (optional)")  
        try:  
            from RUN.run_1a_workflow_runner import run_workflow as _run_workflow  # direct import  
  
            run_res = _run_workflow(workflow_path, cfg=cfg2)  # best-effort calling convention  
            if isinstance(run_res, dict) and run_res.get("run_id"):  
                run_id = str(run_res["run_id"])  
            elif isinstance(run_res, str):  
                run_id = run_res  
            else:  
                run_id = None  
        except Exception as e:  
            # Do not fail build if optional run fails  
            print(f"[BUILD-2C] optional run FAILED: {type(e).__name__}: {e}")  
            run_id = None  
  
    print("[BUILD-2C] done ok=True")  
    return {  
        "ok": True,  
        "workflow_path": workflow_path,  
        "smoke_test_path": smoke_test_path,  
        "run_id": run_id,  
        "summary": {  
            "steps": steps_n,  
            "optimizations": optimizations,  
            "todos": todos,  
        },  
    }  