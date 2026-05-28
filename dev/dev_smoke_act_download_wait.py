"""
Dev smoke test for ACT download_wait integration.
 
This validates:
ENTRY -> ACT -> NAV -> filesystem
 
It simulates a download by creating a file
while ACT waits for it.
"""
 
from __future__ import annotations
 
import threading
import time
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
 
from ENTRY.entry_1a_webdriver_bootstrap import make_driver
from ACT.act_1a_action_engine import run_actions
 
 
def simulate_download(download_dir: Path, delay: float = 2.0) -> None:
    """
    Simulate a browser writing a file after a delay.
    """
    time.sleep(delay)
    target = download_dir / "smoke_test_file.txt"
    with target.open("w", encoding="utf-8") as f:
        f.write("downloaded content")
    print(f"[SIM] Created file: {target}")
 
 
def main() -> int:
    cfg = {
        "BROWSER": "edge",
        "HEADLESS": "true",
        "DOWNLOAD_DIR": "downloads",
        "EXPLICIT_WAIT": 10,
    }
 
    download_dir = Path(cfg["DOWNLOAD_DIR"]).resolve()
    download_dir.mkdir(exist_ok=True)
 
    # Clean up old test files
    for f in download_dir.glob("smoke_test_file.txt"):
        f.unlink()
 
    driver = make_driver(cfg)
 
    try:
        # Start simulated download in background
        t = threading.Thread(
            target=simulate_download,
            args=(download_dir,),
            daemon=True,
        )
        t.start()
 
        steps = [
            {
                "action": "download_wait",
                "timeout": 10,
                "glob": "*.txt"
            }
        ]
 
        print("Running ACT download_wait...")
        run_actions(driver, steps, cfg)
 
        print("Download detected successfully.")
        return 0
 
    finally:
        driver.quit()
 
 
if __name__ == "__main__":
    raise SystemExit(main())