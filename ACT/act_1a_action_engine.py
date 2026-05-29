"""
ACT-1A — Canonical Action Execution Layer

Purpose
-------
Execute normalized workflow steps against a live browser session.

This module serves as the primary runtime action engine and provides
the standard execution surface used by workflow runners, deploy bundles,
and future orchestration layers.

Responsibilities
----------------
- Execute workflow actions sequentially
- Resolve workflow variables (${TOKEN})
- Resolve selector references (selector_ref)
- Interact with Selenium WebDriver
- Record step outcomes and execution timing
- Enforce fail-fast execution behavior
- Execute JavaScript actions
- Support download monitoring and validation
- Capture runtime failures with structured diagnostics

Supported Action Categories
---------------------------
Navigation
- open
- get

Synchronization
- wait
- wait_for_element

Element Interaction
- click
- type
- select
- hover
- scroll
- element lookup

JavaScript
- inline script execution
- external script execution

Downloads
- download_wait
- file existence validation
- file stability validation

Assertions
- runtime expression evaluation
- workflow validation checks

Architecture Position
---------------------
CAPTURE
    ↓
SNAP
    ↓
WORKFLOW-1E
    Normalize
    ↓
WORKFLOW-1F
    Selector Ref First
    ↓
BUILD
    ↓
DEPLOY_BUNDLE
    ↓
VAL-2A
    Validate
    ↓
WORKFLOW-1G
    Load Bundle
    ↓
RUN-1E
    Runner Adapter
    ↓
ACT-1A
    Action Engine
    ↓
SELENIUM

Public API
----------
StepOutcome
ActionEngineError
run_actions(...)
outcomes_as_dicts(...)
outcomes_all_ok(...)
dev_smoke(...)

Dependencies
------------
selenium
NAV-1A

Status
------
Audited

Notes
-----
This is the canonical workflow execution engine.

All workflow execution paths ultimately converge here before
interacting with Selenium WebDriver.

The module provides the foundation for future healing,
telemetry, reporting, replay, and multi-agent execution.
"""
  
from __future__ import annotations  
  
import re  
import time  
import traceback  
from dataclasses import dataclass, asdict  
from pathlib import Path  
from typing import Any, Iterable, MutableMapping, Optional  
  
from selenium.common.exceptions import (  
    ElementClickInterceptedException,  
    JavascriptException,  
    StaleElementReferenceException,  
    TimeoutException,  
    WebDriverException,  
)  
from selenium.webdriver.common.by import By  
from selenium.webdriver.remote.webdriver import WebDriver  
from selenium.webdriver.support import expected_conditions as EC  
from selenium.webdriver.support.select import Select  
from selenium.webdriver.support.ui import WebDriverWait  
  
from NAV.nav_1a_selenium_helpers import wait_for_download as nav_wait_for_download  
  
__all__ = [  
    "StepOutcome",  
    "ActionEngineError",  
    "run_actions",  
    "outcomes_as_dicts",  
    "outcomes_all_ok",  
    "dev_smoke",  
]  
  
_UNRESOLVED_TOKEN_RE = re.compile(r"\$\{([^}]+)\}")  
  
  
@dataclass  
class StepOutcome:  
    index: int  
    action: str  
    name: str  
    ok: bool  
    started_at: float  
    ended_at: float  
    duration_s: float  
    result: Any = None  
    error_type: Optional[str] = None  
    error_message: Optional[str] = None  
    traceback: Optional[str] = None  
  
  
class ActionEngineError(RuntimeError):  
    """  
    Raised when a step fails under fail-fast behavior.  
  
    Attributes  
    ----------  
    outcomes: list[StepOutcome]  
        Outcomes recorded up to (and including) the failing step.  
    step_index: int  
        0-based index of failing step in `steps`.  
    """  
  
    def __init__(  
        self,  
        message: str,  
        *,  
        outcomes: list[StepOutcome],  
        step_index: int,  
        cause: BaseException,  
    ) -> None:  
        super().__init__(message)  
        self.outcomes = outcomes  
        self.step_index = step_index  
        self.__cause__ = cause  
  
  
def outcomes_as_dicts(outcomes: Iterable[StepOutcome]) -> list[dict[str, Any]]:  
    """Convert outcomes to JSON-serializable dicts."""  
    return [asdict(o) for o in outcomes]  
  
  
