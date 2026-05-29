"""  
ENTRY-1A — Standard headless-first webdriver bootstrap (Chrome/Edge configurable)  
  
Purpose  
-------  
Create and configure a Selenium WebDriver with consistent defaults for:  
- headless mode  
- download directory behavior  
- stability flags for CI/headless environments  
- optional attach-to-existing-browser via remote debugging port  
  
Inputs  
------  
cfg: Mapping[str, Any] typically populated from env/CLI. Supported keys:  
- BROWSER: "edge" or "chrome" (default: "edge")  
- HEADLESS: truthy string ("1"/"true"/"yes"/"on") enables headless  
- DOWNLOAD_DIR: downloads folder path (default: env RPA_DOWNLOAD_DIR else "downloads")  
- IMPLICIT_WAIT: seconds for Selenium implicit wait (default: 0)  
- PAGELOAD_TIMEOUT: seconds for page load timeout (optional)  
- DEBUG_PORT: optional port number string (alternate to env REMOTE_DEBUG_PORT)  
- DRIVER_PATH: optional explicit driver path (alternate to env RPA_DRIVER_PATH)  
  
Selenium Manager controls (optional)  
------------------------------------  
- SELENIUM_MANAGER / USE_SELENIUM_MANAGER: truthy => force Selenium Manager (ignore DRIVER_PATH)  
- SELENIUM_MANAGER_FALLBACK: truthy/falsey => if local driver fails due to version mismatch,  
  retry using Selenium Manager. Default: enabled.  
  
Outputs  
-------  
- selenium WebDriver instance (Edge or Chrome)  
  
When to use  
-----------  
- You need a consistent local webdriver bootstrap with predictable headless + downloads behavior.  
  
When NOT to use  
---------------  
- You need Selenium Grid / remote execution.  
- You need enterprise profile/cert injection or special SSO policies (propose a new ENTRY option).  
  
Headless notes  
--------------  
- Uses Chromium headless mode ("--headless=new") when HEADLESS is enabled.  
- Adds common flags: --no-sandbox, --disable-dev-shm-usage, --disable-gpu  
  
Dependencies  
------------  
- selenium  
- standard library: os, pathlib, typing  
  
Common failure modes + mitigations  
----------------------------------  
- Driver binary missing -> FileNotFoundError with actionable path (unless Selenium Manager is enabled).  
- Driver version mismatch -> SessionNotCreatedException; with fallback enabled this will retry via Selenium Manager.  
- Debug attach fails -> verify browser launched with remote debugging port enabled.  
  
Minimal usage example  
---------------------  
from ENTRY.entry_1a_webdriver_bootstrap import make_driver  
cfg = {"BROWSER": "chrome", "HEADLESS": "true", "DOWNLOAD_DIR": "downloads"}  
driver = make_driver(cfg)  
driver.get("https://example.com")  
driver.quit() 

Status
------
Audited

Architecture Position
---------------------
RUN-1A
    ↓
PIPE-1E
    ↓
PIPE-1A
    ↓
ENTRY-1A
    ↓
ACT-1A
"""  
  
from __future__ import annotations  
  
import os  
from pathlib import Path  
from typing import Any, Mapping, Optional, Union  
  
from selenium import webdriver  
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException  
from selenium.webdriver.chrome.options import Options as ChromeOptions  
from selenium.webdriver.chrome.service import Service as ChromeService  
from selenium.webdriver.edge.options import Options as EdgeOptions  
from selenium.webdriver.edge.service import Service as EdgeService  
  
__all__ = [  
    "parse_headless",  
    "default_download_dir",  
    "resolve_driver_path",  
    "make_driver",  
    "dev_smoke",  
]  
  
  
def parse_headless(value: Any) -> bool:  
    """Return True if value represents a truthy headless toggle."""  
    raw = str(value or "").strip().lower()  
    return raw in {"1", "true", "yes", "on"}  
  
  
def _truthy(v: Any) -> Optional[bool]:  
    if v is None:  
        return None  
    if isinstance(v, bool):  
        return v  
    if isinstance(v, (int, float)):  
        return bool(v)  
    if isinstance(v, str):  
        s = v.strip().lower()  
        if s in {"1", "true", "yes", "y", "on"}:  
            return True  
        if s in {"0", "false", "no", "n", "off"}:  
            return False  
    return None  
  
  
