from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from DIFF.diff_1a_capture_edit_diff import diff_capture_edit  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    before = {  
        "schema_id": "CAPTURE_BUNDLE_1A",  
        "name": "cap",  
        "workflow": {"steps": [{"action": "open", "url": "https://example.test/a"}]},  
        "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "cap", "selectors": {}},  
    }  
    after = {  
        "schema_id": "CAPTURE_BUNDLE_1A",  
        "name": "cap",  
        "workflow": {"steps": [{"action": "open", "url": "https://example.test/b"}]},  
        "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "cap", "selectors": {}},  
    }  
  
    d = diff_capture_edit(before, after, include_unified=True)  
    assert d["counts"]["replace"] == 1  
    assert d["counts"]["total"] == 1  
    assert d["changes"][0]["op"] == "replace"  
    assert d["changes"][0]["path"].endswith("/workflow/steps/0/url")  
    assert "https://example.test/a" in d["unified_diff"]  
    assert "https://example.test/b" in d["unified_diff"]  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  