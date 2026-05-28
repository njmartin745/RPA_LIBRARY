"""
app.py — Simplified Selenium RPA runner
---------------------------------------
Runs a JSON-driven list of RPA steps such as:
    open, wait_for_selector, type_selector, click_selector,
    exec_js, exec_js_file, set_var_from_js,
    repeat (with RPA_BREAK_LOOP support),
    switch_back_to_main_tab, wait_until_only_main_tab_left,
    switch_to_tab_index, close_current_tab, switch_to_default_content

Each step is defined in steps.json with fields like:
    { "action": "click_selector", "strategy": "css", "selector": ".submit-btn" }

This runner executes them in order and logs all actions to console + rpa.log
"""

import os, sys, time, json, argparse, logging, subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from venv import logger
from typing import Optional, Dict, Literal
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options as EdgeOptions
from util.combiner import combine as run_combiner


# ==============================================================
# CONFIG & LOGGING
# ==============================================================
AUDIT_LOG_PATH = Path("data/rpa_audit.jsonl")

def build_manifest_from_excel(
    excel_path: Path,
    manifest_path: Path,
    sheet_name: str,
    key_column: str,
    manifest_key_field: str,
) -> int:
    """
    Read an Excel sheet and build manifest.jsonl with one JSON object per row.

    - excel_path: path to the source Excel file
    - sheet_name: worksheet name to read
    - key_column: Excel column header that contains the primary key
    - manifest_key_field: field name to use in each JSONL entry
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    # Load the sheet
    df = pd.read_excel(excel_path, sheet_name=sheet_name)

    if key_column not in df.columns:
        raise KeyError(
            f"Expected key column '{key_column}' in Excel, "
            f"but available columns are: {list(df.columns)}"
        )

    # Make sure output directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with manifest_path.open("w", encoding="utf-8") as fh:
        for _, row in df.iterrows():
            key_value = row[key_column]
            if pd.isna(key_value):
                continue  # skip empty keys

            entry = {manifest_key_field: str(key_value).strip()}
            fh.write(json.dumps(entry) + "\n")
            count += 1

    return count

def audit_ts() -> str:
    """UTC timestamp for audit records."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_audit(rec: dict) -> None:
    """Append a single JSON record to the long-term audit log."""
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False)
            fh.write("\n")
    except Exception:
        # Never blow up the run because auditing failed; just log it.
        logging.getLogger("audit").exception("Failed to write audit record")

def load_ids_from_manifest(manifest_path: Path, cfg: dict) -> list[str]:
    ids: list[str] = []
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            wid = get_record_key(rec, cfg)
            if wid:
                ids.append(wid)
    return ids

