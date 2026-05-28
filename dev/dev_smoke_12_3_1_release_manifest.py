from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from REPORT.report_12a_release_manifest import (  
    build_release_manifest,  
    manifest_to_json,  
    render_manifest_markdown,  
    write_manifest_json,  
    write_manifest_markdown,  
)  
  
  
def main() -> int:  
    try:  
        with tempfile.TemporaryDirectory() as td:  
            wf_path = os.path.join(td, "workflow.json")  
            sel_path = os.path.join(td, "selectors.json")  
  
            # Deterministic contents  
            wf_bytes = b'{"name":"demo","steps":[{"type":"log","message":"hello"}]}\n'  
            sel_bytes = b'{"selectors":{"login_button":"#login"}}\n'  
  
            with open(wf_path, "wb") as f:  
                f.write(wf_bytes)  
            with open(sel_path, "wb") as f:  
                f.write(sel_bytes)  
  
            m1 = build_release_manifest(  
                workflow_version="1.0.0",  
                selectors_version="1.2.3",  
                framework_version="2.0.0",  
                workflow_path=wf_path,  
                selectors_path=sel_path,  
            )  
            m2 = build_release_manifest(  
                workflow_version="1.0.0",  
                selectors_version="1.2.3",  
                framework_version="2.0.0",  
                workflow_path=wf_path,  
                selectors_path=sel_path,  
            )  
  
            # Deterministic hashing and ordering  
            assert manifest_to_json(m1) == manifest_to_json(m2)  
  
            js = manifest_to_json(m1)  
            md = render_manifest_markdown(m1)  
  
            assert js.strip().startswith("{")  
            assert '"manifest_id"' in js and '"components"' in js  
            assert "Release Manifest" in md  
            assert "workflow" in md and "selectors" in md and "framework" in md  
            assert "sha256" in md  # because workflow/selectors artifacts included  
  
            out_json = os.path.join(td, "release_manifest.json")  
            out_md = os.path.join(td, "release_manifest.md")  
  
            write_manifest_json(out_json, m1)  
            write_manifest_markdown(out_md, m1)  
  
            with open(out_json, "r", encoding="utf-8") as f:  
                js_written = f.read()  
            with open(out_md, "r", encoding="utf-8") as f:  
                md_written = f.read()  
  
            assert js_written == js  
            assert md_written == md  
  
        print("PASS: dev_smoke_12_3_1_release_manifest")  
        return 0  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_3_1_release_manifest :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  