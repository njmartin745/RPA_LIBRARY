from __future__ import annotations  
  
import os  
import tempfile  
import json  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from DIFF.diff_12a_reviewable_diffs import (  
    diff_texts_reviewable,  
    diff_files_reviewable,  
    check_reviewable_diff_required,  
    write_text_file,  
)  
  
  
def main() -> int:  
    try:  
        # Canonicalization should eliminate noisy diffs from key-order / formatting differences  
        before_obj = {"b": 2, "a": 1, "steps": [{"type": "log", "message": "hi"}]}  
        after_obj_same = {"a": 1, "steps": [{"message": "hi", "type": "log"}], "b": 2}  
  
        before_text = json.dumps(before_obj)  # unsorted  
        after_text_same = json.dumps(after_obj_same, indent=4)  # different formatting  
  
        res_same = diff_texts_reviewable(before_text, after_text_same, kind="workflow", fromfile="w1.json", tofile="w2.json")  
        assert res_same.changed is False, "Expected no semantic change after canonicalization"  
        assert res_same.diff == "", "Expected empty diff when canonical forms are identical"  
        assert check_reviewable_diff_required(res_same) == []  
  
        # Real change should produce a unified diff  
        after_obj_changed = {"a": 1, "b": 3, "steps": [{"type": "log", "message": "hi"}]}  
        after_text_changed = json.dumps(after_obj_changed)  
  
        res_changed = diff_texts_reviewable(before_text, after_text_changed, kind="workflow", fromfile="w1.json", tofile="w2.json")  
        assert res_changed.changed is True  
        assert res_changed.diff.startswith("--- "), "Expected unified diff header"  
        assert "\n+++ " in res_changed.diff  
        assert "-  \"b\": 2" in res_changed.diff or "+  \"b\": 3" in res_changed.diff  
        assert check_reviewable_diff_required(res_changed) == []  
  
        # File-based smoke  
        with tempfile.TemporaryDirectory() as td:  
            p1 = os.path.join(td, "selectors_before.json")  
            p2 = os.path.join(td, "selectors_after.json")  
            write_text_file(p1, before_text)  
            write_text_file(p2, after_text_changed)  
  
            res_files = diff_files_reviewable(p1, p2, kind="selectors")  
            assert res_files.changed is True  
            assert res_files.diff.startswith("--- ")  
  
        print("PASS: dev_smoke_12_2_2_reviewable_diffs")  
        return 0  
  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_2_2_reviewable_diffs :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  