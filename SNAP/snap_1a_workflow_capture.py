from __future__ import annotations  
  
import json  
from dataclasses import dataclass  
from typing import Any, Dict, Iterable, List, Mapping, Optional, Protocol, Sequence, Tuple  
  
  
__all__ = [  
    "ALLOWED_WORKFLOW_ACTIONS",  
    "CapturedEvent",  
    "capture_install_js",  
    "install_capture_listeners",  
    "fetch_captured_events",  
    "captured_events_to_steps",  
    "dev_smoke",  
]  
  
  
ALLOWED_WORKFLOW_ACTIONS: Tuple[str, ...] = (  
    "open",  
    "click_selector",  
    "type_selector_secret",  
    "wait_for_selector",  
    "exec_js",  
    "exec_js_file",  
    "repeat",  
    "log",  
    "switch_back_to_main_tab",  
)  
  
  
class _JsCapableDriver(Protocol):  
    def execute_script(self, script: str, *args: Any) -> Any: ...  
  
  
@dataclass(frozen=True, slots=True)  
class CapturedEvent:  
    """  
    Canonical captured event representation (deterministic ordering via seq).  
    """  
    kind: str  
    seq: int  
    selector: Optional[str] = None  
    url: Optional[str] = None  
    value: Optional[str] = None  
    tag: Optional[str] = None  
    meta: Optional[Dict[str, Any]] = None  
  
  
def capture_install_js() -> str:  
    """  
    JS snippet to install capture listeners into the current page.  
    - Deterministic ordering: increments `seq` for each pushed event.  
    - Stores events in `window.__rpa_capture.queue`.  
    """  
    # Note: keep the snippet as a single string; deterministic and idempotent.  
    return r"""  
(function () {  
  if (window.__rpa_capture && window.__rpa_capture.installed) return;  
  
  window.__rpa_capture = {  
    installed: true,  
    seq: 0,  
    queue: [],  
    lastValueBySelector: {}  
  };  
  
  function push(evt) {  
    window.__rpa_capture.seq += 1;  
    evt.seq = window.__rpa_capture.seq;  
    window.__rpa_capture.queue.push(evt);  
  }  
  
  function cssEscapeIdent(ident) {  
    // Minimal escape for CSS identifiers.  
    // https://drafts.csswg.org/cssom/#serialize-an-identifier  
    if (ident === null || ident === undefined) return "";  
    ident = String(ident);  
    return ident.replace(/([ !"#$%&'()*+,.\/:;<=>?@[\\\]^`{|}~])/g, "\\$1");  
  }  
  
  function cssPath(el) {  
    if (!el || el.nodeType !== 1) return null;  
  
    // Prefer stable id if present  
    if (el.id) return "#" + cssEscapeIdent(el.id);  
  
    // Prefer name attribute for common inputs  
    var name = el.getAttribute && el.getAttribute("name");  
    if (name) return el.tagName.toLowerCase() + '[name="' + String(name).replace(/"/g, '\\"') + '"]';  
  
    // Build a deterministic path with nth-of-type  
    var parts = [];  
    var node = el;  
    while (node && node.nodeType === 1 && parts.length < 6) {  
      var tag = node.tagName.toLowerCase();  
  
      // Stop early if an ancestor has id  
      if (node.id) {  
        parts.unshift("#" + cssEscapeIdent(node.id));  
        break;  
      }  
  
      var parent = node.parentNode;  
      if (!parent || parent.nodeType !== 1) {  
        parts.unshift(tag);  
        break;  
      }  
  
      var siblings = parent.children;  
      var sameTagCount = 0;  
      var indexAmongSameTag = 0;  
      for (var i = 0; i < siblings.length; i++) {  
        if (siblings[i].tagName && siblings[i].tagName.toLowerCase() === tag) {  
          sameTagCount += 1;  
          if (siblings[i] === node) indexAmongSameTag = sameTagCount;  
        }  
      }  
  
      if (sameTagCount > 1) {  
        parts.unshift(tag + ":nth-of-type(" + indexAmongSameTag + ")");  
      } else {  
        parts.unshift(tag);  
      }  
  
      node = parent;  
    }  
  
    return parts.join(" > ");  
  }  
  
  document.addEventListener("click", function (e) {  
    try {  
      var el = e.target;  
      var sel = cssPath(el);  
      if (!sel) return;  
      push({ kind: "click", selector: sel, tag: (el && el.tagName) ? el.tagName.toLowerCase() : null });  
    } catch (_) {}  
  }, true);  
  
  // Record final-ish values deterministically: capture 'change' and de-duplicate by selector+value.  
  document.addEventListener("change", function (e) {  
    try {  
      var el = e.target;  
      if (!el) return;  
      var sel = cssPath(el);  
      if (!sel) return;  
  
      var v = null;  
      if ("value" in el) v = String(el.value);  
  
      var last = window.__rpa_capture.lastValueBySelector[sel];  
      if (last === v) return;  
      window.__rpa_capture.lastValueBySelector[sel] = v;  
  
      push({ kind: "change", selector: sel, value: v, tag: (el && el.tagName) ? el.tagName.toLowerCase() : null });  
    } catch (_) {}  
  }, true);  
  
  // Basic navigation capture.  
  window.addEventListener("popstate", function () {  
    try { push({ kind: "navigate", url: String(location.href), method: "popstate" }); } catch (_) {}  
  }, true);  
  
  window.addEventListener("hashchange", function () {  
    try { push({ kind: "navigate", url: String(location.href), method: "hashchange" }); } catch (_) {}  
  }, true);  
  
  // Patch history methods to capture SPA navigations.  
  try {  
    var _ps = history.pushState;  
    history.pushState = function () {  
      var ret = _ps.apply(this, arguments);  
      try { push({ kind: "navigate", url: String(location.href), method: "pushState" }); } catch (_) {}  
      return ret;  
    };  
  } catch (_) {}  
  
  try {  
    var _rs = history.replaceState;  
    history.replaceState = function () {  
      var ret = _rs.apply(this, arguments);  
      try { push({ kind: "navigate", url: String(location.href), method: "replaceState" }); } catch (_) {}  
      return ret;  
    };  
  } catch (_) {}  
})();  
""".strip()  
  
  
def install_capture_listeners(driver: _JsCapableDriver) -> None:  
    """  
    Inject capture JS listeners into the current page. Idempotent.  
    """  
    driver.execute_script(capture_install_js())  
  
  