def setup_logging(level: str = "INFO") -> None:
    """Configure logging to both console and rpa.log file."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout),
                  logging.FileHandler("rpa.log", mode="a", encoding="utf-8")]
    )

def load_config(cli_args=None) -> dict:
    """
    Load all configuration values from .env and CLI arguments
    into a unified configuration dictionary.
    """
    load_dotenv()
    url_from_cli = getattr(cli_args, "url", None) if cli_args else None

    return {
        # ----- Core app / login -----
        "URL": url_from_cli or os.getenv("RPA_URL", ""),
        "USERNAME": os.getenv("RPA_USERNAME", ""),
        "PASSWORD": os.getenv("RPA_PASSWORD", ""),

        # ----- Browser / driver -----
        "BROWSER": os.getenv("RPA_BROWSER", "edge").lower(),
        "HEADLESS": os.getenv("HEADLESS", "false"),
        "DEBUG_PORT": os.getenv("RPA_DEBUG_PORT", ""),

        # ----- Paths -----
        "DOWNLOAD_DIR": os.getenv("RPA_DOWNLOAD_DIR", "downloads"),

        # Excel → manifest input source
        "EXCEL_PATH": os.getenv("RPA_EXCEL_PATH", "input/locations.xlsx"),
        "EXCEL_SHEET": os.getenv("RPA_EXCEL_SHEET", "locations"),

        # 🔹 NEW: key column + manifest field
        "EXCEL_KEY_COLUMN": os.getenv("RPA_EXCEL_KEY_COLUMN", "key_ID"),
        "MANIFEST_KEY_FIELD": os.getenv("RPA_MANIFEST_KEY_FIELD", "key_ID"),

        # Manifest system
        "MANIFEST_PATH": os.getenv("RPA_MANIFEST_PATH", "data/manifest.jsonl"),
        "RETRY_MANIFEST_PATH": os.getenv("RPA_RETRY_MANIFEST_PATH", "data/manifest_retry.jsonl"),
        "RECONCILE_PATH": os.getenv("RPA_RECONCILE_PATH", "data/download_reconciliation.jsonl"),
        "AUDIT_LOG": os.getenv("RPA_AUDIT_LOG", "data/rpa_audit.jsonl"),

        # ----- Behavior knobs -----
        "MAX_ATTEMPTS": int(os.getenv("RPA_MAX_ATTEMPTS", "5")),
        "LOG_LEVEL": os.getenv("RPA_LOG_LEVEL", "INFO"),
        "PAGELOAD_TIMEOUT": int(os.getenv("RPA_PAGELOAD_TIMEOUT", "30")),
        "IMPLICIT_WAIT": int(os.getenv("RPA_IMPLICIT_WAIT", "0")),
        "EXPLICIT_WAIT": int(os.getenv("RPA_EXPLICIT_WAIT", "20")),
    }

# ==============================================================
# DRIVER FACTORY
# ==============================================================

def make_driver(cfg):
    """
    Create a Selenium WebDriver using Microsoft Edge (Chromium),
    with a locally managed msedgedriver.exe.
    """
    download_dir = Path(os.getenv("RPA_DOWNLOAD_DIR", "downloads")).expanduser().resolve()
    download_dir.mkdir(parents=True, exist_ok=True)

    headless_raw = str(cfg.get("HEADLESS", "false")).strip().lower()
    headless = headless_raw in {"1", "true", "yes", "on"}

    options = EdgeOptions()
    options.use_chromium = True

    # Download prefs: Edge honors the same Chromium prefs
    prefs = {
        "download.default_directory": str(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "safebrowsing.for_trusted_sources_enabled": False,
    }
    options.add_experimental_option("prefs", prefs)

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")

    if headless:
        options.add_argument("--headless=new")

    # If you *are not* attaching to an existing Edge, leave REMOTE_DEBUG_PORT unset.
    debug_port = os.getenv("REMOTE_DEBUG_PORT")
    if debug_port:
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")

    # >>> The important part: point to your local msedgedriver.exe
    driver_path = Path("drivers/msedgedriver.exe").expanduser().resolve()
    if not driver_path.exists():
        raise FileNotFoundError(f"Edge driver not found at: {driver_path}")

    service = EdgeService(executable_path=str(driver_path))
    driver = webdriver.Edge(service=service, options=options)

    implicit_wait = int(cfg.get("IMPLICIT_WAIT", 10))
    driver.implicitly_wait(implicit_wait)

    return driver


# ==============================================================
# UTILITY HELPERS
# ==============================================================

def by_from_strategy(strategy: str) -> By:
    """Convert a string strategy name to a Selenium By enum."""
    mapping = {
        "id": By.ID, "name": By.NAME, "css": By.CSS_SELECTOR, "xpath": By.XPATH,
        "link_text": By.LINK_TEXT, "partial_link_text": By.PARTIAL_LINK_TEXT,
        "tag_name": By.TAG_NAME, "class_name": By.CLASS_NAME, "aria": "aria"
    }
    s = strategy.strip().lower()
    if s not in mapping:
        raise ValueError(f"Unknown locator strategy: {strategy}")
    return mapping[s]

def get_record_key(rec: dict, cfg: dict) -> str:
    key_field = cfg["MANIFEST_KEY_FIELD"]
    return str(rec.get(key_field, "")).strip()

def wait_for(driver, strategy: str, selector: str, timeout: int):
    """Wait until the given selector is visible and return the element."""
    if strategy == "aria":
        by = By.CSS_SELECTOR
        selector = f'[aria-label="{selector}"]'
    else:
        by = by_from_strategy(strategy)

    wait = WebDriverWait(driver, timeout)
    return wait.until(EC.visibility_of_element_located((by, selector)))

def get_xpath(driver, element) -> str:
    """Return the XPath string of a given element (used for clickability wait)."""
    return driver.execute_script(
        "function xp(el){"
        "if(el.id){return 'id(\"'+el.id+'\")'}"
        "if(el===document.body){return el.tagName.toLowerCase()}"
        "var ix=0;var siblings=el.parentNode.childNodes;"
        "for (var i=0;i<siblings.length;i++){var sib=siblings[i];"
        " if(sib===el){return xp(el.parentNode)+'/'+el.tagName.toLowerCase()+'['+(ix+1)+']'}"
        " if(sib.nodeType===1 && sib.tagName===el.tagName){ix++}}}"
        "return xp(arguments[0]);", element)

def click(driver, strategy: str, selector: str, timeout: int, step_name: str = ""):
    """Wait for an element and perform a click action."""
    log = logging.getLogger("action")
    try:
        el = wait_for(driver, strategy, selector, timeout)
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, get_xpath(driver, el))))
        el.click()
        log.info("Click: %s [%s='%s']", step_name or "element", strategy, selector)
    except Exception:
        capture_failure(driver, f"click_{sanitize(step_name or selector)}")
        log.exception("Click failed: %s", step_name or selector)
        raise

def type_text(driver, strategy: str, selector: str, text: str, timeout: int, step_name: str = ""):
    """Find a field, clear it, and type the provided text."""
    log = logging.getLogger("action")
    try:
        el = wait_for(driver, strategy, selector, timeout)
        el.clear()
        el.send_keys(text)
        log.info("Type: %s [%s='%s'] text='%s'", step_name or "element", strategy, selector, text)
    except Exception:
        capture_failure(driver, f"type_{sanitize(step_name or selector)}")
        log.exception("Type failed: %s", step_name or selector)
        raise

def capture_failure(driver, label: str):
    """Save a screenshot with a timestamp when a step fails."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = f"failure_{label}_{ts}.png"
    try:
        driver.save_screenshot(path)
    except Exception:
        pass