def _selenium_manager_enabled(cfg: Mapping[str, Any]) -> bool:  
    # Force Selenium Manager usage (ignore DRIVER_PATH)  
    v = cfg.get("SELENIUM_MANAGER", cfg.get("USE_SELENIUM_MANAGER"))  
    t = _truthy(v)  
    return bool(t) if t is not None else False  
  
  
def _selenium_manager_fallback_enabled(cfg: Mapping[str, Any]) -> bool:  
    # Allow retry via Selenium Manager when local driver is missing/mismatched.  
    # Default: True (only changes behavior when you would fail anyway).  
    t = _truthy(cfg.get("SELENIUM_MANAGER_FALLBACK"))  
    return True if t is None else bool(t)  
  
  
def _looks_like_driver_version_mismatch(e: BaseException) -> bool:  
    s = str(e).lower()  
    return ("only supports" in s and "version" in s) or ("session not created" in s)  
  
  
def default_download_dir(cfg: Mapping[str, Any]) -> Path:  
    """  
    Resolve and ensure the download directory exists.  
  
    Priority:  
    1) cfg["DOWNLOAD_DIR"]  
    2) env RPA_DOWNLOAD_DIR  
    3) "downloads"  
    """  
    download_dir = (  
        str(cfg.get("DOWNLOAD_DIR") or "").strip() or os.getenv("RPA_DOWNLOAD_DIR", "downloads")  
    )  
    path = Path(download_dir).expanduser().resolve()  
    path.mkdir(parents=True, exist_ok=True)  
    return path  
  
  
def resolve_driver_path(cfg: Mapping[str, Any], browser: str, driver_path: Optional[Path]) -> Path:  
    """  
    Resolve the webdriver binary path.  
  
    Priority:  
    1) explicit driver_path argument  
    2) cfg["DRIVER_PATH"]  
    3) env RPA_DRIVER_PATH  
    4) default per-browser under ./drivers/  
    """  
    if driver_path is not None:  
        return Path(driver_path).expanduser().resolve()  
  
    cfg_path = str(cfg.get("DRIVER_PATH", "") or "").strip()  
    if cfg_path:  
        return Path(cfg_path).expanduser().resolve()  
  
    env_path = str(os.getenv("RPA_DRIVER_PATH", "") or "").strip()  
    if env_path:  
        return Path(env_path).expanduser().resolve()  
  
    default_name = "msedgedriver.exe" if browser == "edge" else "chromedriver.exe"  
    return Path("drivers").joinpath(default_name).expanduser().resolve()  
  
  
def _apply_common_chromium_prefs(options: Union[EdgeOptions, ChromeOptions], download_dir: Path) -> None:  
    prefs = {  
        "download.default_directory": str(download_dir),  
        "download.prompt_for_download": False,  
        "download.directory_upgrade": True,  
        "safebrowsing.enabled": True,  
        # keep off unless you know you need it; some org builds differ  
        "safebrowsing.for_trusted_sources_enabled": False,  
    }  
    options.add_experimental_option("prefs", prefs)  
  
  
def _apply_common_chromium_args(options: Union[EdgeOptions, ChromeOptions], *, headless: bool) -> None:  
    options.add_argument("--no-sandbox")  
    options.add_argument("--disable-dev-shm-usage")  
    options.add_argument("--disable-gpu")  
    options.add_argument("--window-size=1280,800")  
    if headless:  
        options.add_argument("--headless=new")  
  
  