def outcomes_all_ok(outcomes: Iterable[StepOutcome]) -> bool:  
    return all(bool(o.ok) for o in outcomes)  
  
  
# -------------------------  
# Helpers  
# -------------------------  
def _truthy(v: Any) -> bool:  
    s = str(v or "").strip().lower()  
    return s in {"1", "true", "yes", "on"}  
  
  
def _default_timeout(cfg: MutableMapping[str, Any], fallback: int = 20) -> int:  
    try:  
        return int(cfg.get("EXPLICIT_WAIT", fallback))  
    except Exception:  
        return fallback  
  
  
def _deep_resolve(obj: Any, cfg: MutableMapping[str, Any]) -> Any:  
    """  
    Recursively resolve ${KEY} tokens in strings using cfg values.  
    Lists and dicts are walked; other objects are returned unchanged.  
    """  
    if isinstance(obj, str):  
        out = obj  
        for k, v in cfg.items():  
            out = out.replace("${" + str(k) + "}", str(v))  
        return out  
    if isinstance(obj, list):  
        return [_deep_resolve(x, cfg) for x in obj]  
    if isinstance(obj, dict):  
        return {k: _deep_resolve(v, cfg) for k, v in obj.items()}  
    return obj  
  
  
def _assert_no_unresolved_tokens(value: str, *, field: str) -> str:  
    """  
    Fail fast when required strings still contain ${TOKENS} after resolution.  
    Applied only to critical fields (e.g., url, selector).  
    """  
    tokens = _UNRESOLVED_TOKEN_RE.findall(value or "")  
    if tokens:  
        uniq = sorted({t.strip() for t in tokens if t and str(t).strip()})  
        raise ValueError(f"Unresolved ${{...}} tokens in {field}: {uniq}")  
    return value  
  
  
def _by_from_string(by: str) -> By:  
    b = (by or "").strip().lower()  
    if b in {"css", "css_selector"}:  
        return By.CSS_SELECTOR  
    if b == "xpath":  
        return By.XPATH  
    if b == "id":  
        return By.ID  
    if b == "name":  
        return By.NAME  
    raise ValueError(f"Unsupported locator by={by!r}; use 'css' or 'xpath' (preferred).")  
  
  
def _wait_for_element(  
    driver: WebDriver,  
    *,  
    by: By,  
    selector: str,  
    timeout: int,  
    condition: str,  
):  
    cond = (condition or "visible").strip().lower()  
    wait = WebDriverWait(driver, timeout)  
  
    if cond == "present":  
        return wait.until(EC.presence_of_element_located((by, selector)))  
    if cond == "visible":  
        return wait.until(EC.visibility_of_element_located((by, selector)))  
    if cond == "clickable":  
        return wait.until(EC.element_to_be_clickable((by, selector)))  
    raise ValueError(f"Unknown condition={condition!r}; use present|visible|clickable.")  
  
  
def _scroll_into_view(driver: WebDriver, element) -> None:  
    try:  
        driver.execute_script(  
            "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",  
            element,  
        )  
    except Exception:  
        return  
  
  
def _element_snapshot(element) -> dict[str, Any]:  
    try:  
        tag = element.tag_name  
    except Exception:  
        tag = None  
    try:  
        text = element.text  
    except Exception:  
        text = None  
    try:  
        displayed = element.is_displayed()  
    except Exception:  
        displayed = None  
    try:  
        enabled = element.is_enabled()  
    except Exception:  
        enabled = None  
    return {"tag": tag, "text": text, "displayed": displayed, "enabled": enabled}  
  
  
def _read_js(step: dict[str, Any]) -> str:  
    if step.get("script") is not None:  
        return str(step["script"])  
    if step.get("path") is not None:  
        p = Path(str(step["path"])).expanduser()  
        if not p.exists():  
            raise FileNotFoundError(f"JS file not found: {p}")  
        return p.read_text(encoding="utf-8")  
    raise ValueError("js action requires either 'script' (inline) or 'path' (file).")  
  
  
