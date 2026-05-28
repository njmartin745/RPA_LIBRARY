from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from REPORT.report_12a_release_manifest import build_release_manifest  
from REPORT.report_12b_bundle_fingerprint import (  
    canonical_fingerprint_input,  
    compute_bundle_fingerprint,  
    fingerprint_to_json,  
    render_fingerprint_markdown,  
    write_fingerprint_json,  
    write_fingerprint_markdown,  
)  
  
  
def main() -> int:  
    try:  
        # Create identical artifacts in two different directories; fingerprint must match  
        with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:  
            wf_bytes = b'{"name":"demo","steps":[{"type":"log","message":"hello"}]}\n'  
            sel_bytes = b'{"selectors":{"login_button":"#login"}}\n'  
  
            wf1 = os.path.join(td1, "workflow.json")  
            sel1 = os.path.join(td1, "selectors.json")  
            wf2 = os.path.join(td2, "workflow.json")  
            sel2 = os.path.join(td2, "selectors.json")  
  
            for p, b in [(wf1, wf_bytes), (sel1, sel_bytes), (wf2, wf_bytes), (sel2, sel_bytes)]:  
                with open(p, "wb") as f:  
                    f.write(b)  
  
            m1 = build_release_manifest(  
                workflow_version="1.0.0",  
                selectors_version="1.2.3",  
                framework_version="2.0.0",  
                workflow_path=wf1,  
                selectors_path=sel1,  
            )  
            m2 = build_release_manifest(  
                workflow_version="1.0.0",  
                selectors_version="1.2.3",  
                framework_version="2.0.0",  
                workflow_path=wf2,  
                selectors_path=sel2,  
            )  
  
            inp1 = canonical_fingerprint_input(m1)  
            inp2 = canonical_fingerprint_input(m2)  
            assert inp1 == inp2, "Canonical fingerprint input must not depend on file paths"  
  
            bf1 = compute_bundle_fingerprint(m1)  
            bf2 = compute_bundle_fingerprint(m2)  
            assert bf1.fingerprint == bf2.fingerprint, "Fingerprint must be stable across different paths"  
  
            js = fingerprint_to_json(bf1)  
            md = render_fingerprint_markdown(bf1)  
            assert js.strip().startswith("{")  
            assert '"fingerprint"' in js  
            assert "Bundle Fingerprint" in md  
            assert bf1.fingerprint in md  
  
            out_json = os.path.join(td1, "bundle_fingerprint.json")  
            out_md = os.path.join(td1, "bundle_fingerprint.md")  
            write_fingerprint_json(out_json, bf1)  
            write_fingerprint_markdown(out_md, bf1)  
  
            with open(out_json, "r", encoding="utf-8") as f:  
                js_written = f.read()  
            with open(out_md, "r", encoding="utf-8") as f:  
                md_written = f.read()  
  
            assert js_written == js  
            assert md_written == md  
  
        print("PASS: dev_smoke_12_3_2_bundle_fingerprint")  
        return 0  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_3_2_bundle_fingerprint :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  