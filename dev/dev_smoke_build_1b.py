from __future__ import annotations  
  
import json  
import sys  
import tempfile  
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))  
  
from BUILD.build_1a_workflow_generator import generate_workflow  # noqa: E402  
from BUILD.build_1b_intake_questionnaire import build_spec_from_answers  # noqa: E402  
  
  
def main() -> int:  
    synthetic_answers = {  
        "name": "smoke_build_1b",  
        "intent": "BUILD-1B smoke: questionnaire -> spec -> BUILD-1A workflow",  
        "entry_url": "https://example.com/",  
        "headless": True,  
        "requires_login": False,  
        "input_mode": "none",  
        "selectors_known": False,  
        "downloads_expected": False,  
        "download_dir": "downloads",  
        "notes": "Synthetic intake answers for smoke test.",  
    }  
  
    payload = build_spec_from_answers(synthetic_answers)  
    assert payload["ok"] is True, f"build_spec_from_answers failed:\n{json.dumps(payload, indent=2)}"  
    spec = payload["spec"]  
    assert isinstance(spec, dict) and spec.get("name"), "Spec missing name"  
  
    with tempfile.TemporaryDirectory() as td:  
        out_dir = Path(td)  
        result = generate_workflow(spec, output_dir=out_dir, overwrite=True)  
  
        assert result["ok"] is True, f"generate_workflow failed:\n{json.dumps(result, indent=2)}"  
        wf_path = Path(result["workflow_path"])  
        assert wf_path.exists(), f"workflow not created: {wf_path}"  
  
        obj = json.loads(wf_path.read_text(encoding="utf-8"))  
        assert isinstance(obj, dict)  
        assert obj.get("metadata", {}).get("generator") == "BUILD-1A"  
        assert isinstance(obj.get("steps"), list)  
  
        print("PASS: BUILD-1B")  
        print(f"workflow_path: {wf_path}")  
        print("actions_used:", result.get("summary", {}).get("actions_used", {}))  
  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  