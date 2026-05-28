# NAV/nav_1a_selenium_helpers.py
"""
NAV-1A — Selenium navigation and interaction helpers (pure helpers, no logging)
 
Purpose
-------
Provide small, reusable Selenium helper functions that encapsulate explicit-wait
patterns (WebDriverWait + expected_conditions) for common UI interactions in a
headless-safe way.
 
These helpers are intentionally:
- selector-based (no coordinate clicking)
- explicit-wait driven (no sleeps)  [NOTE: except wait_for_download, which must poll filesystem]
- pure utilities (no logging, no cfg coupling)
 
Inputs / Outputs
----------------
All helpers accept:
- driver: selenium WebDriver
- by: selenium.webdriver.common.by.By OR a string alias ("css", "xpath", "id", "name", ...)
- locator: selector string
 
Return values:
- wait_for_visible / wait_for_clickable -> WebElement
- click / type_text / switch_to_frame -> WebElement (or frame element for switch)
- switch_to_default_content -> None
- wait_for_download -> Path of detected stable downloaded file
 
Failure modes
-------------
- Timeout waiting for an element: raises TimeoutError with locator context.
- Click intercepted/stale: click() retries once on staleness and may fallback to JS click.
- Download wait timeout: raises TimeoutError with directory context.
 
Minimal usage example
---------------------
from ENTRY.entry_1a_webdriver_bootstrap import make_driver
from selenium.webdriver.common.by import By
from NAV.nav_1a_selenium_helpers import wait_for_visible, click
 
cfg = {"HEADLESS": "true"}
driver = make_driver(cfg)
try:
    driver.get("https://example.com")
    h1 = wait_for_visible(driver, By.CSS_SELECTOR, "h1", timeout=10)
    click(driver, "css", "a", timeout=10)
finally:
    driver.quit()
"""
 
from __future__ import annotations
 
import time
from pathlib import Path
from typing import Optional, Union
 
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    JavascriptException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
 
__all__ = [
    "wait_for_visible",
    "wait_for_clickable",
    "click",
    "type_text",
    "switch_to_frame",
    "switch_to_default_content",
    "wait_for_download",
]
 
ByLike = Union[By, str]
 
 
def _normalize_by(by: ByLike) -> By:
    """
    Normalize locator strategy.
 
    Accepts:
    - selenium By constants (which are strings like "css selector")
    - short aliases like "css", "xpath", etc.
    """
 
    # Selenium By.* values are already strings like "css selector"
    if isinstance(by, str):
        b = by.strip().lower().replace(" ", "_")
    else:
        # In case someone passes the By class directly (unlikely but safe)
        b = str(by).strip().lower().replace(" ", "_")
 
    if b in {"css", "css_selector"}:
        return By.CSS_SELECTOR
    if b == "xpath":
        return By.XPATH
    if b == "id":
        return By.ID
    if b == "name":
        return By.NAME
    if b in {"class", "class_name"}:
        return By.CLASS_NAME
    if b in {"tag", "tag_name"}:
        return By.TAG_NAME
    if b in {"link_text"}:
        return By.LINK_TEXT
    if b in {"partial_link_text"}:
        return By.PARTIAL_LINK_TEXT
 
    raise ValueError(f"Unsupported 'by' locator: {by!r}")
 
 
def _scroll_into_view(driver: WebDriver, element: WebElement) -> None:
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
            element,
        )
    except Exception:
        # Best-effort only; keep helper pure and resilient.
        return
 
 
def wait_for_visible(
    driver: WebDriver,
    by: ByLike,
    locator: str,
    timeout: int = 15,
) -> WebElement:
    """
    Wait until an element is visible.
 
    Raises TimeoutError on failure with locator context.
    """
    by_ = _normalize_by(by)
    try:
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by_, locator))
        )
    except TimeoutException as e:
        raise TimeoutError(
            f"Timed out after {timeout}s waiting for visible element: {by_} {locator!r}"
        ) from e
 
 
def wait_for_clickable(
    driver: WebDriver,
    by: ByLike,
    locator: str,
    timeout: int = 15,
) -> WebElement:
    """
    Wait until an element is clickable.
 
    Raises TimeoutError on failure with locator context.
    """
    by_ = _normalize_by(by)
    try:
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by_, locator))
        )
    except TimeoutException as e:
        raise TimeoutError(
            f"Timed out after {timeout}s waiting for clickable element: {by_} {locator!r}"
        ) from e
 
 
