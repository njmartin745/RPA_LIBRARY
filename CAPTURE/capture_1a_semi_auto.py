# CAPTURE/capture_1a_semi_auto.py  
"""  
CAPTURE-1A — Semi-Automatic Selector Capture (headed capture session)  
  
Developer tool:  
- Launches a headed browser session (forces headless off)  
- User clicks an element once  
- Captures element attributes + generates selector candidates (CSS + XPath)  
- Prompts user to choose a candidate  
- Saves into SELECTOR-1A registry JSON format (preserving existing entries)  
  
Notes:  
- User click is only for capture. No coordinate clicking automation is used for production.  
- Prints instructions (interactive developer tool).  
"""  
  
from __future__ import annotations  
  
import inspect  
import json  
import time  
from copy import deepcopy  
from pathlib import Path  
from typing import Any, Dict, List, Optional, Tuple  
  
__all__ = [  
    "capture_session",  
]  
  
  
def _read_text(p: Path) -> str:  
    return p.read_text(encoding="utf-8", errors="replace")  
  
  
def _safe_load_json(p: Path) -> Optional[Any]:  
    try:  
        return json.loads(_read_text(p))  
    except Exception:  
        return None  
  
  
def _write_json_pretty(p: Path, obj: Any) -> None:  
    p.parent.mkdir(parents=True, exist_ok=True)  
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")  
  
  
def _set_dotted_path(root: Dict[str, Any], dotted: str) -> Tuple[Dict[str, Any], str]:  
    parts = [x for x in (dotted or "").split(".") if x]  
    if len(parts) < 2:  
        raise ValueError("selector_name must be a dotted path like 'group.element'")  
    cur: Dict[str, Any] = root  
    for p in parts[:-1]:  
        nxt = cur.get(p)  
        if nxt is None:  
            cur[p] = {}  
            nxt = cur[p]  
        if not isinstance(nxt, dict):  
            raise ValueError(f"Cannot set '{dotted}': '{p}' exists but is not an object/dict")  
        cur = nxt  
    return cur, parts[-1]  
  
  
def _create_driver_via_entry_forced_headed(cfg: dict) -> Any:  
    """  
    Uses ENTRY-1A to create driver, forcing headed mode regardless of cfg defaults.  
    """  
    if not isinstance(cfg, dict):  
        raise ValueError("cfg must be a dict")  
  
    cfg2 = deepcopy(cfg)  
    # force headed (cover common conventions)  
    cfg2["headless"] = False  
    cfg2["HEADLESS"] = False  
  
    try:  
        entry_mod = __import__("ENTRY.entry_1a_webdriver_bootstrap", fromlist=["*"])  
    except Exception as e:  
        raise ValueError(  
            "Failed to import ENTRY-1A.\n"  
            "Expected: ENTRY/entry_1a_webdriver_bootstrap.py\n"  
            f"Import error: {e}"  
        )  
  
    # requirement says "make_driver", but be tolerant if repo uses a different name  
    candidates = ["make_driver", "create_driver", "bootstrap_driver", "bootstrap_webdriver", "build_driver", "get_driver"]  
  
    last_err: Optional[Exception] = None  
    for fn_name in candidates:  
        fn = getattr(entry_mod, fn_name, None)  
        if not callable(fn):  
            continue  
  
        try:  
            sig = inspect.signature(fn)  
            params = sig.parameters  
            has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())  
  
            if has_varkw:  
                return fn(cfg=cfg2)  # type: ignore[misc]  
  
            if "cfg" in params:  
                return fn(cfg2)  # type: ignore[misc]  
            if "config" in params:  
                return fn(cfg2)  # type: ignore[misc]  
  
            # fallback best-effort  
            try:  
                return fn(cfg2)  # type: ignore[misc]  
            except TypeError:  
                return fn()  # type: ignore[misc]  
  
        except Exception as e:  
            last_err = e  
  
    raise ValueError(  
        "Could not find a driver factory in ENTRY-1A.\n"  
        f"Tried: {', '.join(candidates)}\n"  
        + (f"Last error: {last_err}" if last_err else "")  
    )  
  
  