def sanitize(s: str) -> str:
    """Convert a step name into a safe filename string."""
    return (s or "step").lower().replace(" ", "_").replace("/", "_")

def wait_seconds(seconds: float):
    """Pause execution for a given number of seconds."""
    time.sleep(float(seconds))


# ==============================================================
# MAIN RUNNER
# ==============================================================

def run_steps(driver, steps, cfg):
    """
    Execute all steps from a loaded steps.json list.

    Supports nested 'repeat' blocks, variable substitution (${VAR}),
    JS break handling (RPA_BREAK_LOOP), and tab/window management.
    """
    wait = cfg["EXPLICIT_WAIT"]
    log = logging.getLogger("steps")

    # Record main browser window handle (used for tab switching)
    if "MAIN_WINDOW_HANDLE" not in cfg:
        try:
            cfg["MAIN_WINDOW_HANDLE"] = driver.current_window_handle
            log.info("Main window handle recorded.")
        except Exception:
            pass

    # Local resolver for ${VARS} in steps
    def resolve(val):
        if not isinstance(val, str):
            return val
        out = val
        for k, v in cfg.items():
            out = out.replace("${" + k + "}", str(v))
        return out

    # Iterate over each step
    for i, step in enumerate(steps, 1):
        action = step.get("action")
        name = step.get("name", action)
        log.info("Step %d: %s", i, name)

        try:
            # --- Basic selectors & typing ---
            if action == "open":
                url = resolve(step["url"])
                driver.get(url)
                log.info("Opened %s", url)

            elif action == "wait_for_selector":
                strategy = step["strategy"]; selector = step["selector"]
                wait_for(driver, strategy, selector, wait)
                log.info("Visible: [%s='%s']", strategy, selector)

            elif action == "look_for_selector":
                # Non-blocking probe: check if an element exists/visible and
                # stash the result in cfg under the given var name.
                strategy = step["strategy"]
                selector = resolve(step["selector"])
                var_name = step.get("var", "HAS_SELECTOR")

                from selenium.webdriver.common.by import By

                by = None
                if strategy == "css":
                    by = By.CSS_SELECTOR
                elif strategy == "id":
                    by = By.ID
                elif strategy == "xpath":
                    by = By.XPATH
                elif strategy == "name":
                    by = By.NAME
                else:
                    raise ValueError(f"Unsupported strategy for look_for_selector: {strategy!r}")

                try:
                    elems = driver.find_elements(by, selector)
                    # consider it "found" if any element is displayed
                    found = any(e.is_displayed() for e in elems)
                except Exception:
                    found = False

                cfg[var_name] = found
                log.info(
                    "look_for_selector [%s='%s'] -> %s (stored as %s)",
                    strategy, selector, found, var_name,
                )

            elif action == "type_selector":
                strategy = step["strategy"]; selector = step["selector"]
                text = step.get("text")
                if text is None and "env" in step:
                    text = str(cfg.get(step["env"], ""))
                text = resolve(text or "")
                type_text(driver, strategy, selector, text, wait, step_name=step.get("name", selector))

            elif action == "type_selector_secret":
                strategy = step["strategy"]
                selector = step["selector"]

                # Allow fallback to "text" if "secret" isn't present
                raw = step.get("secret") or step.get("text", "")
                text = resolve(raw)

                el = wait_for(driver, strategy, selector, wait)
                el.clear()
                el.send_keys(text)

                # Never log the actual value
                log.info("Type: %s [secret masked]", step.get("name", selector))

            elif action == "click_selector":
                strategy = step["strategy"]; selector = step["selector"]
                click(driver, strategy, selector, wait, step_name=step.get("name", selector))

            elif action == "wait_seconds":
                secs = float(step.get("seconds", 1))
                wait_seconds(secs)
                log.debug("Waited %.3f seconds", secs)

            elif action == "log":
                msg = step.get("message", "")
                msg = resolve(msg)
                log.info(msg)

            # --- JavaScript execution ---
            elif action == "exec_js":
                script = resolve(step["script"])
                result = driver.execute_script(script)
                log.info("Executed JS; result=%r", result)

            elif action == "exec_js_file":
                path = resolve(step["path"])
                if not os.path.exists(path):
                    raise FileNotFoundError(f"JS file not found: {path}")
                with open(path, "r", encoding="utf-8") as fh:
                    script = fh.read()
                script = resolve(script)
                result = driver.execute_script(script)

                name_for_log = os.path.basename(path)

                # If the script returns a structured object {ok, code, message, meta}
                if isinstance(result, dict) and "ok" in result and "message" in result:
                    status = "OK" if result.get("ok") else "FAIL"
                    code = result.get("code") or "NO_CODE"
                    msg = result.get("message")

                    # For the polling probe, keep "not ready" noise at DEBUG
                    if (
                        name_for_log == "probe_frames_and_export_break.js"
                        and result.get("code") == "EXPORT_NOT_READY"
                    ):
                        log.debug(
                            "JS[%s]: %s %s – %s", name_for_log, status, code, msg
                        )
                    else:
                        log.info(
                            "JS[%s]: %s %s – %s", name_for_log, status, code, msg
                        )
                else:
                    # Fallback for scripts that return primitives/legacy shapes
                    log.info("Executed JS file %s; raw result=%r", path, result)


            elif action == "set_var_from_js":
                var_name = step["var"]
                script = resolve(step["script"])
                result = driver.execute_script(script)
                cfg[var_name] = result
                log.info("Set cfg['%s'] = %r", var_name, result)

            # --- Repetition & Loop control ---
            elif action == "repeat":
                # Supports numeric or variable-based iteration counts
                times_raw = step.get("times", 1)
                if isinstance(times_raw, str) and times_raw.startswith("${") and times_raw.endswith("}"):
                    var_name = times_raw[2:-1]
                    try:
                        times = int(cfg.get(var_name, 0))
                    except (TypeError, ValueError):
                        times = 0
                else:
                    times = int(times_raw)

                inner = step.get("steps", [])
                for loop_i in range(times):
                    cfg_loop = dict(cfg)
                    cfg_loop["LOOP_INDEX"] = loop_i

                    # NEW: map LOOP_INDEX → CURRENT_ID from manifest_ids if available
                    manifest_ids = cfg.get("manifest_ids")
                    if isinstance(manifest_ids, (list, tuple)) and 0 <= loop_i < len(manifest_ids):
                        cfg_loop["CURRENT_ID"] = manifest_ids[loop_i]

                    log.debug("Repeat iteration %d/%d", loop_i + 1, times)
                    try:
                        run_steps(driver, inner, cfg_loop)
                        # Optionally propagate inner loop vars back to parent cfg
                        for k, v in cfg_loop.items():
                            if k not in cfg or cfg[k] != v:
                                cfg[k] = v
                    except Exception as e:
                        msg = str(e) or ""
                        if "RPA_BREAK_LOOP" in msg:
                            log.info("Repeat: break signaled at iteration %d; continuing after repeat.", loop_i)
                            break
                        raise
                    

            # --- Tab / Window management ---
            elif action == "switch_back_to_main_tab":
                main = cfg.get("MAIN_WINDOW_HANDLE")
                if not main:
                    handles = driver.window_handles
                    if not handles:
                        raise RuntimeError("No browser windows are open.")
                    main = handles[0]
                    cfg["MAIN_WINDOW_HANDLE"] = main
                driver.switch_to.window(main)
                log.info("Switched back to main tab.")

            elif action == "wait_until_only_main_tab_left":
                # Wait until only one browser tab remains open
                timeout = float(step.get("timeout", 180))
                poll_ms = int(step.get("poll_ms", 400))
                deadline = time.time() + timeout
                last_count = None
                while True:
                    handles = driver.window_handles
                    count = len(handles)
                    if last_count != count:
                        log.info("Tab count: %d", count)
                        last_count = count
                    if count <= 1:
                        if handles:
                            driver.switch_to.window(handles[0])
                        log.info("Only main tab left; continuing.")
                        break
                    if time.time() >= deadline:
                        raise TimeoutError(f"Timed out waiting for only main tab; still have {count} tabs.")
                    time.sleep(poll_ms / 1000.0)

            elif action == "switch_to_tab_index":
                idx = int(step["index"])
                handles = driver.window_handles
                if idx < 0 or idx >= len(handles):
                    raise IndexError(f"Tab index {idx} out of range (0..{len(handles)-1}).")
                driver.switch_to.window(handles[idx])
                log.info("Switched to tab index %d.", idx)

            elif action == "close_current_tab":
                current = driver.current_window_handle
                driver.close()
                handles = [h for h in driver.window_handles if h != current]
                if handles:
                    next_handle = cfg.get("MAIN_WINDOW_HANDLE")
                    if next_handle not in handles:
                        next_handle = handles[-1]
                    driver.switch_to.window(next_handle)
                log.info("Closed current tab and switched.")

            elif action == "switch_to_default_content":
                driver.switch_to.default_content()
                log.info("Switched to default content")

            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            # Detect intentional JS break (throw new Error('RPA_BREAK_LOOP'))
            msg = str(e) or ""
            if "RPA_BREAK_LOOP" in msg:
                log.info("Loop-break signal received inside step '%s'; bubbling up.", name)
                raise RuntimeError("RPA_BREAK_LOOP")

            # Otherwise treat as a real failure
            try:
                capture_failure(driver, sanitize(name))
            except Exception:
                pass
            log.exception("Step failed: %s", name)
            raise

