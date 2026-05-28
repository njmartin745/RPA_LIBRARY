# dev_smoke_capture_1a.py  
from __future__ import annotations  
  
import os  
import sys  
import tempfile  
from pathlib import Path  
  
ROOT = Path(__file__).resolve().parents[1]  
if str(ROOT) not in sys.path:  
    sys.path.insert(0, str(ROOT))  
  
from CAPTURE.capture_1a_semi_auto import capture_session  
from SELECTOR.selector_1a_registry import get_selector, load_selectors  
  
  
def _truthy_env(name: str) -> bool:  
    v = str(os.getenv(name, "") or "").strip().lower()  
    return v in {"1", "true", "yes", "y", "on"}  
  
  
def main() -> int:  
    # This smoke is intentionally interactive; skip by default so unattended smoke sweeps pass.  
    if not _truthy_env("RPA_RUN_INTERACTIVE_SMOKES"):  
        print("SKIP: dev_smoke_capture_1a.py (interactive)")  
        print("  Set RPA_RUN_INTERACTIVE_SMOKES=1 to run this smoke.")  
        return 0  
  
    if not (sys.stdin.isatty() and sys.stdout.isatty()):  
        print("SKIP: dev_smoke_capture_1a.py (interactive requires a TTY)")  
        print("  Run from an interactive terminal and set RPA_RUN_INTERACTIVE_SMOKES=1.")  
        return 0  
  
    print("CAPTURE-1A smoke test (interactive)")  
    print("  - A headed browser will open to https://example.com")  
    print("  - Click the <h1> element once")  
    print("  - Choose a candidate to save (press Enter for default)\n")  
  
    with tempfile.TemporaryDirectory() as td:  
        tmp = Path(td)  
        selectors_path = tmp / "selectors.json"  
  
        saved = capture_session(  
            "https://www.google.com",  
            selector_name="example.h1",  
            cfg={"headless": True},  # will be forced headed by capture tool  
            output_path=selectors_path,  
            timeout=60,  
        )  
  
        reg = load_selectors(selectors_path=selectors_path)  
        resolved = get_selector("example.h1", registry=reg)  
        assert isinstance(resolved, dict)  
        assert resolved.get("selector"), "Resolution returned empty selector"  
  
        print("\nPASS: CAPTURE-1A (semi-auto)")  
        print(f"  saved preferred: {saved['saved'].get('preferred')}")  
        print(f"  resolved: {resolved.get('strategy')} -> {resolved.get('selector')}")  
        return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  