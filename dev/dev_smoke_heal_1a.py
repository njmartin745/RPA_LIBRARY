# dev_smoke_heal_1a.py  
from __future__ import annotations  
  
import json  
import tempfile  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT)) 
  
from HEAL.heal_1a_patch_workflow import apply_diagnosis_patch  
  
  
def _load_json(p: Path) -> dict:  
    return json.loads(p.read_text(encoding="utf-8"))  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory() as td:  
        base = Path(td)  
        wf_path = base / "mini_workflow.json"  
        out_dir = base / "patched"  
  
        # Minimal workflow with 4 steps (3–5 required)  
        workflow = {  
            "name": "mini_workflow",  
            "steps": [  
                {"action": "nav.goto", "url": "https://example.com"},  
                {"action": "act.click", "selector_ref": "example.h1"},  
                {"action": "val.file_exists", "path": "download.csv"},  
                {"action": "out.save", "path": "out.json"},  
            ],  
        }  
        wf_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")  
  
        # --- TIMEOUT case ---  
        d_timeout = {"category": "TIMEOUT", "confidence": 0.9, "notes": {"inputs_used": {"step_index": 1}}}  
        r1 = apply_diagnosis_patch(wf_path, diagnosis=d_timeout, output_dir=out_dir)  
        p1 = Path(r1["patch_json_path"])  
        m1 = Path(r1["patch_md_path"])  
        assert p1.exists() and m1.exists()  
  
        patched1 = _load_json(p1)  
        assert patched1["steps"][1].get("timeout") == 20, "Expected injected timeout=20 on failing step"  
  
        # --- IFRAME_CONTEXT case ---  
        d_iframe = {"category": "IFRAME_CONTEXT", "confidence": 0.8, "notes": {"inputs_used": {"step_index": 1}}}  
        r2 = apply_diagnosis_patch(wf_path, diagnosis=d_iframe, output_dir=out_dir)  
        p2 = Path(r2["patch_json_path"])  
        assert p2.exists()  
        patched2 = _load_json(p2)  
        assert len(patched2["steps"]) == len(workflow["steps"]) + 1  
        assert patched2["steps"][1].get("action") == "TODO_IFRAME_SWITCH", "Expected TODO iframe switch insertion"  
  
        # --- DOWNLOAD case ---  
        d_dl = {"category": "DOWNLOAD", "confidence": 0.9, "notes": {"inputs_used": {"step_index": 2}}}  
        r3 = apply_diagnosis_patch(wf_path, diagnosis=d_dl, output_dir=out_dir)  
        p3 = Path(r3["patch_json_path"])  
        m3 = Path(r3["patch_md_path"])  
        assert p3.exists() and m3.exists()  
        md3 = m3.read_text(encoding="utf-8")  
        assert "DOWNLOAD:" in md3 or "download_wait" in md3.lower(), "Expected DOWNLOAD TODO note in patch report"  
  
        print("PASS: HEAL-1A")  
        print("Patch outputs:")  
        print(" -", r1["patch_json_path"])  
        print(" -", r1["patch_md_path"])  
        print(" -", r2["patch_json_path"])  
        print(" -", r2["patch_md_path"])  
        print(" -", r3["patch_json_path"])  
        print(" -", r3["patch_md_path"])  
        return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  