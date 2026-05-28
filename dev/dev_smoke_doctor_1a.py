# dev_smoke_doctor_1a.py  
from __future__ import annotations  
  
import json  
import tempfile  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from DOCTOR.doctor_1a_check import format_preflight_report, run_preflight  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory() as td:  
        root = Path(td)  
  
        # Fake repo structure  
        (root / "workflows").mkdir(parents=True, exist_ok=True)  
        (root / "data").mkdir(parents=True, exist_ok=True)  
        (root / "SCHEMA").mkdir(parents=True, exist_ok=True)  
        (root / "reports").mkdir(parents=True, exist_ok=True)  
        (root / "artifacts").mkdir(parents=True, exist_ok=True)  
        (root / "downloads").mkdir(parents=True, exist_ok=True)  
        (root / "history").mkdir(parents=True, exist_ok=True)  
  
        # Minimal workflow + selectors  
        (root / "workflows" / "one.json").write_text(json.dumps({"name": "one", "steps": []}, indent=2) + "\n", encoding="utf-8")  
        (root / "data" / "selectors.json").write_text(json.dumps({"example": {"h1": "h1"}}, indent=2) + "\n", encoding="utf-8")  
  
        # Minimal REGISTRY package to satisfy import best-effort  
        (root / "REGISTRY").mkdir(parents=True, exist_ok=True)  
        (root / "REGISTRY" / "__init__.py").write_text("# smoke\n", encoding="utf-8")  
        (root / "REGISTRY" / "registry_1a_store.py").write_text("# smoke\n", encoding="utf-8")  
  
        # First pass should be ok (selenium/driver may warn; ok should remain True in non-strict mode)  
        res1 = run_preflight(root=root, strict=False, cfg=None)  
        assert res1["ok"] is True, "Expected ok==True for fake repo in non-strict mode"  
        txt1 = format_preflight_report(res1)  
  
        # Remove selectors.json => should fail  
        (root / "data" / "selectors.json").unlink()  
        res2 = run_preflight(root=root, strict=False, cfg=None)  
        assert res2["ok"] is False, "Expected ok==False when selectors.json is missing"  
        txt2 = format_preflight_report(res2)  
  
        print("PASS: DOCTOR-1A")  
        print("---- report (ok case) ----")  
        print(txt1)  
        print("---- report (missing selectors) ----")  
        print(txt2)  
        return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  