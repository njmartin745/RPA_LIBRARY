from __future__ import annotations  
  
import json  
import sys  
import tempfile  
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))  
  
from BUILD.build_1c_smoke_stub_generator import generate_smoke_stub  # noqa: E402  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory() as td:  
        tmp = Path(td)  
  
        # Create a minimal workflow JSON that looks like BUILD-1A output  
        wf = {  
            "name": "smoke_build_1c",  
            "intent": "BUILD-1C smoke test workflow",  
            "entry_url": "https://example.com/",  
            "headless": True,  
            "inputs": {"mode": "none"},  
            "outputs": {"downloads": False},  
            "notes": ["TODO: steps[1] selector_ref unresolved"],  
            "metadata": {  
                "created_at_utc": "1970-01-01T00:00:00Z",  
                "generator": "BUILD-1A",  
                "schema_version": "SCHEMA-1A",  
            },  
            "steps": [  
                {"action": "get", "url": "https://example.com/"},  
                {"action": "click", "selector_ref": "TODO_SELECTOR_1"},  
            ],  
        }  
        wf_path = tmp / "smoke_build_1c.json"  
        wf_path.write_text(json.dumps(wf, indent=2, sort_keys=True) + "\n", encoding="utf-8")  
  
        res = generate_smoke_stub(wf_path, output_dir=tmp, overwrite=True)  
        assert res["ok"] is True, f"generate_smoke_stub failed: {res}"  
  
        smoke_path = Path(res["smoke_path"])  
        assert smoke_path.exists(), f"smoke stub not created: {smoke_path}"  
  
        text = smoke_path.read_text(encoding="utf-8")  
        assert "run_workflow" in text, "smoke stub missing run_workflow reference"  
        assert "PASS: SMOKE" in text and "FAIL: SMOKE" in text, "smoke stub missing PASS/FAIL handling"  
  
        print("PASS: BUILD-1C")  
        print(f"smoke_path: {smoke_path}")  
        print(f"workflow: {wf_path}")  
  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  