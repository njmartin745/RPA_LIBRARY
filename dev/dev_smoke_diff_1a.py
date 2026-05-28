# dev_smoke_diff_1a.py  
from __future__ import annotations  
  
import json  
import tempfile  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from DIFF.diff_1a_config_changes import (  
    compute_fingerprint,  
    diff_fingerprints,  
    write_diff_report,  
    write_fingerprint,  
)  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory() as td:  
        root = Path(td)  
  
        # Structure  
        (root / "workflows").mkdir(parents=True, exist_ok=True)  
        (root / "data").mkdir(parents=True, exist_ok=True)  
        (root / "SCHEMA").mkdir(parents=True, exist_ok=True)  
        (root / "reports").mkdir(parents=True, exist_ok=True)  
  
        # Initial files  
        (root / "workflows" / "a.json").write_text(json.dumps({"name": "a", "steps": [{"action": "nav.goto"}]}, indent=2) + "\n", encoding="utf-8")  
        (root / "data" / "selectors.json").write_text(json.dumps({"example": {"h1": "h1"}}, indent=2) + "\n", encoding="utf-8")  
        (root / "SCHEMA" / "schema.json").write_text(json.dumps({"version": 1, "fields": ["action"]}, indent=2) + "\n", encoding="utf-8")  
  
        fp_a = compute_fingerprint(  
            root=root,  
            workflows_dir="workflows",  
            selectors_path="data/selectors.json",  
            schema_dir="SCHEMA",  
        )  
        a_path = write_fingerprint(fp_a, out_dir=root / "reports", name="fingerprint_a")  
  
        # Modify workflow + selectors  
        (root / "workflows" / "a.json").write_text(json.dumps({"name": "a", "steps": [{"action": "nav.goto"}, {"action": "act.click"}]}, indent=2) + "\n", encoding="utf-8")  
        (root / "data" / "selectors.json").write_text(json.dumps({"example": {"h1": "h1"}, "new": {"btn": "#btn"}}, indent=2) + "\n", encoding="utf-8")  
  
        fp_b = compute_fingerprint(  
            root=root,  
            workflows_dir="workflows",  
            selectors_path="data/selectors.json",  
            schema_dir="SCHEMA",  
        )  
        b_path = write_fingerprint(fp_b, out_dir=root / "reports", name="fingerprint_b")  
  
        d = diff_fingerprints(fp_a, fp_b)  
        report_paths = write_diff_report(d, out_dir=root / "reports", name="diff_ab")  
  
        assert fp_a["overall_hash"] != fp_b["overall_hash"], "Expected overall_hash to differ after modifications"  
        assert d["workflows"]["counts"]["changed"] >= 1, "Expected at least one changed workflow file"  
        assert d["selectors"]["changed"] is True, "Expected selectors to be flagged changed"  
  
        dp_json = Path(report_paths["json"])  
        dp_md = Path(report_paths["md"])  
        assert dp_json.exists() and dp_json.stat().st_size > 20  
        assert dp_md.exists() and dp_md.stat().st_size > 20  
        assert a_path.exists() and a_path.stat().st_size > 20  
        assert b_path.exists() and b_path.stat().st_size > 20  
  
        print("PASS: DIFF-1A")  
        print("fingerprint_a:", a_path.as_posix())  
        print("fingerprint_b:", b_path.as_posix())  
        print("diff json:", dp_json.as_posix())  
        print("diff md:", dp_md.as_posix())  
        return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  