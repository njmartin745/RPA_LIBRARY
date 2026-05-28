from __future__ import annotations  
  
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple  
  
__all__ = [  
    "CAPTURE_QUEUE_GLOBAL_1A",  
    "CAPTURE_EVENT_KINDS_1A",  
    "SUPPORTED_STEP_ACTIONS_1A",  
    "js_install_capture_listeners_1a",  
    "js_drain_capture_events_1a",  
    "install_capture_listeners_in_page_1a",  
    "drain_capture_events_from_page_1a",  
    "normalize_capture_event_1a",  
    "capture_events_to_schema_steps_1a",  
    "drain_capture_steps_from_page_1a",  
    "dev_smoke",  
]  
  
CAPTURE_QUEUE_GLOBAL_1A = "__rpa_capture_1a"  
  
# Kinds emitted by the JS recorder. Keep narrow + deterministic.  
CAPTURE_EVENT_KINDS_1A: Tuple[str, ...] = (  
    "open",  
    "click",  
    "type_password",  
)  
  
# Must remain within the framework’s supported step actions.  
SUPPORTED_STEP_ACTIONS_1A: Tuple[str, ...] = (  
    "open",  
    "click_selector",  
    "type_selector_secret",  
)  
  
  
def js_install_capture_listeners_1a() -> str:  
    """  
    Returns JS that installs a capture queue + listeners into the current page.  
  
    Notes:  
    - Does NOT capture plaintext input values.  
    - Records only a narrow set of supported user actions needed for 11.1.1.  
    - Uses a monotonic sequence id (no timestamps) for deterministic ordering.  
    """  
    # Deterministic string (no formatting based on environment).  
    return r"""  
(function(){  
  var G = "%s";  
  if (window[G] && window[G].installed) { return "already_installed"; }  
  
  function _escIdent(s){  
    // Conservative CSS ident escaping (works even if CSS.escape is unavailable)  
    return String(s).replace(/[^a-zA-Z0-9_-]/g, function(ch){  
      var hex = ch.charCodeAt(0).toString(16).toUpperCase();  
      return "\\" + hex + " ";  
    });  
  }  
  
  function _cssPath(el){  
    if (!el || el.nodeType !== 1) return null;  
    if (el.id) return "#" + _escIdent(el.id);  
  
    var parts = [];  
    while (el && el.nodeType === 1 && el !== document.documentElement) {  
      var tag = (el.tagName || "").toLowerCase();  
      if (!tag) break;  
  
      var parent = el.parentNode;  
      if (!parent || parent.nodeType !== 1) {  
        parts.push(tag);  
        break;  
      }  
  
      // nth-of-type for stability within siblings of same tag  
      var i = 0;  
      var sib = el;  
      while (sib) {  
        if (sib.nodeType === 1 && (sib.tagName || "").toLowerCase() === tag) i++;  
        sib = sib.previousSibling;  
      }  
  
      parts.push(tag + ":nth-of-type(" + i + ")");  
      el = parent;  
    }  
    parts.reverse();  
    return parts.join(" > ");  
  }  
  
  window[G] = {  
    installed: true,  
    seq: 0,  
    queue: [],  
    last_url: String(location.href || "")  
  };  
  
  function _push(ev){  
    try {  
      window[G].seq += 1;  
      ev.seq = window[G].seq;  
      window[G].queue.push(ev);  
    } catch (e) {  
      // swallow to avoid breaking the page  
    }  
  }  
  
  function _maybeEmitOpen(){  
    var u = String(location.href || "");  
    if (u && u !== window[G].last_url) {  
      window[G].last_url = u;  
      _push({kind: "open", url: u});  
    }  
  }  
  
  // Initial page URL (record as an open event once)  
  _push({kind: "open", url: String(location.href || "")});  
  
  window.addEventListener("hashchange", function(){ _maybeEmitOpen(); }, true);  
  window.addEventListener("popstate", function(){ _maybeEmitOpen(); }, true);  
  
  document.addEventListener("click", function(e){  
    var t = e && e.target ? e.target : null;  
    var sel = _cssPath(t);  
    if (sel) _push({kind: "click", selector: sel});  
  }, true);  
  
  document.addEventListener("input", function(e){  
    var t = e && e.target ? e.target : null;  
    if (!t || t.nodeType !== 1) return;  
    var tag = (t.tagName || "").toLowerCase();  
    if (tag !== "input") return;  
  
    var typ = String(t.getAttribute("type") || t.type || "").toLowerCase();  
    if (typ !== "password") return;  
  
    var sel = _cssPath(t);  
    if (sel) _push({kind: "type_password", selector: sel});  
  }, true);  
  
  return "installed";  
})();  
""" % (CAPTURE_QUEUE_GLOBAL_1A,)  
  
  
def js_drain_capture_events_1a(*, max_events: int = 250) -> str:  
    """  
    Returns JS that drains up to max_events from the queue and returns them.  
    """  
    if not isinstance(max_events, int) or max_events <= 0:  
        raise ValueError("max_events must be a positive int")  
  
    return r"""  
(function(){  
  var G = "%s";  
  if (!window[G] || !window[G].queue) return [];  
  var n = %d;  
  if (n <= 0) return [];  
  return window[G].queue.splice(0, n);  
})();  
""" % (CAPTURE_QUEUE_GLOBAL_1A, max_events)  
  
  
def install_capture_listeners_in_page_1a(driver: Any) -> str:  
    """  
    Execute the install JS in the current page.  
    driver must implement execute_script(str)->Any (Selenium WebDriver compatible).  
    """  
    return str(driver.execute_script(js_install_capture_listeners_1a()))  
  
  
