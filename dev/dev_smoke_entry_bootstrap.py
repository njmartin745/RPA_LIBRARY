# dev_smoke_entry_bootstrap.py
"""
Smoke Test: ENTRY-1A webdriver bootstrap (Edge + Chrome)
 
Runs quick headless boots for each supported browser and navigates to https://example.com.
 
Usage:
  python dev_smoke_entry_bootstrap.py
  python dev_smoke_entry_bootstrap.py --headed
  python dev_smoke_entry_bootstrap.py --browser edge
  python dev_smoke_entry_bootstrap.py --browser chrome
 
Notes:
- This is intentionally NOT pytest. It's a fast manual sanity check.
- Requires drivers under ./drivers/ OR DRIVER_PATH/RPA_DRIVER_PATH set.
"""
 
from __future__ import annotations
 
import argparse
import sys
from typing import Dict, Any

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
     
from ENTRY.entry_1a_webdriver_bootstrap import make_driver
 
 
def _run_one(browser: str, *, headless: bool) -> None:
    cfg: Dict[str, Any] = {
        "BROWSER": browser,
        "HEADLESS": "true" if headless else "false",
    }
 
    print(f"\n== ENTRY Smoke: {browser.upper()} | headless={headless} ==")
    driver = make_driver(cfg)
    try:
        driver.get("https://example.com")
        title = driver.title or ""
        print(f"OK: navigated (title={title!r})")
    finally:
        driver.quit()
        print("OK: quit")
 
 
def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--headed", action="store_true", help="Run with HEADLESS=false")
    p.add_argument("--browser", choices=["edge", "chrome", "both"], default="both")
    args = p.parse_args()
 
    headless = not args.headed
 
    try:
        if args.browser in ("edge", "both"):
            _run_one("edge", headless=headless)
        if args.browser in ("chrome", "both"):
            _run_one("chrome", headless=headless)
    except Exception as e:
        print(f"\nSMOKE TEST FAILED: {e.__class__.__name__}: {e}")
        return 1
 
    print("\n✅ SMOKE TEST PASSED")
    return 0
 
 
if __name__ == "__main__":
    raise SystemExit(main())