def click(
    driver: WebDriver,
    by: ByLike,
    locator: str,
    timeout: int = 15,
) -> WebElement:
    """
    Click an element using explicit waits and headless-safe scrolling.
 
    Strategy:
    - wait clickable
    - scroll into view
    - click
    - on staleness: reacquire once and retry
    - on intercepted click: attempt JS element click (still selector-based)
 
    Raises RuntimeError with context on failure.
    """
    by_ = _normalize_by(by)
    el = wait_for_clickable(driver, by_, locator, timeout)
    _scroll_into_view(driver, el)
 
    try:
        el.click()
        return el
 
    except StaleElementReferenceException:
        el = wait_for_clickable(driver, by_, locator, timeout)
        _scroll_into_view(driver, el)
        el.click()
        return el
 
    except ElementClickInterceptedException as e:
        # Fallback: JS click (still element-based, no coordinates)
        try:
            driver.execute_script("arguments[0].click(); return true;", el)
            return el
        except (JavascriptException, WebDriverException) as je:
            raise RuntimeError(
                f"Click intercepted and JS fallback failed for: {by_} {locator!r}"
            ) from je
 
    except WebDriverException as e:
        raise RuntimeError(f"Click failed for: {by_} {locator!r}") from e
 
 
def type_text(
    driver: WebDriver,
    by: ByLike,
    locator: str,
    text: str,
    *,
    clear_first: bool = True,
    timeout: int = 15,
) -> WebElement:
    """
    Type text into an input/textarea using explicit waits.
 
    - waits for visibility
    - scrolls into view
    - optionally clears before typing
 
    Raises RuntimeError with context on failure.
    """
    by_ = _normalize_by(by)
    el = wait_for_visible(driver, by_, locator, timeout)
    _scroll_into_view(driver, el)
 
    # Focus best-effort
    try:
        el.click()
    except WebDriverException:
        pass
 
    try:
        if clear_first:
            el.clear()
        el.send_keys(text)
        return el
    except WebDriverException as e:
        raise RuntimeError(f"type_text failed for: {by_} {locator!r}") from e
 
 
def switch_to_frame(
    driver: WebDriver,
    by: ByLike,
    locator: str,
    timeout: int = 15,
) -> WebElement:
    """
    Switch to an iframe/frame located by selector.
 
    Raises TimeoutError if the frame element does not appear;
    raises RuntimeError if switching fails.
    """
    by_ = _normalize_by(by)
    try:
        frame_el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by_, locator))
        )
    except TimeoutException as e:
        raise TimeoutError(
            f"Timed out after {timeout}s waiting for frame element: {by_} {locator!r}"
        ) from e
 
    try:
        driver.switch_to.frame(frame_el)
        return frame_el
    except WebDriverException as e:
        raise RuntimeError(f"Failed switching to frame: {by_} {locator!r}") from e
 
 
def switch_to_default_content(driver: WebDriver) -> None:
    """Switch back to the top-level document (undo switch_to_frame)."""
    driver.switch_to.default_content()
 
 
def wait_for_download(
    directory: Path,
    timeout: int = 30,
    *,
    stable_s: float = 0.75,
    poll_s: float = 0.25,
) -> Path:
    """
    Wait for a stable, non-empty file to appear in a directory (basic download hook).
 
    - Ignores common temporary download suffixes (.crdownload, .part, .tmp)
    - Requires file size > 0 and stable for a short period
 
    Returns the resolved Path to the detected file.
 
    Raises TimeoutError on failure.
    """
    directory = Path(directory).expanduser().resolve()
    if not directory.exists():
        raise FileNotFoundError(f"Download directory does not exist: {directory}")
 
    temp_suffixes = {".crdownload", ".part", ".tmp"}
    deadline = time.monotonic() + float(timeout)
 
    def is_candidate(p: Path) -> bool:
        if not p.is_file():
            return False
        if p.suffix.lower() in temp_suffixes:
            return False
        return True
 
    def safe_mtime(p: Path) -> float:
        try:
            return p.stat().st_mtime
        except OSError:
            return 0.0
 
    def stable_nonzero(p: Path) -> bool:
        try:
            s1 = p.stat().st_size
            m1 = p.stat().st_mtime
        except OSError:
            return False
 
        if s1 <= 0:
            return False
 
        # Wait a bit and confirm size+mtime haven't changed
        time.sleep(max(0.0, float(stable_s)))
        try:
            s2 = p.stat().st_size
            m2 = p.stat().st_mtime
        except OSError:
            return False
 
        return (s2 == s1) and (m2 == m1) and (s2 > 0)
 
    last_seen: Optional[Path] = None
 
    while time.monotonic() < deadline:
        try:
            files = sorted(
                (p for p in directory.glob("*") if is_candidate(p)),
                key=safe_mtime,
                reverse=True,
            )
        except OSError:
            files = []
 
        for p in files:
            last_seen = p
            if stable_nonzero(p):
                return p.resolve()
 
        time.sleep(max(0.01, float(poll_s)))
 
    msg = f"Timed out after {timeout}s waiting for download in: {directory}"
    if last_seen is not None:
        msg += f" (last seen: {last_seen.name})"
    raise TimeoutError(msg)