def _ensure_js_contract(result: Any) -> dict[str, Any]:  
    if not isinstance(result, dict):  
        raise RuntimeError(f"JS must return an object/dict with {{ok: bool}}; got {type(result).__name__}")  
    ok = result.get("ok", None)  
    if not isinstance(ok, bool):  
        raise RuntimeError("JS return contract violation: result['ok'] must be boolean.")  
    return result  
  
  
def _safe_assert_eval(expr: str, cfg: MutableMapping[str, Any]) -> bool:  
    allowed_builtins = {  
        "len": len,  
        "any": any,  
        "all": all,  
        "min": min,  
        "max": max,  
        "sum": sum,  
        "sorted": sorted,  
        "str": str,  
        "int": int,  
        "float": float,  
        "bool": bool,  
    }  
    locals_env: dict[str, Any] = {"cfg": cfg}  
    for k, v in cfg.items():  
        if isinstance(k, str) and k.isidentifier():  
            locals_env[k] = v  
    return bool(eval(expr, {"__builtins__": allowed_builtins}, locals_env))  
  
  
def _download_wait(  
    *,  
    cfg: MutableMapping[str, Any],  
    path: Optional[str],  
    filename: Optional[str],  
    glob_pat: Optional[str],  
    timeout: int,  
    poll_s: float = 0.25,  
    stable_s: float = 0.75,  
) -> dict[str, Any]:  
    from pathlib import Path as _Path  
  
    download_dir = _Path(str(cfg.get("DOWNLOAD_DIR", "downloads"))).expanduser().resolve()  
    deadline = time.time() + timeout  
  
    def stable_nonzero(p: _Path) -> bool:  
        if not p.exists():  
            return False  
        try:  
            size1 = p.stat().st_size  
        except OSError:  
            return False  
        if size1 <= 0:  
            return False  
        t0 = time.time()  
        while time.time() - t0 < stable_s:  
            time.sleep(min(poll_s, 0.25))  
            try:  
                size2 = p.stat().st_size  
            except OSError:  
                return False  
            if size2 != size1:  
                return False  
        return True  
  
    if path:  
        target = _Path(path).expanduser().resolve()  
        while time.time() < deadline:  
            if stable_nonzero(target):  
                return {"ok": True, "path": str(target), "mode": "path"}  
            time.sleep(poll_s)  
        raise TimeoutError(f"download_wait timeout: file not found/stable: {target}")  
  
    if filename:  
        target = (download_dir / filename).resolve()  
        while time.time() < deadline:  
            if stable_nonzero(target):  
                return {"ok": True, "path": str(target), "mode": "filename"}  
            time.sleep(poll_s)  
        raise TimeoutError(f"download_wait timeout: file not found/stable: {target}")  
  
    if glob_pat:  
        while time.time() < deadline:  
            matches = sorted(download_dir.glob(glob_pat))  
            for p in matches:  
                if stable_nonzero(p):  
                    return {"ok": True, "path": str(p.resolve()), "mode": "glob", "glob": glob_pat}  
            time.sleep(poll_s)  
        raise TimeoutError(f"download_wait timeout: no stable match for glob {glob_pat!r} in {download_dir}")  
  
    raise ValueError("download_wait requires one of: path, filename, glob")  
  
  
def _resolve_selector(step: dict[str, Any], cfg: MutableMapping[str, Any]) -> str:  
    """  
    Strict selector resolution:  
    - prefer step['selector']  
    - else try step['selector_ref'] via common cfg registries (best-effort)  
    - else raise (do NOT pretend success)  
    """  
    sel = step.get("selector")  
    if isinstance(sel, str) and sel.strip():  
        return sel.strip()  
  
    ref = step.get("selector_ref")  
    if isinstance(ref, str) and ref.strip():  
        ref = ref.strip()  
        for key in ("SELECTORS", "SELECTOR_REGISTRY", "REGISTRY_SELECTORS"):  
            reg = cfg.get(key)  
            if isinstance(reg, dict):  
                v = reg.get(ref)  
                if isinstance(v, str) and v.strip():  
                    return v.strip()  
        raise ValueError(  
            f"selector_ref {ref!r} could not be resolved. "  
            "Ensure selector registry is loaded into cfg (e.g. cfg['SELECTORS'])."  
        )  
  
    raise ValueError("Step missing required field: 'selector' (or 'selector_ref').")  
  
  