_JS_INSTALL_LISTENER = r"""  
(function(){  
  function cssEscape(s){  
    try { return CSS.escape(s); } catch(e) {}  
    return String(s).replace(/([ #;?%&,.+*~\':"!^$$$()=>|\/@])/g,'\\$1');  
  }  
  
  function clipText(s){  
    s = (s || "").replace(/\s+/g, " ").trim();  
    if (s.length > 80) s = s.slice(0, 80);  
    return s;  
  }  
  
  function getAttr(el, name){  
    try {  
      var v = el.getAttribute(name);  
      if (v === null || v === undefined) return null;  
      v = String(v).trim();  
      return v ? v : null;  
    } catch(e){ return null; }  
  }  
  
  function uniqueCss(sel){  
    if (!sel) return null;  
    try {  
      return document.querySelectorAll(sel).length === 1;  
    } catch(e){  
      return null;  
    }  
  }  
  
  function cssCandidate(el){  
    if (!el) return null;  
  
    var tag = (el.tagName || "").toLowerCase();  
    if (!tag) return null;  
  
    var id = (el.id || "").trim();  
    if (id) return "#" + cssEscape(id);  
  
    var testid = getAttr(el, "data-testid");  
    if (testid) return '[data-testid="' + testid.replace(/"/g, '\\"') + '"]';  
  
    var name = getAttr(el, "name");  
    if (name) return tag + '[name="' + name.replace(/"/g, '\\"') + '"]';  
  
    var aria = getAttr(el, "aria-label");  
    if (aria) return tag + '[aria-label="' + aria.replace(/"/g, '\\"') + '"]';  
  
    // stable-ish class chain (avoid numeric-heavy classes)  
    var classes = [];  
    try {  
      for (var i=0;i<el.classList.length;i++){  
        var c = el.classList[i];  
        if (!c) continue;  
        if (/\d/.test(c)) continue;  
        if (c.length > 40) continue;  
        classes.push(c);  
      }  
    } catch(e){}  
  
    if (classes.length){  
      classes = classes.slice(0, 3);  
      return tag + "." + classes.map(cssEscape).join(".");  
    }  
  
    // fallback to tag (may be unique on simple pages)  
    return tag;  
  }  
  
  function xpathLiteral(s){  
    // very small helper: return a quoted literal if possible; otherwise null  
    if (s.indexOf('"') === -1) return '"' + s + '"';  
    if (s.indexOf("'") === -1) return "'" + s + "'";  
    return null;  
  }  
  
  function xpathCandidate(el){  
    if (!el) return null;  
    var tag = (el.tagName || "").toLowerCase();  
    if (!tag) return null;  
  
    var id = (el.id || "").trim();  
    if (id) return '//*[@id=' + xpathLiteral(id) + ']';  
  
    var testid = getAttr(el, "data-testid");  
    if (testid){  
      var lit = xpathLiteral(testid);  
      if (lit) return '//*[@data-testid=' + lit + ']';  
    }  
  
    var name = getAttr(el, "name");  
    if (name){  
      var lit2 = xpathLiteral(name);  
      if (lit2) return '//' + tag + '[@name=' + lit2 + ']';  
    }  
  
    var aria = getAttr(el, "aria-label");  
    if (aria){  
      var lit3 = xpathLiteral(aria);  
      if (lit3) return '//' + tag + '[@aria-label=' + lit3 + ']';  
    }  
  
    // If inner text is simple (no quotes), allow a text match  
    var txt = clipText(el.innerText || "");  
    var lit4 = xpathLiteral(txt);  
    if (txt && lit4){  
      return '//' + tag + '[normalize-space()=' + lit4 + ']';  
    }  
  
    // positional path (avoid /html/body unless necessary)  
    // build segments like: div[2]/span[1]  
    var segs = [];  
    var cur = el;  
    for (var depth=0; depth<6 && cur && cur.nodeType === 1; depth++){  
      var t = (cur.tagName || "").toLowerCase();  
      if (!t) break;  
      var idx = 1;  
      var sib = cur;  
      while ((sib = sib.previousElementSibling) != null){  
        if ((sib.tagName || "").toLowerCase() === t) idx++;  
      }  
      segs.unshift(t + "[" + idx + "]");  
      cur = cur.parentElement;  
    }  
    if (!segs.length) return null;  
    return "//" + segs.join("/");  
  }  
  
  if (!window.__selectorCapture){  
    window.__selectorCapture = { installed: false, last: null };  
  }  
  if (window.__selectorCapture.installed) return true;  
  
  document.addEventListener("click", function(ev){  
    try {  
      var el = ev.target;  
      if (!el || el.nodeType !== 1) return;  
  
      var tag = (el.tagName || "").toLowerCase();  
      var id = (el.id || "").trim() || null;  
  
      var classList = [];  
      try { classList = Array.from(el.classList || []); } catch(e){ classList = []; }  
  
      var name = getAttr(el, "name");  
      var aria = getAttr(el, "aria-label");  
      var testid = getAttr(el, "data-testid");  
      var text = clipText(el.innerText || "");  
  
      var css = cssCandidate(el);  
      var cssUnique = uniqueCss(css);  
      var xp = xpathCandidate(el);  
  
      window.__selectorCapture.last = {  
        ts: Date.now(),  
        tagName: tag,  
        id: id,  
        classList: classList,  
        name: name,  
        aria_label: aria,  
        data_testid: testid,  
        innerText: text,  
        css_candidate: css,  
        css_unique: cssUnique,  
        xpath_candidate: xp  
      };  
    } catch(e){}  
  }, true);  
  
  window.__selectorCapture.installed = true;  
  return true;  
})();  
"""  
  
  
def _build_ranked_candidates(captured: dict) -> List[dict]:  
    """  
    Returns 2–4 candidates ranked with reasons.  
    Candidate dict shape:  
      { "strategy": "css"|"xpath", "selector": "...", "reason": "...", "unique": bool|None }  
    """  
    out: List[dict] = []  
    tag = captured.get("tagName")  
    el_id = captured.get("id")  
    testid = captured.get("data_testid")  
    name = captured.get("name")  
  
    css = captured.get("css_candidate")  
    css_unique = captured.get("css_unique")  
    xp = captured.get("xpath_candidate")  
  
    if isinstance(el_id, str) and el_id:  
        out.append({"strategy": "css", "selector": f"#{el_id}", "reason": "Has id (usually most stable)", "unique": True})  
    if isinstance(testid, str) and testid:  
        out.append(  
            {  
                "strategy": "css",  
                "selector": f'[data-testid="{testid}"]',  
                "reason": "Has data-testid (often stable test hook)",  
                "unique": None,  
            }  
        )  
    # include computed CSS candidate (covers tag[name], class chain, or tag fallback)  
    if isinstance(css, str) and css:  
        reason = "Generated CSS candidate"  
        if isinstance(name, str) and name and isinstance(tag, str) and tag and css.startswith(f"{tag}[name="):  
            reason = "Has name attribute"  
        out.append({"strategy": "css", "selector": css, "reason": reason, "unique": css_unique})  
  
    if isinstance(xp, str) and xp:  
        out.append({"strategy": "xpath", "selector": xp, "reason": "Generated XPath candidate", "unique": None})  
  
    # de-dup by (strategy, selector) preserving order  
    seen = set()  
    dedup: List[dict] = []  
    for c in out:  
        key = (c.get("strategy"), c.get("selector"))  
        if key in seen:  
            continue  
        seen.add(key)  
        dedup.append(c)  
  
    return dedup[:4]  
  
  
