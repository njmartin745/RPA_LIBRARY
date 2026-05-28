from __future__ import annotations  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from BUILD.build_3b_bundle_fingerprint import stamp_bundle_version_and_fingerprint  
  
__all__ = ["dev_smoke"]  
  
  
def dev_smoke() -> None:  
    base = {  
        "schema_id": "DEPLOY_BUNDLE_1A",  
        "name": "captured",  
        "workflow": {"steps": [{"action": "open", "url": "https://example.test/app"}]},  
        "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "captured", "selectors": {}},  
        "meta": {"source_schema_id": "CAPTURE_BUNDLE_1A", "source_name": "captured"},  
    }  
  
    stamped1 = stamp_bundle_version_and_fingerprint(base)  
    stamped2 = stamp_bundle_version_and_fingerprint(dict(base))  
  
    assert stamped1["fingerprint"]["algo"] == "sha256"  
    assert stamped1["fingerprint"]["sha256"] == stamped2["fingerprint"]["sha256"]  
    assert stamped1["version"] == stamped2["version"]  
    assert stamped1["version"].startswith("sha256:")  
  
    changed = dict(base)  
    changed["meta"] = dict(base["meta"])  
    changed["meta"]["source_name"] = "captured2"  
    stamped3 = stamp_bundle_version_and_fingerprint(changed)  
    assert stamped3["fingerprint"]["sha256"] != stamped1["fingerprint"]["sha256"]  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  