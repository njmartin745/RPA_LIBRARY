# dev_smoke_reason_1a.py  
from __future__ import annotations  
  
import json  

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from REASON.reason_1a_diagnose import diagnose_failure  
  
  
def main() -> int:  
    cases = [  
        {  
            "name": "TimeoutException -> TIMEOUT",  
            "inp": {"error_type": "TimeoutException", "error_message": "Timed out receiving message from renderer"},  
            "expect_cat": "TIMEOUT",  
            "min_conf": 0.8,  
        },  
        {  
            "name": "NoSuchElementException -> SELECTOR_NOT_FOUND",  
            "inp": {"error_type": "NoSuchElementException", "error_message": "Unable to locate element: #missing"},  
            "expect_cat": "SELECTOR_NOT_FOUND",  
            "min_conf": 0.8,  
        },  
        {  
            "name": "Download timeout -> DOWNLOAD",  
            "inp": {"error_message": "Timed out waiting for download to complete"},  
            "expect_cat": "DOWNLOAD",  
            "min_conf": 0.8,  
        },  
        {  
            "name": "ElementClickInterceptedException -> CLICK_INTERCEPTED",  
            "inp": {"error_type": "ElementClickInterceptedException", "error_message": "Other element would receive the click"},  
            "expect_cat": "CLICK_INTERCEPTED",  
            "min_conf": 0.8,  
        },  
        {  
            "name": "iframe context hint -> IFRAME_CONTEXT",  
            "inp": {  
                "step_index": 2,  
                "error_type": "NoSuchElementException",  
                "error_message": "Unable to locate element: h1",  
                "timeline": {  
                    "run_id": "smoke",  
                    "workflow_name": "wf",  
                    "steps": [  
                        {"step_index": 0, "action": "nav.goto", "status": "ok", "url": "https://example.com"},  
                        {"step_index": 1, "action": "act.switch_to_frame", "status": "ok", "metadata": {"frame": 0}},  
                        {"step_index": 2, "action": "act.click", "status": "failed", "selector": "h1"},  
                    ],  
                },  
            },  
            "expect_cat": "IFRAME_CONTEXT",  
            "min_conf": 0.65,  
        },  
    ]  
  
    example_diag = None  
    for c in cases:  
        d = diagnose_failure(**c["inp"])  
        assert d["category"] == c["expect_cat"], f"{c['name']}: expected {c['expect_cat']} got {d['category']}"  
        assert d["confidence"] >= c["min_conf"], f"{c['name']}: confidence {d['confidence']} < {c['min_conf']}"  
        assert isinstance(d.get("fixes"), list) and d["fixes"], f"{c['name']}: expected fixes"  
        assert isinstance(d.get("next_probes"), list), f"{c['name']}: expected next_probes"  
        if example_diag is None:  
            example_diag = d  
  
    print("Example diagnosis:")  
    print(json.dumps(example_diag, indent=2, sort_keys=True))  
    print("PASS: REASON-1A")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  