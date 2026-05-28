"""  
How to run:  
  python dev/dev_smoke_var_1a.py  
"""  
  
from __future__ import annotations  

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from VAR.var_1a_runtime_store import render_vars, set_var  
  
  
def main() -> int:  
    cfg = {}  
  
    set_var(cfg, "title", "Example Domain")  
    out = render_vars("Page: ${title}", cfg)  
  
    d = {"label": "Title is ${title}", "nested": {"t": "${title}"}}  
    l = ["${title}", "Page: ${title}", {"x": "${title}"}]  
    rd = render_vars(d, cfg)  
    rl = render_vars(l, cfg)  
  
    ok = True  
    ok = ok and (out == "Page: Example Domain")  
    ok = ok and (rd["label"] == "Title is Example Domain")  
    ok = ok and (rd["nested"]["t"] == "Example Domain")  
    ok = ok and (rl[0] == "Example Domain")  
    ok = ok and (rl[1] == "Page: Example Domain")  
    ok = ok and (rl[2]["x"] == "Example Domain")  
  
    print("\n=== dev_smoke_var_1a ===")  
    print(f"rendered_str: {out!r}")  
    print(f"rendered_dict: {rd!r}")  
    print(f"rendered_list: {rl!r}")  
  
    if ok:  
        print("PASS: dev_smoke_var_1a")  
        return 0  
  
    print("FAIL: dev_smoke_var_1a")  
    return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  