def capture_session(  
    url: str,  
    *,  
    selector_name: str,  
    cfg: dict,  
    output_path: str | Path = "data/selectors.json",  
    timeout: int = 60,  
) -> dict:  
    """  
    Headed capture session.  
  
    Returns:  
      {  
        "selector_name": "...",  
        "output_path": "...",  
        "saved": { ... leaf record ... },  
        "captured": { ... captured metadata ... },  
        "candidates": [ ... ],  
      }  
    """  
    if not isinstance(url, str) or not url.strip():  
        raise ValueError("url must be a non-empty string")  
    if not isinstance(selector_name, str) or not selector_name.strip():  
        raise ValueError("selector_name must be a non-empty string")  
    if not isinstance(cfg, dict):  
        raise ValueError("cfg must be a dict")  
    if not isinstance(timeout, int) or timeout <= 0:  
        raise ValueError("timeout must be a positive int")  
  
    out_path = Path(output_path)  
  
    print("NOTE: Selector capture requires a HEADED browser session (headless disabled).")  
    print("      Production runs can remain headless-first; this is a developer-only utility.\n")  
  
    driver = _create_driver_via_entry_forced_headed(cfg)  
    try:  
        driver.get(url)  
  
        print("Instructions:")  
        print("  1) If needed, login/navigate manually in the opened browser.")  
        print("  2) When ready, click the target element ONCE.\n")  
  
        # Install click listener  
        driver.execute_script(_JS_INSTALL_LISTENER)  
  
        # Poll until click captured  
        deadline = time.time() + timeout  
        captured = None  
        while time.time() < deadline:  
            captured = driver.execute_script("return (window.__selectorCapture && window.__selectorCapture.last) || null;")  
            if isinstance(captured, dict) and captured.get("ts"):  
                break  
            time.sleep(0.25)  
  
        if not (isinstance(captured, dict) and captured.get("ts")):  
            raise ValueError(f"Timed out after {timeout}s waiting for element click capture")  
  
        candidates = _build_ranked_candidates(captured)  
        if not candidates:  
            raise ValueError("No selector candidates could be generated for the clicked element")  
  
        print("Captured element:")  
        print(f"  tag: {captured.get('tagName')}")  
        print(f"  id: {captured.get('id')}")  
        print(f"  data-testid: {captured.get('data_testid')}")  
        print(f"  name: {captured.get('name')}")  
        print(f"  aria-label: {captured.get('aria_label')}")  
        print(f"  text: {captured.get('innerText')}\n")  
  
        print("Selector candidates:")  
        for i, c in enumerate(candidates, start=1):  
            uniq = c.get("unique")  
            uniq_s = "" if uniq is None else (" (unique)" if uniq else " (NOT unique)")  
            print(f"  {i}) {c['strategy']}: {c['selector']}{uniq_s} — {c.get('reason')}")  
  
        choice_raw = input(f"\nChoose which candidate to save (1-{len(candidates)}) [1]: ").strip()  
        choice = 1  
        if choice_raw:  
            try:  
                choice = int(choice_raw)  
            except Exception:  
                raise ValueError("Invalid choice: must be an integer")  
        if choice < 1 or choice > len(candidates):  
            raise ValueError(f"Choice out of range: {choice}")  
  
        chosen = candidates[choice - 1]  
        preferred = chosen["strategy"]  
  
        # load registry (preserve existing)  
        reg: Dict[str, Any] = {}  
        if out_path.exists():  
            loaded = _safe_load_json(out_path)  
            if loaded is None:  
                raise ValueError(f"Existing selectors file is not valid JSON: {out_path}")  
            if not isinstance(loaded, dict):  
                raise ValueError(f"Existing selectors file must be a JSON object: {out_path}")  
            reg = loaded  
  
        parent, leaf_key = _set_dotted_path(reg, selector_name.strip())  
        leaf = parent.get(leaf_key)  
        if leaf is None:  
            leaf = {}  
            parent[leaf_key] = leaf  
        if not isinstance(leaf, dict):  
            raise ValueError(f"Existing selector entry at '{selector_name}' is not an object; cannot update")  
  
        css_cand = captured.get("css_candidate")  
        xp_cand = captured.get("xpath_candidate")  
  
        # store both if present; mark preferred  
        if isinstance(css_cand, str) and css_cand:  
            leaf["css"] = css_cand  
        if isinstance(xp_cand, str) and xp_cand:  
            leaf["xpath"] = xp_cand  
        leaf["preferred"] = preferred  
  
        leaf["meta"] = {  
            "tagName": captured.get("tagName"),  
            "id": captured.get("id"),  
            "classList": captured.get("classList"),  
            "name": captured.get("name"),  
            "aria_label": captured.get("aria_label"),  
            "data_testid": captured.get("data_testid"),  
            "innerText": captured.get("innerText"),  
            "css_unique": captured.get("css_unique"),  
            "captured_ts": captured.get("ts"),  
        }  
  
        _write_json_pretty(out_path, reg)  
  
        saved = {  
            "selector_name": selector_name.strip(),  
            "output_path": str(out_path),  
            "saved": deepcopy(leaf),  
            "captured": captured,  
            "candidates": candidates,  
        }  
        print("\nSaved selector entry.")  
        return saved  
  
    finally:  
        try:  
            q = getattr(driver, "quit", None)  
            if callable(q):  
                q()  
        except Exception:  
            pass  