import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))   
  
from BUILD.build_2a_nl_spec_generator import nl_to_build_spec, validate_generated_steps  
  
  
def main() -> None:  
    description = """  
    Open ${URL}.  
    Log in with ${USERNAME} and ${PASSWORD}.  
    Wait for "Catalog View".  
    Click "Export Excel" to download the file.  
    Switch back to main tab.  
    """  
  
    spec = nl_to_build_spec(description, workflow_name="Smoke NL Spec")  
    validate_generated_steps(spec["steps"])  
  
    # Basic assertions (deterministic scaffolding expectations)  
    assert spec["spec_version"] == "BUILD-2A"  
    assert any(s.get("action") == "open" for s in spec["steps"])  
    assert any(s.get("action") == "repeat" for s in spec["steps"])  
    assert "selector_hints" in spec and isinstance(spec["selector_hints"], list)  
  
    print("dev_smoke_build_2a.py: OK")  
    print(json.dumps(spec, indent=2))  
  
  
if __name__ == "__main__":  
    main()  