# -------------------------  
# Action implementations  
# -------------------------  
def _act_get(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    url = str(step["url"])  
    _assert_no_unresolved_tokens(url, field="url")  
    driver.get(url)  
    return {"url": url}  
  
  
def _act_open(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    # SCHEMA alias of get  
    url = str(step["url"])  
    _assert_no_unresolved_tokens(url, field="url")  
    driver.get(url)  
    return {"url": url}  
  
  
def _act_wait(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    seconds = float(step.get("seconds", 0))  
    time.sleep(seconds)  
    return {"slept": seconds}  
  
  
def _act_wait_for_element(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    by = _by_from_string(str(step.get("by", "css")))  
    selector = str(step["selector"])  
    timeout = int(step.get("timeout") or _default_timeout(cfg))  
    condition = str(step.get("condition", "visible"))  
    el = _wait_for_element(driver, by=by, selector=selector, timeout=timeout, condition=condition)  
    snap = _element_snapshot(el)  
    save_as = step.get("save_as")  
    if save_as:  
        cfg[str(save_as)] = snap  
    return snap  
  
  
def _act_wait_for_selector(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    # REQUIREMENT: MUST fail if element is not found within timeout  
    by = _by_from_string(str(step.get("by", "css")))  
    selector = _resolve_selector(step, cfg)  
    _assert_no_unresolved_tokens(selector, field="selector")  
    timeout = int(step.get("timeout") or _default_timeout(cfg))  
    condition = str(step.get("condition", "visible"))  
  
    try:  
        el = _wait_for_element(driver, by=by, selector=selector, timeout=timeout, condition=condition)  
    except TimeoutException as e:  
        raise RuntimeError(  
            f"wait_for_selector failed: not found / condition not met within {timeout}s "  
            f"(by={by!s}, selector={selector!r}, condition={condition!r})"  
        ) from e  
  
    # Post-condition hardening: detect immediate staleness / unexpected non-ready state.  
    cond = (condition or "visible").strip().lower()  
    try:  
        if cond in {"visible", "clickable"} and not el.is_displayed():  
            raise RuntimeError(  
                f"wait_for_selector failed: element not displayed after wait "  
                f"(by={by!s}, selector={selector!r}, condition={condition!r})"  
            )  
        if cond == "clickable" and not el.is_enabled():  
            raise RuntimeError(  
                f"wait_for_selector failed: element not enabled after wait "  
                f"(by={by!s}, selector={selector!r})"  
            )  
    except StaleElementReferenceException as e:  
        raise RuntimeError(  
            f"wait_for_selector failed: element became stale immediately after wait "  
            f"(by={by!s}, selector={selector!r}, condition={condition!r})"  
        ) from e  
  
    snap = _element_snapshot(el)  
    save_as = step.get("save_as")  
    if save_as:  
        cfg[str(save_as)] = snap  
    return snap  
  
  
def _act_click(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    by = _by_from_string(str(step.get("by", "css")))  
    selector = str(step["selector"])  
    timeout = int(step.get("timeout") or _default_timeout(cfg))  
  
    el = _wait_for_element(driver, by=by, selector=selector, timeout=timeout, condition="clickable")  
    _scroll_into_view(driver, el)  
    try:  
        el.click()  
        return {"clicked": True}  
    except StaleElementReferenceException:  
        el = _wait_for_element(driver, by=by, selector=selector, timeout=timeout, condition="clickable")  
        _scroll_into_view(driver, el)  
        el.click()  
        return {"clicked": True, "retry": "stale"}  
    except ElementClickInterceptedException:  
        # canonical click keeps JS fallback  
        try:  
            driver.execute_script("arguments[0].click(); return true;", el)  
            return {"clicked": True, "fallback": "js"}  
        except JavascriptException:  
            raise  
  
  
def _act_click_selector(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    # REQUIREMENT: MUST fail if element is not found OR not clickable  
    by = _by_from_string(str(step.get("by", "css")))  
    selector = _resolve_selector(step, cfg)  
    _assert_no_unresolved_tokens(selector, field="selector")  
    timeout = int(step.get("timeout") or _default_timeout(cfg))  
  
    try:  
        el = _wait_for_element(driver, by=by, selector=selector, timeout=timeout, condition="clickable")  
        _scroll_into_view(driver, el)  
        el.click()  
        return {"clicked": True}  
    except TimeoutException as e:  
        raise RuntimeError(  
            f"click_selector failed: element not found/clickable within {timeout}s "  
            f"(by={by!s}, selector={selector!r})"  
        ) from e  
    except StaleElementReferenceException as e:  
        # deterministic single retry  
        try:  
            el = _wait_for_element(driver, by=by, selector=selector, timeout=timeout, condition="clickable")  
            _scroll_into_view(driver, el)  
            el.click()  
            return {"clicked": True, "retry": "stale"}  
        except Exception as e2:  
            raise RuntimeError(  
                f"click_selector failed after stale retry (by={by!s}, selector={selector!r}): "  
                f"{type(e2).__name__}: {e2}"  
            ) from e2  
    except ElementClickInterceptedException as e:  
        raise RuntimeError(  
            f"click_selector failed: click intercepted (by={by!s}, selector={selector!r}): {e}"  
        ) from e  
    except WebDriverException as e:  
        raise RuntimeError(  
            f"click_selector failed (by={by!s}, selector={selector!r}): {type(e).__name__}: {e}"  
        ) from e  
  
  
def _act_type(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    by = _by_from_string(str(step.get("by", "css")))  
    selector = str(step["selector"])  
    text = str(step.get("text", ""))  
    timeout = int(step.get("timeout") or _default_timeout(cfg))  
    clear = bool(step.get("clear", True))  
    click_first = bool(step.get("click_first", True))  
  
    el = _wait_for_element(driver, by=by, selector=selector, timeout=timeout, condition="visible")  
    _scroll_into_view(driver, el)  
    if click_first:  
        el_click = _wait_for_element(driver, by=by, selector=selector, timeout=timeout, condition="clickable")  
        _scroll_into_view(driver, el_click)  
        el_click.click()  
        el = el_click  
  
    if clear:  
        el.clear()  
  
    el.send_keys(text)  
    return {"typed": True, "chars": len(text)}  
  
  
def _act_type_selector_secret(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    # REQUIREMENT: MUST fail if element is not found  
    by = _by_from_string(str(step.get("by", "css")))  
    selector = _resolve_selector(step, cfg)  
    _assert_no_unresolved_tokens(selector, field="selector")  
    timeout = int(step.get("timeout") or _default_timeout(cfg))  
  
    secret_val = step.get("secret", None)  
    if secret_val is None:  
        # legacy compatibility  
        secret_val = step.get("text", None)  
    if secret_val is None:  
        raise ValueError("type_selector_secret requires 'secret' (or legacy 'text').")  
  
    click_first = bool(step.get("click_first", True))  
    clear = bool(step.get("clear", True))  
  
    try:  
        el = _wait_for_element(driver, by=by, selector=selector, timeout=timeout, condition="visible")  
        _scroll_into_view(driver, el)  
  
        if click_first:  
            el2 = _wait_for_element(driver, by=by, selector=selector, timeout=timeout, condition="clickable")  
            _scroll_into_view(driver, el2)  
            el2.click()  
            el = el2  
  
        if clear:  
            el.clear()  
  
        el.send_keys(str(secret_val))  
        return {"typed": True}  
    except TimeoutException as e:  
        raise RuntimeError(  
            f"type_selector_secret failed: element not found within {timeout}s (by={by!s}, selector={selector!r})"  
        ) from e  
    except WebDriverException as e:  
        raise RuntimeError(  
            f"type_selector_secret failed (by={by!s}, selector={selector!r}): {type(e).__name__}: {e}"  
        ) from e  
  
  
def _act_select(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    by = _by_from_string(str(step.get("by", "css")))  
    selector = str(step["selector"])  
    timeout = int(step.get("timeout") or _default_timeout(cfg))  
  
    el = _wait_for_element(driver, by=by, selector=selector, timeout=timeout, condition="visible")  
    _scroll_into_view(driver, el)  
    sel = Select(el)  
  
    if "by_text" in step and step["by_text"] is not None:  
        txt = str(step["by_text"])  
        sel.select_by_visible_text(txt)  
        return {"selected": "text", "value": txt}  
    if "by_value" in step and step["by_value"] is not None:  
        val = str(step["by_value"])  
        sel.select_by_value(val)  
        return {"selected": "value", "value": val}  
    if "by_index" in step and step["by_index"] is not None:  
        idx = int(step["by_index"])  
        sel.select_by_index(idx)  
        return {"selected": "index", "value": idx}  
  
    raise ValueError("select action requires one of: by_text, by_value, by_index")  
  
  
def _act_js(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    script = _read_js(step)  
    result = driver.execute_script(script)  
    result = _ensure_js_contract(result)  
    if result["ok"] is False:  
        code = result.get("code", "")  
        msg = result.get("message", "JS returned ok:false")  
        raise RuntimeError(f"JS step failed (ok:false) code={code!r} message={msg!r}")  
    save_as = step.get("save_as")  
    if save_as:  
        cfg[str(save_as)] = result  
    return result  
  
  
def _act_switch_frame(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    target = str(step.get("target", "") or "").strip().lower()  
    if target in {"default", "root"}:  
        driver.switch_to.default_content()  
        return {"frame": "default"}  
    if target == "parent":  
        driver.switch_to.parent_frame()  
        return {"frame": "parent"}  
  
    if "index" in step and step["index"] is not None:  
        idx = int(step["index"])  
        driver.switch_to.frame(idx)  
        return {"frame": "index", "index": idx}  
  
    if "by" in step and "selector" in step:  
        by = _by_from_string(str(step.get("by", "css")))  
        selector = str(step["selector"])  
        timeout = int(step.get("timeout") or _default_timeout(cfg))  
        frame_el = _wait_for_element(driver, by=by, selector=selector, timeout=timeout, condition="present")  
        driver.switch_to.frame(frame_el)  
        return {"frame": "element", "by": str(step.get("by")), "selector": selector}  
  
    raise ValueError("switch_frame requires target=default|parent, or index, or by+selector")  
  
  
def _act_switch_tab(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    if "MAIN_WINDOW_HANDLE" not in cfg:  
        cfg["MAIN_WINDOW_HANDLE"] = driver.current_window_handle  
  
    if step.get("handle") is not None:  
        h = str(step["handle"])  
        driver.switch_to.window(h)  
        return {"tab": "handle", "handle": h}  
  
    if step.get("index") is not None:  
        idx = int(step["index"])  
        handles = driver.window_handles  
        if idx < 0 or idx >= len(handles):  
            raise IndexError(f"switch_tab index {idx} out of range for {len(handles)} handles")  
        driver.switch_to.window(handles[idx])  
        return {"tab": "index", "index": idx, "handle": handles[idx]}  
  
    target = str(step.get("target", "") or "").strip().lower()  
    if target == "main":  
        h = str(cfg["MAIN_WINDOW_HANDLE"])  
        driver.switch_to.window(h)  
        return {"tab": "main", "handle": h}  
    if target == "last":  
        h = driver.window_handles[-1]  
        driver.switch_to.window(h)  
        return {"tab": "last", "handle": h}  
  
    raise ValueError("switch_tab requires one of: target=main|last, index, handle")  
  
  
def _act_switch_back_to_main_tab(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    # SCHEMA action convenience  
    return _act_switch_tab(driver, {"target": "main"}, cfg)  
  
  
def _act_assert(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    expr = str(step["expr"])  
    ok = _safe_assert_eval(expr, cfg)  
    if not ok:  
        raise AssertionError(f"Assertion failed: {expr}")  
    return {"asserted": True, "expr": expr}  
  
  
def _act_download_wait(driver: WebDriver, step: dict[str, Any], cfg: MutableMapping[str, Any]) -> Any:  
    timeout = int(step.get("timeout") or _default_timeout(cfg))  
    info = _download_wait(  
        cfg=cfg,  
        path=step.get("path"),  
        filename=step.get("filename"),  
        glob_pat=step.get("glob"),  
        timeout=timeout,  
    )  
    save_as = step.get("save_as")  
    if save_as:  
        cfg[str(save_as)] = info["path"]  
    return info  
  
  
_ACTIONS: dict[str, Any] = {  
    # Canonical actions  
    "get": _act_get,  
    "wait": _act_wait,  
    "wait_for_element": _act_wait_for_element,  
    "click": _act_click,  
    "type": _act_type,  
    "select": _act_select,  
    "js": _act_js,  
    "switch_frame": _act_switch_frame,  
    "switch_tab": _act_switch_tab,  
    "assert": _act_assert,  
    "download_wait": _act_download_wait,  
    # SCHEMA actions (STRICT)  
    "open": _act_open,  
    "wait_for_selector": _act_wait_for_selector,  
    "click_selector": _act_click_selector,  
    "type_selector_secret": _act_type_selector_secret,  
    # SCHEMA aliases  
    "exec_js": _act_js,  
    "exec_js_file": _act_js,  
    "switch_back_to_main_tab": _act_switch_back_to_main_tab,  
}  
  
  
def run_actions(  
    driver: WebDriver,  
    steps: list[dict[str, Any]],  
    cfg: MutableMapping[str, Any],  
    *,  
    fail_fast: bool = True,  
) -> list[StepOutcome]:  
    """  
    Execute steps against driver, mutating cfg as needed.  
  
    Returns list[StepOutcome]. Under fail-fast behavior, raises ActionEngineError  
    after recording the failing StepOutcome (unless step has continue_on_error).  
    """  
    outcomes: list[StepOutcome] = []  
    # Aggregate markers for higher layers (Runner/Report) when non-fail-fast execution continues.  
    cfg["ACT_LAST_CALL_ALL_OK"] = True  
  
    for idx, raw_step in enumerate(steps):  
        started = time.time()  
  
        step = _deep_resolve(raw_step, cfg)  
        action = str(step.get("action", "")).strip()  
        name = str(step.get("name") or action or f"step_{idx}").strip()  
  
        outcome = StepOutcome(  
            index=idx,  
            action=action,  
            name=name,  
            ok=False,  
            started_at=started,  
            ended_at=started,  
            duration_s=0.0,  
            result=None,  
            error_type=None,  
            error_message=None,  
            traceback=None,  
        )  
  
        try:  
            if not action:  
                raise ValueError("Step missing required field: 'action'")  
  
            fn = _ACTIONS.get(action)  
            if fn is None:  
                raise ValueError(f"Unknown action: {action!r}")  
  
            result = fn(driver, step, cfg)  
  
            outcome.ok = True  
            outcome.result = result  
  
        except Exception as e:  
            outcome.ok = False  
            outcome.error_type = type(e).__name__  
            outcome.error_message = str(e)  
            outcome.traceback = traceback.format_exc()  
  
            step_continue = _truthy(step.get("continue_on_error", False))  
            if fail_fast and not step_continue:  
                # IMPORTANT: do not append twice; include failing outcome in exception payload.  
                raise ActionEngineError(  
                    f"Action failed at step {idx} ({action}): {outcome.error_message}",  
                    outcomes=outcomes + [outcome],  
                    step_index=idx,  
                    cause=e,  
                ) from e  
  
        finally:  
            outcome.ended_at = time.time()  
            outcome.duration_s = outcome.ended_at - outcome.started_at  
            outcomes.append(outcome)  
            if not outcome.ok:  
                cfg["ACT_LAST_CALL_ALL_OK"] = False  
                cfg["ACT_ANY_FAILED"] = True  
  
    return outcomes  
  
  
def dev_smoke() -> None:  
    # Ensure required SCHEMA actions are present and strict selector resolution fails fast.  
    assert "wait_for_selector" in _ACTIONS  
    assert "click_selector" in _ACTIONS  
    assert "type_selector_secret" in _ACTIONS  
  
    cfg: MutableMapping[str, Any] = {}  
    try:  
        _resolve_selector({"selector_ref": "LOGIN_USERNAME"}, cfg)  
        raise AssertionError("Expected selector_ref resolution to fail without registry")  
    except ValueError:  
        pass  
  
    # JS contract enforcement smoke  
    try:  
        _ensure_js_contract({"ok": True})  
    except Exception as e:  
        raise AssertionError(f"JS contract smoke failed: {e}") from e  
  
    # Unresolved token enforcement smoke (critical fields)  
    try:  
        _assert_no_unresolved_tokens("${URL}", field="url")  
        raise AssertionError("Expected unresolved token check to fail")  
    except ValueError:  
        pass  