# dev_smoke_nav_1a.py
"""
Dev smoke test for NAV-1A Selenium helpers.
 
- Uses ENTRY-1A to create a WebDriver
- Opens example.com
- Demonstrates wait_for_visible + click
 
Run:
  python dev_smoke_nav_1a.py
"""
 
from __future__ import annotations
 
import os
from selenium.webdriver.common.by import By

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
     
from ENTRY.entry_1a_webdriver_bootstrap import make_driver
from NAV.nav_1a_selenium_helpers import wait_for_visible, click
 
 
def main() -> int:
    cfg = {
        "BROWSER": os.getenv("BROWSER", "edge"),
        "HEADLESS": os.getenv("HEADLESS", "true"),
    }
 
    driver = make_driver(cfg)
    try:
        driver.get("https://example.com")
 
        h1 = wait_for_visible(driver, By.CSS_SELECTOR, "h1", timeout=10)
        print("H1 text:", h1.text)
        assert "Example Domain" in (driver.title or ""), f"Unexpected title: {driver.title!r}"
 
        # Demonstrate click helper (navigates to IANA)
        click(driver, "css", "a", timeout=10)
        wait_for_visible(driver, "css", "body", timeout=10)
 
        print("New title:", driver.title)
        assert "IANA" in (driver.title or "") or "iana.org" in (driver.current_url or ""), (
            f"Unexpected destination: title={driver.title!r} url={driver.current_url!r}"
        )
 
        print("✅ NAV-1A SMOKE PASSED")
        return 0
    finally:
        driver.quit()
 
 
if __name__ == "__main__":
    raise SystemExit(main())