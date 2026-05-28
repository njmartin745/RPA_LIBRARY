# REASON/reason_1a_diagnose.py  
"""  
REASON-1A — Failure Diagnosis Engine (agent-friendly)  
  
Pure, deterministic, rule-based diagnosis helper.  
- No logging  
- No Selenium calls  
- No filesystem writes  
- No imports from project modules with side effects  
  
Public API:  
  diagnose_failure(...)  
"""  
  
from __future__ import annotations  
  
from typing import Any, Dict, List, Optional, Tuple  
  
__all__ = [  
    "diagnose_failure",  
]  
  
CATEGORIES = [  
    "SELECTOR_NOT_FOUND",  
    "TIMEOUT",  
    "IFRAME_CONTEXT",  
    "STALE_ELEMENT",  
    "CLICK_INTERCEPTED",  
    "NAVIGATION",  
    "AUTH_SESSION",  
    "DOWNLOAD",  
    "JS_EXECUTION",  
    "CONFIG",  
    "UNKNOWN",  
]  
  
  
def _norm(s: Optional[str]) -> str:  
    return (s or "").strip().lower()  
  
  
def _join_text(*parts: Optional[str]) -> str:  
    return "\n".join([p for p in (parts or []) if isinstance(p, str) and p.strip()])  
  
  
def _contains_any(text: str, needles: List[str]) -> bool:  
    t = text  
    return any(n in t for n in needles)  
  
  
def _timeline_steps(timeline: Optional[dict]) -> List[dict]:  
    if not isinstance(timeline, dict):  
        return []  
    steps = timeline.get("steps")  
    if not isinstance(steps, list):  
        return []  
    out = [s for s in steps if isinstance(s, dict)]  
    return out  
  
  
def _get_action_from_timeline(timeline: Optional[dict], step_index: Optional[int]) -> Optional[str]:  
    steps = _timeline_steps(timeline)  
    if step_index is None or not isinstance(step_index, int):  
        return None  
    for s in steps:  
        if s.get("step_index") == step_index and isinstance(s.get("action"), str):  
            return s["action"]  
    return None  
  
  
def _recent_actions(timeline: Optional[dict], step_index: Optional[int], window: int = 5) -> List[str]:  
    steps = _timeline_steps(timeline)  
    if not steps:  
        return []  
    # Sort by step_index if present; otherwise keep order  
    def key(s: dict) -> Tuple[int, int]:  
        si = s.get("step_index")  
        return (si if isinstance(si, int) else 10**9, 0)  
  
    steps_sorted = sorted(steps, key=key)  
    if step_index is None or not isinstance(step_index, int):  
        # last N actions  
        actions = [s.get("action") for s in steps_sorted if isinstance(s.get("action"), str)]  
        return actions[-window:]  
  
    prior = [s for s in steps_sorted if isinstance(s.get("step_index"), int) and s["step_index"] <= step_index]  
    actions = [s.get("action") for s in prior if isinstance(s.get("action"), str)]  
    return actions[-window:]  
  
  
def _count_failed_timeouts(timeline: Optional[dict]) -> int:  
    steps = _timeline_steps(timeline)  
    c = 0  
    for s in steps:  
        st = _norm(s.get("status"))  
        act = _norm(s.get("action"))  
        meta = s.get("metadata") if isinstance(s.get("metadata"), dict) else {}  
        msg = _norm(meta.get("error_message")) if isinstance(meta, dict) else ""  
        if st in {"failed", "fail", "error", "exception"} and (  
            "timeout" in act or "wait" in act or "timeout" in msg or "timed out" in msg  
        ):  
            c += 1  
    return c  
  
  
def _mk_fix(rank: int, fix: str, why: str, probe: str, headless_note: str = "") -> dict:  
    return {  
        "rank": rank,  
        "fix": fix,  
        "why": why,  
        "headless_note": headless_note,  
        "probe": probe,  
    }  
  
  