def fetch_captured_events(driver: _JsCapableDriver) -> List[CapturedEvent]:  
    """  
    Fetch and clear the capture queue from the browser, returning canonical CapturedEvent objects.  
    """  
    raw = driver.execute_script(  
        """  
return (function () {  
  if (!window.__rpa_capture || !window.__rpa_capture.queue) return [];  
  var q = window.__rpa_capture.queue.slice();  
  window.__rpa_capture.queue = [];  
  return q;  
})();  
""".strip()  
    )  
    if not raw:  
        return []  
  
    events: List[CapturedEvent] = []  
    for item in raw:  
        if not isinstance(item, dict):  
            continue  
        kind = str(item.get("kind") or "")  
        seq = int(item.get("seq") or 0)  
        selector = item.get("selector")  
        url = item.get("url")  
        value = item.get("value")  
        tag = item.get("tag")  
        meta = {k: v for k, v in item.items() if k not in {"kind", "seq", "selector", "url", "value", "tag"}}  
        events.append(  
            CapturedEvent(  
                kind=kind,  
                seq=seq,  
                selector=str(selector) if selector is not None else None,  
                url=str(url) if url is not None else None,  
                value=str(value) if value is not None else None,  
                tag=str(tag) if tag is not None else None,  
                meta=meta or None,  
            )  
        )  
  
    # Deterministic: sort by seq (JS should already assign increasing seq)  
    events.sort(key=lambda e: e.seq)  
    return events  
  
  
def _selector_fields(  
    selector: str,  
    selector_ref_map: Optional[Mapping[str, str]],  
) -> Dict[str, str]:  
    if selector_ref_map:  
        ref = selector_ref_map.get(selector)  
        if ref:  
            return {"selector_ref": ref}  
    return {"selector": selector}  
  
  
def _js_set_value_step(selector: str, value: str) -> Dict[str, Any]:  
    # Deterministic JS: querySelector + set value + dispatch input/change  
    sel_js = json.dumps(selector)  
    val_js = json.dumps(value)  
    js = (  
        "(() => {"  
        f"  const el = document.querySelector({sel_js});"  
        "  if (!el) return false;"  
        f"  el.value = {val_js};"  
        "  el.dispatchEvent(new Event('input', { bubbles: true }));"  
        "  el.dispatchEvent(new Event('change', { bubbles: true }));"  
        "  return true;"  
        "})()"  
    )  
    return {"action": "exec_js", "js": js}  
  
  