# ==============================================================
# MAIN ENTRY POINT
# ==============================================================

def main():
    """CLI entry: load config, read steps.json, and run the workflow with retries + audit."""
    parser = argparse.ArgumentParser(description="Slim Selenium RPA runner.")
    parser.add_argument("--url", help="Override URL from .env")
    parser.add_argument("--steps", default="steps.json", help="Path to steps JSON")
    args = parser.parse_args()

    cfg = load_config(args)
    setup_logging(cfg["LOG_LEVEL"])
    log = logging.getLogger("main")

    # Stable run identifier for this invocation
    run_id = audit_ts()

    project_root = Path(__file__).resolve().parent

    excel_path = project_root / cfg["EXCEL_PATH"]
    manifest_path = project_root / cfg["MANIFEST_PATH"]
    retry_manifest_path = project_root / cfg["RETRY_MANIFEST_PATH"]

    # ------------------------------------------------------------------
    # 1) Always build a fresh baseline manifest from Excel
    # ------------------------------------------------------------------
    count = build_manifest_from_excel(
        excel_path=excel_path,
        sheet_name=cfg["EXCEL_SHEET"],
        key_column=cfg["EXCEL_KEY_COLUMN"],
        manifest_key_field=cfg["MANIFEST_KEY_FIELD"],
        manifest_path=manifest_path,
    )
    log.info("Built minimal manifest.jsonl with %d keys [%s]", count, cfg["MANIFEST_KEY_FIELD"])

    # Max attempts for retry loop (can override via env)
    max_attempts = int(os.getenv("RPA_MAX_ATTEMPTS", "5"))

    driver = None
    try:
        # ------------------------------------------------------------------
        # 2) Create driver and load steps.json once
        # ------------------------------------------------------------------
        driver = make_driver(cfg)
        steps_path = args.steps or "steps.json"
        if not os.path.exists(steps_path):
            raise FileNotFoundError(f"Steps file not found: {steps_path}")
        with open(steps_path, "r", encoding="utf-8") as f:
            steps = json.load(f)

        # ------------------------------------------------------------------
        # 3) Automatic retry loop
        # ------------------------------------------------------------------
        attempt = 1
        while attempt <= max_attempts:
            log.info("===== RPA attempt %d of %d =====", attempt, max_attempts)

            # 3a) Retry-first manifest selection for this attempt
            active_manifest_path = manifest_path  # default to full manifest

            if retry_manifest_path.exists():
                try:
                    with retry_manifest_path.open("r", encoding="utf-8") as fh:
                        lines = [line.strip() for line in fh if line.strip()]
                    if lines:
                        log.warning(
                            "Retry manifest detected with %d remaining IDs; "
                            "using manifest_retry.jsonl instead of full manifest.",
                            len(lines),
                        )
                        active_manifest_path = retry_manifest_path
                    else:
                        log.info(
                            "Retry manifest exists but is empty; using full manifest.jsonl."
                        )
                except Exception as e:
                    log.error(
                        "Failed reading retry manifest (%s); using full manifest.jsonl.",
                        e,
                    )
            else:
                log.info("No retry manifest detected; using full manifest.jsonl.")

            # 3b) Load IDs from the active manifest
            key_ids = load_ids_from_manifest(active_manifest_path, cfg)
            total = len(key_ids)
            if total == 0:
                log.info(
                    "No %s values to process from %s; nothing to do this attempt.",
                    cfg["MANIFEST_KEY_FIELD"],
                    active_manifest_path,
                )
                
                write_audit(
                    {
                        "run_id": run_id,
                        "attempt": attempt,
                        "phase": "attempt_start",
                        "manifest_source": active_manifest_path.name,
                        "total_ids": 0,
                        "status": "no_ids",
                        "timestamp": audit_ts(),
                    }
                )
                break

            log.info(
                "Loaded %d %s values from %s",
                total,
                cfg["MANIFEST_KEY_FIELD"],
                active_manifest_path,
            )
            
            # Audit attempt start
            write_audit(
                {
                    "run_id": run_id,
                    "attempt": attempt,
                    "phase": "attempt_start",
                    "manifest_source": active_manifest_path.name,
                    "total_ids": total,
                    "status": "running",
                    "timestamp": audit_ts(),
                }
            )

            # 3c) Per-ID loop for this attempt
            for idx, wid in enumerate(key_ids, start=1):
                cfg["CURRENT_ID"] = wid
                log.info("-" * 80)
                log.info(
                    "Location %d/%d (attempt %d): CURRENT_ID=%s",
                    idx,
                    total,
                    attempt,
                    wid,
                )

                try:
                    run_steps(driver, steps, cfg)
                    log.info("Selection OK for %s=%s", cfg["MANIFEST_KEY_FIELD"], wid)
                    log.info("-" * 80)
                    write_audit(
                        {
                            "run_id": run_id,
                            "attempt": attempt,
                            "phase": "download",
                            "manifest_source": active_manifest_path.name,
                            cfg["MANIFEST_KEY_FIELD"]: wid,
                            "status": "ok",
                            "timestamp": audit_ts(),
                        }
                    )
                except Exception:
                    log.exception("Selection FAILED for %s=%s", cfg["MANIFEST_KEY_FIELD"], wid)
                    write_audit(
                        {
                            "run_id": run_id,
                            "attempt": attempt,
                            "phase": "download",
                            "manifest_source": active_manifest_path.name,
                            cfg["MANIFEST_KEY_FIELD"]: wid,
                            "status": "failed",
                            "timestamp": audit_ts(),
                        }
                    )
                    # If you prefer to skip failures and continue, replace `raise` with `continue`
                    raise

            # ------------------------------------------------------------------
            # Final wait to *try* to ensure export tabs are closed
            # (non-fatal: proceed even if this fails)
            # ------------------------------------------------------------------
            log.info("Waiting up to 600 seconds for export tabs to close before renaming...")

            max_wait = 600.0
            poll = 40.0
            start = time.time()

            while True:
                try:
                    handles = driver.window_handles
                    tab_count = len(handles)
                    logging.getLogger("steps").info("Final tab wait: tab count = %d", tab_count)
                except Exception as e:
                    logging.getLogger("steps").warning(
                        "Final tab wait: could not query window handles (%s); proceeding anyway.",
                        e,
                    )
                    break
                
                # Done: 0 or 1 tab is fine
                if tab_count <= 2:
                    logging.getLogger("steps").info(
                        "Final tab wait: all export tabs closed (tab count = %d).",
                        tab_count,
                    )
                    break
                
                elapsed = time.time() - start
                if elapsed >= max_wait:
                    logging.getLogger("steps").warning(
                        "Final tab wait: timed out after %.1fs (tab count = %d); proceeding anyway.",
                        elapsed,
                        tab_count,
                    )
                    break
                
                time.sleep(poll)

            # 3d) Post-processing: rename downloads and build/update retry manifest
            project_root = Path(__file__).resolve().parent

            # Build env for child processes so they can also audit with same run_id/attempt
            child_env = os.environ.copy()
            child_env["RPA_RUN_ID"] = run_id
            child_env["RPA_ATTEMPT"] = str(attempt)

            # 3d-1) Run namer.py to rename downloaded Excel files to <key_id>.xlsx
            namer_path = project_root / "util/namer.py"
            if namer_path.exists():
                log.info("Running namer.py to rename downloaded files...")
                try:
                    subprocess.run(
                        [sys.executable, str(namer_path)],
                        check=True,
                        env=child_env,
                    )
                except subprocess.CalledProcessError as e:
                    log.error("namer.py failed with exit code %s", e.returncode)
                    write_audit(
                        {
                            "run_id": run_id,
                            "attempt": attempt,
                            "phase": "rename",
                            "status": "namer_error",
                            "exit_code": e.returncode,
                            "timestamp": audit_ts(),
                        }
                    )
                    raise
            else:
                log.warning("namer.py not found; skipping rename step.")
                write_audit(
                    {
                        "run_id": run_id,
                        "attempt": attempt,
                        "phase": "rename",
                        "status": "namer_missing",
                        "timestamp": audit_ts(),
                    }
                )

            # 3d-2) Run reconcile_downloads.py to produce/update manifest_retry.jsonl
            reconcile_path = project_root / "util/reconcile_downloads.py"
            if reconcile_path.exists():
                log.info("Running reconcile_downloads.py to generate retry manifest...")
                try:
                    subprocess.run(
                        [sys.executable, str(reconcile_path)],
                        check=True,
                        env=child_env,
                    )
                except subprocess.CalledProcessError as e:
                    log.error(
                        "reconcile_downloads.py failed with exit code %s",
                        e.returncode,
                    )
                    write_audit(
                        {
                            "run_id": run_id,
                            "attempt": attempt,
                            "phase": "reconcile",
                            "status": "reconcile_error",
                            "exit_code": e.returncode,
                            "timestamp": audit_ts(),
                        }
                    )
                    raise
            else:
                log.warning(
                    "reconcile_downloads.py not found; skipping reconciliation step."
                )
                write_audit(
                    {
                        "run_id": run_id,
                        "attempt": attempt,
                        "phase": "reconcile",
                        "status": "reconcile_missing",
                        "timestamp": audit_ts(),
                    }
                )

            # 3e) Check if there is anything left to retry
            remaining = 0
            if retry_manifest_path.exists():
                try:
                    with retry_manifest_path.open("r", encoding="utf-8") as fh:
                        remaining_lines = [line.strip() for line in fh if line.strip()]
                    remaining = len(remaining_lines)
                except Exception as e:
                    log.error(
                        "Failed reading retry manifest after attempt %d (%s).",
                        attempt,
                        e,
                    )

            if remaining == 0:
                log.info(
                    "No remaining IDs in manifest_retry.jsonl after attempt %d; all done.",
                    attempt,
                )
                write_audit(
                    {
                        "run_id": run_id,
                        "attempt": attempt,
                        "phase": "attempt_complete",
                        "status": "all_downloaded",
                        "timestamp": audit_ts(),
                    }
                )
                break

            log.warning(
                "After attempt %d, %d IDs still remain in retry manifest; "
                "will run another attempt.",
                attempt,
                remaining,
            )
            write_audit(
                {
                    "run_id": run_id,
                    "attempt": attempt,
                    "phase": "attempt_complete",
                    "status": "remaining",
                    "remaining_ids": remaining,
                    "timestamp": audit_ts(),
                }
            )
            attempt += 1

        # After the loop, if we've exhausted attempts and still have remaining IDs, log a summary
        if attempt > max_attempts and retry_manifest_path.exists():
            try:
                with retry_manifest_path.open("r", encoding="utf-8") as fh:
                    leftover_recs = [
                        json.loads(line) for line in fh if line.strip()
                    ]
                leftover_ids = [
                    get_record_key(rec, cfg)
                    for rec in leftover_recs
                    if get_record_key(rec, cfg)
                ]

                if leftover_ids:
                    log.error(
                        "Max attempts (%d) reached; %d %s still missing. "
                        "See manifest_retry.jsonl for details.",
                        max_attempts,
                        len(leftover_ids),
                        cfg["MANIFEST_KEY_FIELD"],
                    )
                    write_audit(
                        {
                            "run_id": run_id,
                            "attempt": max_attempts,
                            "phase": "completion",
                            "status": "incomplete",
                            "remaining_ids": leftover_ids,
                            "timestamp": audit_ts(),
                        }
                    )
                else:
                    write_audit(
                        {
                            "run_id": run_id,
                            "attempt": max_attempts,
                            "phase": "completion",
                            "status": "complete",
                            "timestamp": audit_ts(),
                        }
                    )
            except Exception:
                log.exception("Failed to read final retry manifest after max attempts.")

        else:
            # Normal completion (no leftover or we broke early)
            write_audit(
                {
                    "run_id": run_id,
                    "attempt": attempt,
                    "phase": "completion",
                    "status": "complete",
                    "timestamp": audit_ts(),
                }
            )

        # ------------------------------------------------------------------
        # Optional post-run combiner: merge all cleaned .xlsx into one CSV
        # ------------------------------------------------------------------
        run_combiner_flag = (os.getenv("RUN_COMBINER", "N") or "N").strip().lower()
        if run_combiner_flag in {"y", "yes", "true", "1", "on"}:
            log.info("RUN_COMBINER is enabled; running combiner utility...")
            try:
                run_combiner()
            except Exception:
                # Log combiner failure but do NOT treat it as an RPA failure.
                log.exception("Combiner failed after main RPA run.")
        else:
            log.info("RUN_COMBINER not enabled; skipping combiner step.")

        log.info("RPA workflow (with retries) completed.")

    except Exception as e:
        log.exception("RPA failed: %s", e)
        write_audit(
            {
                "run_id": run_id,
                "phase": "completion",
                "status": "failed",
                "error": str(e),
                "timestamp": audit_ts(),
            }
        )
        sys.exit(1)
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()