def drain_capture_events_from_page_1a(driver: Any, *, max_events: int = 250) -> List[Dict[str, Any]]:  
    """  
    Drain capture events from the current page.  
    """  
    out = driver.execute_script(js_drain_capture_events_1a(max_events=max_events))  
    if out is None:  
        return []  
    if not isinstance(out, list):  
        raise TypeError("drain_capture_events_from_page_1a expected a list from execute_script")  
    normed: List[Dict[str, Any]] = []  
    for e in out:  
        ne = normalize_capture_event_1a(e)  
        if ne is not None:  
            normed.append(ne)  
    return normed  
  
  
def normalize_capture_event_1a(ev: Any) -> Optional[Dict[str, Any]]:  
    """  
    Validate/minimize a single captured event dict.  
  
    Returns:  
      normalized dict, or None if the event is unsupported/unusable.  
    """  
    if not isinstance(ev, Mapping):  
        return None  
  
    kind = ev.get("kind")  
    if kind not in CAPTURE_EVENT_KINDS_1A:  
        return None  
  
    out: Dict[str, Any] = {"kind": str(kind)}  
  
    # seq is optional (monotonic ordering)  
    if "seq" in ev:  
        try:  
            out["seq"] = int(ev["seq"])  
        except Exception:  
            # ignore bad seq  
            pass  
  
    if kind == "open":  
        url = ev.get("url")  
        if not isinstance(url, str) or not url.strip():  
            return None  
        out["url"] = url  
        return out  
  
    if kind in ("click", "type_password"):  
        sel = ev.get("selector")  
        if not isinstance(sel, str) or not sel.strip():  
            return None  
        out["selector"] = sel  
        return out  
  
    return None  
  
  
def capture_events_to_schema_steps_1a(  
    events: Sequence[Mapping[str, Any]],  
    *,  
    default_secret_ref: str = "CAPTURE_SECRET_1A",  
) -> List[Dict[str, Any]]:  
    """  
    Convert normalized capture events into SCHEMA-1A step dicts using only supported actions.  
    """  
    steps: List[Dict[str, Any]] = []  
  
    for ev in events:  
        kind = ev.get("kind")  
        if kind == "open":  
            steps.append({"action": "open", "url": ev["url"]})  
        elif kind == "click":  
            steps.append({"action": "click_selector", "selector": ev["selector"]})  
        elif kind == "type_password":  
            # never capture the value; only a reference placeholder  
            steps.append(  
                {  
                    "action": "type_selector_secret",  
                    "selector": ev["selector"],  
                    "secret_ref": default_secret_ref,  
                }  
            )  
        else:  
            # normalized_capture_event_1a should have filtered this already  
            continue  
  
    return steps  
  
  
def drain_capture_steps_from_page_1a(  
    driver: Any,  
    *,  
    max_events: int = 250,  
    default_secret_ref: str = "CAPTURE_SECRET_1A",  
) -> List[Dict[str, Any]]:  
    """  
    Convenience: drain events via JS, normalize, and convert to step dicts.  
    """  
    events = drain_capture_events_from_page_1a(driver, max_events=max_events)  
    return capture_events_to_schema_steps_1a(events, default_secret_ref=default_secret_ref)  
  
  
def dev_smoke() -> None:  
    class _FakeDriver:  
        def __init__(self) -> None:  
            self.scripts: List[str] = []  
            self._installed = False  
  
        def execute_script(self, script: str) -> Any:  
            self.scripts.append(script)  
            if "installed" in script and "already_installed" in script:  
                # install script  
                if self._installed:  
                    return "already_installed"  
                self._installed = True  
                return "installed"  
            # drain script: return deterministic synthetic events  
            return [  
                {"kind": "open", "url": "https://example.invalid/", "seq": 1},  
                {"kind": "click", "selector": "#login", "seq": 2},  
                {"kind": "type_password", "selector": "input:nth-of-type(1)", "seq": 3},  
            ]  
  
    d = _FakeDriver()  
    s = install_capture_listeners_in_page_1a(d)  
    assert s in ("installed", "already_installed")  
    events = drain_capture_events_from_page_1a(d, max_events=10)  
    assert [e["kind"] for e in events] == ["open", "click", "type_password"]  
  
    steps = capture_events_to_schema_steps_1a(events, default_secret_ref="CAPTURE_SECRET_1A")  
    assert [st["action"] for st in steps] == ["open", "click_selector", "type_selector_secret"]  
    assert steps[0]["url"] == "https://example.invalid/"  
    assert steps[1]["selector"] == "#login"  
    assert steps[2]["secret_ref"] == "CAPTURE_SECRET_1A"  
  
    # Ensure JS is generated deterministically and references the global queue name.  
    js1 = js_install_capture_listeners_1a()  
    js2 = js_install_capture_listeners_1a()  
    assert js1 == js2  
    assert CAPTURE_QUEUE_GLOBAL_1A in js1  
  
    jsd = js_drain_capture_events_1a(max_events=5)  
    assert "splice" in jsd and "5" in jsd  