def _base_notes(  
    *,  
    matched_rules: List[str],  
    action: Optional[str],  
    step_index: Optional[int],  
    error_type: Optional[str],  
    error_message: Optional[str],  
    traceback_text: Optional[str],  
    context: Optional[dict],  
    timeline: Optional[dict],  
) -> dict:  
    inputs_used = {  
        "action": action,  
        "step_index": step_index,  
        "error_type": error_type,  
        "error_message": (error_message[:500] if isinstance(error_message, str) else None),  
        "traceback_text": (traceback_text[:800] if isinstance(traceback_text, str) else None),  
        "context_keys": sorted(list(context.keys())) if isinstance(context, dict) else None,  
        "timeline_present": isinstance(timeline, dict),  
    }  
    return {"matched_rules": matched_rules, "inputs_used": inputs_used}  
  
  
def diagnose_failure(  
    *,  
    action: str | None = None,  
    step_index: int | None = None,  
    error_type: str | None = None,  
    error_message: str | None = None,  
    traceback_text: str | None = None,  
    context: dict | None = None,  
    timeline: dict | None = None,  
) -> dict:  
    """  
    Deterministic, rule-based classification + actionable guidance.  
  
    Returns a dict with at minimum:  
      {  
        "category": <known>,  
        "confidence": 0..1,  
        "title": str,  
        "why": [..],  
        "fixes": [{rank, fix, why, headless_note, probe}, ...],  
        "next_probes": [..],  
        "notes": {"matched_rules": [...], "inputs_used": {...}}  
      }  
    """  
    # Prefer explicit action, otherwise pull from timeline if possible  
    action_eff = action if (isinstance(action, str) and action.strip()) else _get_action_from_timeline(timeline, step_index)  
  
    et = _norm(error_type)  
    em = _norm(error_message)  
    tb = _norm(traceback_text)  
    blob = _join_text(et, em, tb)  
    blob_l = blob.lower()  
  
    recent = [a.lower() for a in _recent_actions(timeline, step_index)]  
    prev_action = recent[-2] if len(recent) >= 2 else (recent[-1] if recent else None)  
  
    matched: List[str] = []  
  
    def result(  
        category: str,  
        confidence: float,  
        title: str,  
        why: List[str],  
        fixes: List[dict],  
        next_probes: List[str],  
    ) -> dict:  
        if category not in CATEGORIES:  
            category = "UNKNOWN"  
        confidence = float(max(0.0, min(1.0, confidence)))  
        return {  
            "category": category,  
            "confidence": confidence,  
            "title": title,  
            "why": why,  
            "fixes": fixes,  
            "next_probes": next_probes,  
            "notes": _base_notes(  
                matched_rules=matched,  
                action=action_eff,  
                step_index=step_index,  
                error_type=error_type,  
                error_message=error_message,  
                traceback_text=traceback_text,  
                context=context,  
                timeline=timeline,  
            ),  
        }  
  
    # -----------------------------  
    # CONFIG (driver/session setup)  
    # -----------------------------  
    if _contains_any(  
        blob_l,  
        [  
            "sessionnotcreatedexception",  
            "session not created",  
            "cannot find chrome binary",  
            "chromedriver",  
            "geckodriver",  
            "driver executable",  
            "binary is not found",  
            "invalid argument",  
            "invalid capability",  
            "capabilities",  
        ],  
    ):  
        matched.append("CONFIG:driver_or_capabilities")  
        return result(  
            "CONFIG",  
            0.9,  
            "WebDriver/browser configuration error",  
            [  
                "The error text indicates the driver could not start a valid browser session or received invalid options.",  
            ],  
            [  
                _mk_fix(  
                    1,  
                    "Verify browser + matching driver are installed and on PATH (or configured in ENTRY-1A).",  
                    "Session creation failures commonly come from missing/mismatched driver binaries.",  
                    "Record browser/driver versions and the exact options/capabilities used.",  
                ),  
                _mk_fix(  
                    2,  
                    "Remove/adjust invalid capabilities and re-run with minimal config.",  
                    "Invalid arguments/capabilities can prevent session creation.",  
                    "Log the resolved config after merges (defaults + overrides).",  
                ),  
            ],  
            [  
                "Capture the full capabilities/options payload used to start the session.",  
                "Log browser/driver versions (and OS) used in the failing environment.",  
            ],  
        )  
  
    # -----------------------------  
    # AUTH_SESSION  
    # -----------------------------  
    if _contains_any(blob_l, ["401", "403", "unauthorized", "forbidden", "login", "sign in", "invalid session"]):  
        matched.append("AUTH_SESSION:auth_or_session")  
        return result(  
            "AUTH_SESSION",  
            0.85,  
            "Authentication/session issue (not logged in or session expired)",  
            [  
                "The error text suggests the run is unauthenticated, unauthorized, or using an invalid/expired session.",  
            ],  
            [  
                _mk_fix(  
                    1,  
                    "Re-authenticate and ensure the workflow establishes a valid session before protected actions.",  
                    "Most portal flows require an explicit login step or cookie persistence.",  
                    "Log current URL + page title right before failure to confirm you’re on the expected authenticated page.",  
                ),  
                _mk_fix(  
                    2,  
                    "Add a guard check after navigation: assert presence of a known post-login element.",  
                    "Detecting login redirects early prevents confusing downstream selector failures.",  
                    "Probe for login form selectors when an expected element is missing.",  
                ),  
            ],  
            [  
                "Capture current URL and any redirect targets around the failing step.",  
                "Log presence/absence of a login form marker (e.g., password field) right after nav.",  
            ],  
        )  
  
    # -----------------------------  
    # NAVIGATION  
    # -----------------------------  
    if _contains_any(  
        blob_l,  
        [  
            "net::err_",  
            "dns",  
            "name_not_resolved",  
            "not reachable",  
            "connection refused",  
            "connection reset",  
            "timeout loading page",  
            "err_connection",  
        ],  
    ):  
        matched.append("NAVIGATION:network_or_page_load")  
        return result(  
            "NAVIGATION",  
            0.85,  
            "Navigation/network failure",  
            [  
                "The error text suggests a network/DNS/connectivity issue or the page failed to load.",  
            ],  
            [  
                _mk_fix(  
                    1,  
                    "Verify the URL is reachable from the runtime environment (DNS, VPN, proxies).",  
                    "Automation frequently fails in CI/servers due to restricted network routes.",  
                    "Probe by logging response/redirect info (where available) and current URL.",  
                ),  
                _mk_fix(  
                    2,  
                    "Add retries/backoff around navigation and critical loads.",  
                    "Transient network failures are common.",  
                    "Probe by recording timing (DNS/TLS/page load) if your environment allows it.",  
                ),  
            ],  
            [  
                "Log current URL, page title, and readyState at failure time.",  
                "Record whether the environment requires proxy/VPN and whether it was enabled.",  
            ],  
        )  
  
    # -----------------------------  
    # DOWNLOAD  
    # -----------------------------  
    if _contains_any(blob_l, ["download"]) and _contains_any(blob_l, ["timed out", "timeout", "file not found", "no such file"]):  
        matched.append("DOWNLOAD:download_timeout_or_missing")  
        return result(  
            "DOWNLOAD",  
            0.9,  
            "Download did not complete (timeout or missing file)",  
            [  
                "The error text indicates a download wait timed out or a file was not found after triggering a download.",  
            ],  
            [  
                _mk_fix(  
                    1,  
                    "Increase download wait timeout and confirm the download was actually triggered.",  
                    "Some portals generate files asynchronously or behind extra confirmation.",  
                    "Probe by logging a timestamped list of files in the download directory during waits.",  
                ),  
                _mk_fix(  
                    2,  
                    "Ensure the browser download directory and permissions are correctly configured.",  
                    "Misconfigured download paths cause files to land elsewhere or fail silently.",  
                    "Probe by logging the resolved download directory from config.",  
                ),  
            ],  
            [  
                "Log the download directory path and list its contents before/after the triggering action.",  
                "Record whether a new tab/popup/confirm dialog appeared when initiating the download.",  
            ],  
        )  
  
    # -----------------------------  
    # JS_EXECUTION  
    # -----------------------------  
    if _contains_any(blob_l, ["javascriptexception", "javascript error", "execute_script"]):  
        matched.append("JS_EXECUTION:js_exception")  
        return result(  
            "JS_EXECUTION",  
            0.85,  
            "JavaScript execution failed",  
            [  
                "The failure originated from executing JavaScript in the browser context.",  
            ],  
            [  
                _mk_fix(  
                    1,  
                    "Validate the JS snippet against the current page DOM and guard for nulls.",  
                    "Pages often change structure; robust JS should handle missing elements.",  
                    "Probe by logging the JS snippet and any returned values (or error text).",  
                ),  
                _mk_fix(  
                    2,  
                    "Ensure you are in the correct frame/window before executing script.",  
                    "JS runs in the currently selected context.",  
                    "Probe by logging current URL + frame/window handle info before script execution.",  
                ),  
            ],  
            [  
                "Capture the exact JS code and the browser console error (if available).",  
                "Record whether an iframe switch occurred earlier in the run.",  
            ],  
        )  
  
    # -----------------------------  
    # CLICK_INTERCEPTED  
    # -----------------------------  
    if _contains_any(blob_l, ["elementclickinterceptedexception", "element click intercepted", "other element would receive the click"]):  
        matched.append("CLICK_INTERCEPTED:click_intercepted")  
        return result(  
            "CLICK_INTERCEPTED",  
            0.9,  
            "Click was intercepted (overlay/animation/element not clickable)",  
            [  
                "The target element was present, but something blocked the click (overlay, modal, sticky header, animation).",  
            ],  
            [  
                _mk_fix(  
                    1,  
                    "Wait for overlays/spinners to disappear before clicking (explicit wait on invisibility).",  
                    "Interception is commonly caused by transient UI layers.",  
                    "Probe by logging presence of known overlay selectors at click time.",  
                    "Headless rendering/layout can differ slightly; verify behavior headed when diagnosing.",  
                ),  
                _mk_fix(  
                    2,  
                    "Scroll the element into view and click when it is clickable (not just present).",  
                    "Elements can exist but be outside the viewport or covered.",  
                    "Probe by recording element rect + viewport size (via JS) at click time.",  
                    "Headless layout differences can change which element receives the click.",  
                ),  
            ],  
            [  
                "Log which element is at the click point (e.g., document.elementFromPoint via JS) during failure.",  
                "Capture whether a modal/dialog is open and blocking the page.",  
            ],  
        )  
  
    # -----------------------------  
    # STALE_ELEMENT  
    # -----------------------------  
    if _contains_any(blob_l, ["staleelementreferenceexception", "stale element reference"]):  
        matched.append("STALE_ELEMENT:stale_reference")  
        return result(  
            "STALE_ELEMENT",  
            0.9,  
            "Element became stale (DOM updated after locating it)",  
            [  
                "The page DOM changed between finding the element and interacting with it.",  
            ],  
            [  
                _mk_fix(  
                    1,  
                    "Re-locate the element immediately before interacting (avoid reusing old element handles).",  
                    "Stale references happen after re-render, navigation, or list updates.",  
                    "Probe by logging whether navigation/ajax occurred between find and act.",  
                ),  
                _mk_fix(  
                    2,  
                    "Wait for the page/state to stabilize before interacting.",  
                    "Ensures you click/type after dynamic updates finish.",  
                    "Probe by logging readyState and key spinner visibility before and after waits.",  
                ),  
            ],  
            [  
                "Record whether the step included a wait for a known stable marker before clicking/typing.",  
                "Log timestamps around DOM updates (if you track them) to correlate with staleness.",  
            ],  
        )  
  
    # -----------------------------  
    # IFRAME_CONTEXT (must come before SELECTOR_NOT_FOUND)  
    # -----------------------------  
    iframe_hint_in_error = _contains_any(blob_l, ["iframe", "frame", "no such frame", "target frame detached"])  
    iframe_hint_in_timeline = any(("frame" in a) for a in recent) or (prev_action is not None and "frame" in prev_action)  
  
    if iframe_hint_in_error or iframe_hint_in_timeline:  
        # If it looks like a selector failure immediately after a frame switch, raise confidence.  
        no_such = _contains_any(blob_l, ["nosuchelementexception", "unable to locate element", "no such element"])  
        conf = 0.75 if (iframe_hint_in_timeline and no_such) else (0.7 if iframe_hint_in_timeline else 0.6)  
        matched.append("IFRAME_CONTEXT:frame_hint")  
        return result(  
            "IFRAME_CONTEXT",  
            conf,  
            "Likely wrong iframe/frame context",  
            [  
                "The error/timeline suggests the target element is inside a different iframe (or you forgot to switch back to default content).",  
                f"Recent actions: {recent}" if recent else "No timeline actions available.",  
            ],  
            [  
                _mk_fix(  
                    1,  
                    "Switch into the correct iframe before locating/clicking the element; switch back to default content after.",  
                    "Element lookups happen in the current frame context.",  
                    "Probe by logging iframe count and which iframe you switched to (name/id/index).",  
                ),  
                _mk_fix(  
                    2,  
                    "Add a frame-availability wait before switching and before searching inside the frame.",  
                    "Frames can load asynchronously.",  
                    "Probe by logging document.readyState inside the frame context after switching.",  
                ),  
            ],  
            [  
                "Log the current frame context (or which iframe selector/index you used) at failure time.",  
                "Record the number of iframes on the page and whether the target is inside one (quick DOM probe).",  
            ],  
        )  
  
    # -----------------------------  
    # SELECTOR_NOT_FOUND  
    # -----------------------------  
    if _contains_any(blob_l, ["nosuchelementexception", "unable to locate element", "no such element"]):  
        matched.append("SELECTOR_NOT_FOUND:no_such_element")  
        return result(  
            "SELECTOR_NOT_FOUND",  
            0.9,  
            "Element not found for the given selector",  
            [  
                "The selector did not match any elements in the current DOM/context at the time of the step.",  
            ],  
            [  
                _mk_fix(  
                    1,  
                    "Verify and update the selector (use CAPTURE-1A to recapture a stable selector).",  
                    "Selectors often drift when UI changes.",  
                    "Probe by logging the selector used and whether a nearby parent/container exists.",  
                    "Headless vs headed can differ; confirm the selector in a headed debug session if needed.",  
                ),  
                _mk_fix(  
                    2,  
                    "Add an explicit wait for the element to exist/visible before acting.",  
                    "The element may appear after async loads.",  
                    "Probe by logging page readyState and any spinner/loader indicators.",  
                ),  
            ],  
            [  
                "Log current URL and page title at failure time (to confirm correct page/state).",  
                "If the page is dynamic, log whether an expected container element exists before searching for the target.",  
            ],  
        )  
  
    # -----------------------------  
    # TIMEOUT (generic)  
    # -----------------------------  
    if _contains_any(blob_l, ["timeoutexception", "timed out", "timeout"]) or _count_failed_timeouts(timeline) >= 2:  
        matched.append("TIMEOUT:timeout_match")  
        extra = ""  
        n_to = _count_failed_timeouts(timeline)  
        if n_to >= 2:  
            matched.append("TIMEOUT:repeated_timeouts_in_timeline")  
            extra = f"Multiple timeout-like failures observed in timeline: {n_to}."  
        return result(  
            "TIMEOUT",  
            0.9 if "timeoutexception" in blob_l else (0.8 if "timed out" in blob_l else 0.7),  
            "Timed out waiting for a condition (element/state/navigation)",  
            [  
                "A wait condition did not become true within the allotted time.",  
                extra if extra else "No additional timeline timeout aggregation available.",  
            ],  
            [  
                _mk_fix(  
                    1,  
                    "Increase timeout or use a more specific wait condition (visible/clickable/present).",  
                    "Incorrect wait targets or slow environments can cause timeouts.",  
                    "Probe by logging which condition was being waited on and how long it waited.",  
                ),  
                _mk_fix(  
                    2,  
                    "Verify navigation/state transitions occur before the wait starts (correct URL, correct page).",  
                    "Waiting on the wrong page will always time out.",  
                    "Probe by logging URL/title before and after navigation actions.",  
                ),  
            ],  
            [  
                "Log current URL/title and the selector being waited for at timeout.",  
                "Record step durations to identify whether slowness is systemic or localized.",  
            ],  
        )  
  
    # -----------------------------  
    # Fallback UNKNOWN  
    # -----------------------------  
    matched.append("UNKNOWN:no_rule_matched")  
    return result(  
        "UNKNOWN",  
        0.25,  
        "Unclassified automation failure",  
        [  
            "No specific rule matched the provided error text/timeline.",  
            "More context is needed to provide a confident diagnosis.",  
        ],  
        [  
            _mk_fix(  
                1,  
                "Capture more context around the failing step (URL, selector, page state, last actions).",  
                "Most root causes become obvious with minimal additional context.",  
                "Probe by attaching a structured error payload (error_type/message/traceback + action + selector + url).",  
            )  
        ],  
        [  
            "Include error_type, error_message, and traceback_text (full) next time.",  
            "Include the last ~5 timeline steps with actions/statuses and any selector/url fields.",  
            "Log current URL and the action being performed when the error occurred.",  
        ],  
    )  