def captured_events_to_steps(  
    events: Sequence[CapturedEvent] | Sequence[Mapping[str, Any]],  
    *,  
    selector_ref_map: Optional[Mapping[str, str]] = None,  
    include_clicks: bool = True,  
    include_navigation: bool = True,  
    include_changes: bool = False,  
    change_mode: str = "exec_js",  
    redact_change_values: bool = True,  
    secret_ref_placeholder: str = "CAPTURE_TODO_SECRET_REF",  
) -> List[Dict[str, Any]]:  
    """  
    Convert captured events into SCHEMA-1A-compatible step dicts, using only supported actions.  
  
    Parameters  
    ----------  
    selector_ref_map:  
      If provided and contains the captured CSS selector, emit `selector_ref` instead of `selector`.  
      (This supports the 11.1.2 selector-pack stage without requiring it.)  
  
    include_changes:  
      If True, convert 'change' events into steps using change_mode:  
        - "exec_js": emit exec_js that sets the value (optionally redacted)  
        - "log": emit log describing the change (no value)  
        - "type_selector_secret": emit type_selector_secret with placeholder secret_ref  
        - "ignore": ignore changes even if include_changes True  
  
    redact_change_values:  
      If True and change_mode=="exec_js", set value to "" (blank) rather than captured text,  
      avoiding accidental secret capture while still producing a valid supported step.  
    """  
    # Canonicalize input  
    canon: List[CapturedEvent] = []  
    for e in events:  
        if isinstance(e, CapturedEvent):  
            canon.append(e)  
        elif isinstance(e, Mapping):  
            canon.append(  
                CapturedEvent(  
                    kind=str(e.get("kind") or ""),  
                    seq=int(e.get("seq") or 0),  
                    selector=str(e["selector"]) if e.get("selector") is not None else None,  
                    url=str(e["url"]) if e.get("url") is not None else None,  
                    value=str(e["value"]) if e.get("value") is not None else None,  
                    tag=str(e["tag"]) if e.get("tag") is not None else None,  
                    meta=None,  
                )  
            )  
        else:  
            continue  
  
    canon.sort(key=lambda x: x.seq)  
  
    steps: List[Dict[str, Any]] = []  
    for ev in canon:  
        if ev.kind == "click" and include_clicks:  
            if not ev.selector:  
                continue  
            step: Dict[str, Any] = {"action": "click_selector"}  
            step.update(_selector_fields(ev.selector, selector_ref_map))  
            steps.append(step)  
            continue  
  
        if ev.kind == "navigate" and include_navigation:  
            if not ev.url:  
                continue  
            steps.append({"action": "open", "url": ev.url})  
            continue  
  
        if ev.kind == "change" and include_changes:  
            if change_mode == "ignore":  
                continue  
            if not ev.selector:  
                continue  
  
            if change_mode == "log":  
                steps.append(  
                    {  
                        "action": "log",  
                        "message": f"Captured change on {ev.selector}",  
                    }  
                )  
                continue  
  
            if change_mode == "type_selector_secret":  
                step = {"action": "type_selector_secret", "secret_ref": secret_ref_placeholder}  
                step.update(_selector_fields(ev.selector, selector_ref_map))  
                steps.append(step)  
                continue  
  
            if change_mode == "exec_js":  
                v = "" if redact_change_values else (ev.value or "")  
                steps.append(_js_set_value_step(ev.selector, v))  
                continue  
  
            raise ValueError(f"Unsupported change_mode: {change_mode}")  
  
        # Unknown kinds are ignored (deterministic, conservative)  
        continue  
  
    # Safety: ensure we never emit unsupported actions  
    allowed = set(ALLOWED_WORKFLOW_ACTIONS)  
    for s in steps:  
        a = s.get("action")  
        if a not in allowed:  
            raise ValueError(f"Emitted unsupported action: {a}")  
  
    return steps  
  
  
def dev_smoke() -> None:  
    """  
    Minimal self-check without requiring a live browser.  
    """  
    sample = [  
        CapturedEvent(kind="click", seq=1, selector="#login"),  
        CapturedEvent(kind="navigate", seq=2, url="https://example.test/app"),  
        CapturedEvent(kind="change", seq=3, selector="input[name=\"username\"]", value="alice"),  
    ]  
  
    steps = captured_events_to_steps(  
        sample,  
        selector_ref_map={"#login": "btn_login"},  
        include_clicks=True,  
        include_navigation=True,  
        include_changes=True,  
        change_mode="exec_js",  
        redact_change_values=True,  
    )  
  
    assert steps[0]["action"] == "click_selector"  
    assert steps[0].get("selector_ref") == "btn_login"  
    assert "selector" not in steps[0]  
    assert steps[1] == {"action": "open", "url": "https://example.test/app"}  
    assert steps[2]["action"] == "exec_js"  
    assert "document.querySelector" in steps[2]["js"]  
  
    # Determinism: same input => same output  
    steps2 = captured_events_to_steps(  
        sample,  
        selector_ref_map={"#login": "btn_login"},  
        include_clicks=True,  
        include_navigation=True,  
        include_changes=True,  
        change_mode="exec_js",  
        redact_change_values=True,  
    )  
    assert steps == steps2  
  
    # Allowed actions only  
    allowed = set(ALLOWED_WORKFLOW_ACTIONS)  
    assert all(s["action"] in allowed for s in steps)  