def make_driver(  
    cfg: Mapping[str, Any],  
    *,  
    driver_path: Optional[Path] = None,  
) -> Union[webdriver.Edge, webdriver.Chrome]:  
    """  
    Create a Selenium WebDriver (Chrome or Edge) using a local driver binary,  
    with optional Selenium Manager fallback.  
  
    Mirrors the intake runner’s approach:  
    - download prefs set via Chromium "prefs"  
    - optional attach via remote debuggerAddress  
    """  
    browser = str(cfg.get("BROWSER", "edge")).strip().lower()  
    if browser not in {"edge", "chrome"}:  
        raise ValueError(f"Unsupported BROWSER={browser!r}; expected 'edge' or 'chrome'.")  
  
    download_dir = default_download_dir(cfg)  
    headless = parse_headless(cfg.get("HEADLESS", "false"))  
  
    debug_port = (  
        str(os.getenv("REMOTE_DEBUG_PORT", "")).strip() or str(cfg.get("DEBUG_PORT", "")).strip()  
    )  
  
    force_manager = _selenium_manager_enabled(cfg)  
    allow_manager_fallback = _selenium_manager_fallback_enabled(cfg)  
  
    # detect whether user explicitly pinned a driver path (don’t silently bypass unless forced)  
    cfg_driver = str(cfg.get("DRIVER_PATH", "") or "").strip()  
    env_driver = str(os.getenv("RPA_DRIVER_PATH", "") or "").strip()  
    explicit_driver_pinned = (driver_path is not None) or bool(cfg_driver) or bool(env_driver)  
  
    resolved_driver_path = resolve_driver_path(cfg, browser=browser, driver_path=driver_path)  
  
    def _make_with_manager() -> Union[webdriver.Edge, webdriver.Chrome]:  
        # Selenium Manager path resolution happens inside webdriver.* constructors  
        if browser == "edge":  
            options_m = EdgeOptions()  
            options_m.use_chromium = True  
            _apply_common_chromium_prefs(options_m, download_dir)  
            _apply_common_chromium_args(options_m, headless=headless)  
            if debug_port:  
                options_m.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")  
            return webdriver.Edge(options=options_m)  
        else:  
            options_m = ChromeOptions()  
            _apply_common_chromium_prefs(options_m, download_dir)  
            _apply_common_chromium_args(options_m, headless=headless)  
            if debug_port:  
                options_m.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")  
            return webdriver.Chrome(options=options_m)  
  
    if force_manager:  
        driver: Union[webdriver.Edge, webdriver.Chrome] = _make_with_manager()  
    else:  
        if not resolved_driver_path.exists():  
            # If no pinned driver, try manager before failing.  
            if allow_manager_fallback and not explicit_driver_pinned:  
                driver = _make_with_manager()  
            else:  
                raise FileNotFoundError(  
                    f"{browser.title()} driver not found at: {resolved_driver_path}. "  
                    f"Set DRIVER_PATH/RPA_DRIVER_PATH or place it under drivers/."  
                )  
        else:  
            # Try local driver first, then fallback on mismatch.  
            try:  
                if browser == "edge":  
                    options = EdgeOptions()  
                    options.use_chromium = True  
                    _apply_common_chromium_prefs(options, download_dir)  
                    _apply_common_chromium_args(options, headless=headless)  
                    if debug_port:  
                        options.add_experimental_option(  
                            "debuggerAddress", f"127.0.0.1:{debug_port}"  
                        )  
                    service = EdgeService(executable_path=str(resolved_driver_path))  
                    driver = webdriver.Edge(service=service, options=options)  
                else:  
                    options = ChromeOptions()  
                    _apply_common_chromium_prefs(options, download_dir)  
                    _apply_common_chromium_args(options, headless=headless)  
                    if debug_port:  
                        options.add_experimental_option(  
                            "debuggerAddress", f"127.0.0.1:{debug_port}"  
                        )  
                    service = ChromeService(executable_path=str(resolved_driver_path))  
                    driver = webdriver.Chrome(service=service, options=options)  
            except (SessionNotCreatedException, WebDriverException) as e:  
                if allow_manager_fallback and _looks_like_driver_version_mismatch(e):  
                    driver = _make_with_manager()  
                else:  
                    raise  
  
    implicit_wait = int(cfg.get("IMPLICIT_WAIT", 0) or 0)  
    driver.implicitly_wait(implicit_wait)  
  
    page_timeout = cfg.get("PAGELOAD_TIMEOUT", None)  
    if page_timeout is not None and str(page_timeout).strip() != "":  
        driver.set_page_load_timeout(int(page_timeout))  
  
    return driver  
  
  
def dev_smoke() -> None:  
    assert parse_headless("true") is True  
    assert parse_headless(" False ") is False  
    p = default_download_dir({"DOWNLOAD_DIR": ".dev_tmp/entry_1a_downloads_smoke"})  
    assert p.exists()  
    assert callable(make_driver)  
  
  
if __name__ == "__main__":  
    dev_smoke()  