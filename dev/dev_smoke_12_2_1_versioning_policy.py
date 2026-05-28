from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from REGISTRY.reg_12a_versioning_policy import (  
    parse_semver,  
    is_valid_semver,  
    compare_semver,  
    bump_semver,  
    get_versioning_policy,  
    render_versioning_policy_markdown,  
    versioning_policy_to_json,  
    check_release_versions,  
    write_versioning_policy_markdown,  
)  
  
  
def main() -> int:  
    try:  
        # SemVer parsing / validation  
        v = parse_semver("1.2.3")  
        assert str(v) == "1.2.3"  
        assert is_valid_semver("0.0.0") is True  
        assert is_valid_semver("1.2") is False  
        assert is_valid_semver("1.2.3-alpha") is False  # production policy is strict  
  
        # Comparison / bumping  
        assert compare_semver("1.0.0", "1.0.1") == -1  
        assert compare_semver("2.0.0", "1.9.9") == 1  
        assert str(bump_semver("1.2.3", "patch")) == "1.2.4"  
        assert str(bump_semver("1.2.3", "minor")) == "1.3.0"  
        assert str(bump_semver("1.2.3", "major")) == "2.0.0"  
  
        # Policy renderers  
        policy = get_versioning_policy()  
        md = render_versioning_policy_markdown(policy)  
        assert "Release Versioning Policy" in md  
        assert "workflow" in md and "selectors" in md and "framework" in md  
        assert "Bump guidance" in md  
  
        js = versioning_policy_to_json(policy)  
        assert js.strip().startswith("{")  
        assert '"policy_id"' in js and '"components"' in js  
  
        # Release version checks  
        issues_ok = check_release_versions(  
            {"workflow": "1.0.0", "selectors": "1.2.3", "framework": "1.9.9"},  
            require_same_major=False,  
        )  
        assert issues_ok == [], f"Expected no issues, got: {issues_ok}"  
  
        issues_bad = check_release_versions(  
            {"workflow": "1.0", "selectors": "x.y.z", "framework": "1.0.0"},  
            require_same_major=False,  
        )  
        assert len(issues_bad) >= 2  
  
        # I/O smoke: write and read back deterministically  
        with tempfile.TemporaryDirectory() as td:  
            out_path = os.path.join(td, "versioning_policy.md")  
            write_versioning_policy_markdown(out_path)  
            assert os.path.exists(out_path)  
            with open(out_path, "r", encoding="utf-8") as f:  
                written = f.read()  
            assert written == md  
  
        print("PASS: dev_smoke_12_2_1_versioning_policy")  
        return 0  
  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_2_1_versioning_policy :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  