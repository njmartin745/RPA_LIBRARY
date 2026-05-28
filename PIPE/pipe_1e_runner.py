"""  
PIPE-1E — Single runnable pipeline entrypoint.  
  
This module orchestrates an end-to-end run by *composing existing modules*:  
- Steps: PIPE-1C (load/render/normalize)  
- Worklist/driver/loop/actions/logging/state: delegated to PIPE-1A orchestrator  
  (which uses PIPE/INPUT/LOOP/ACT/NAV/STATE/LOG layers)  
  
Exit codes  
----------  
- 0: all items succeeded  
- 2: completed run with one or more item failures  
- 1: fatal error (exception / could not run)  
  
Env-friendly cfg keys supported  
-------------------------------  
WORKLIST_PATH / WORKLIST_XLSX, WORKLIST_SHEET, WORKLIST_ID_COLUMN,  
STEPS_PATH or STEPS (inline),  
MANIFEST_PATH, LOG_PATH,  
STOP_ON_ERROR, HEADLESS, BROWSER, EXPLICIT_WAIT.  
"""  
  
from __future__ import annotations  
  
import importlib  
import json  
import logging  
import os  
import pkgutil  
import tempfile  
import zipfile  
import xml.etree.ElementTree as ET  
from typing import Any, Callable, Dict, List, MutableMapping, Optional, Tuple  
  
from PIPE.pipe_1h_log_jsonl_path_policy import (  
    maybe_cleanup_log_jsonl_path,  
    select_log_jsonl_path,  
)  
  
__all__ = ["run_pipeline", "exit_code_for_summary", "main"]  
  
# ----------------------------  
# Resolution helpers (introspection-friendly)  
# ----------------------------  
  
  
def _resolve_callable(module_name: str, attr: str) -> Optional[Callable[..., Any]]:  
    try:  
        mod = importlib.import_module(module_name)  
    except Exception:  
        return None  
    fn = getattr(mod, attr, None)  
    return fn if callable(fn) else None  
  
  
def _scan_package_for_callable(pkg_name: str, attr: str) -> Optional[Callable[..., Any]]:  
    try:  
        pkg = importlib.import_module(pkg_name)  
    except Exception:  
        return None  
    if not hasattr(pkg, "__path__"):  
        return None  
  
    for mi in pkgutil.iter_modules(pkg.__path__, prefix=pkg.__name__ + "."):  
        try:  
            mod = importlib.import_module(mi.name)  
        except Exception:  
            continue  
        fn = getattr(mod, attr, None)  
        if callable(fn):  
            return fn  
    return None  
  
  
def _resolve_run_worklist() -> Callable[[MutableMapping[str, Any], List[Dict[str, Any]]], Dict[str, Any]]:  
    fn = _resolve_callable("PIPE.pipe_1a_run_orchestrator", "run_worklist")  
    if fn:  
        return fn  # type: ignore[return-value]  
  
    fn = _scan_package_for_callable("PIPE", "run_worklist")  
    if fn:  
        return fn  # type: ignore[return-value]  
  
    raise RuntimeError("PIPE-1E: Could not resolve PIPE-1A run_worklist(cfg, steps).")  
  
  
def _resolve_load_steps_from_cfg() -> Callable[[MutableMapping[str, Any]], List[Dict[str, Any]]]:  
    fn = _resolve_callable("PIPE.pipe_1c_steps_loader", "load_steps_from_cfg")  
    if fn:  
        return fn  # type: ignore[return-value]  
    raise RuntimeError("PIPE-1E: Could not resolve PIPE-1C load_steps_from_cfg(cfg).")  
  
  
# ----------------------------  
# cfg normalization (env-friendly)  
# ----------------------------  
  
  
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
  
  
def _apply_env_defaults(cfg: MutableMapping[str, Any]) -> None:  
    keys = (  
        "WORKLIST_PATH",  
        "WORKLIST_XLSX",  
        "WORKLIST_SHEET",  
        "WORKLIST_ID_COLUMN",  
        "STEPS_PATH",  
        "MANIFEST_PATH",  
        "LOG_PATH",  
        "STOP_ON_ERROR",  
        "HEADLESS",  
        "BROWSER",  
        "EXPLICIT_WAIT",  
    )  
    for k in keys:  
        if k not in cfg or cfg.get(k) in (None, ""):  
            ev = os.environ.get(k)  
            if ev is not None and ev != "":  
                cfg[k] = ev  
  
    # PIPE-1F: coerce/alias env values (DRY_RUN, etc.)  
    try:  
        from PIPE.pipe_1f_env_overrides import apply_env_overrides  
  
        apply_env_overrides(cfg, environ=os.environ)  
    except Exception:  
        pass  
  
    # PIPE-1G: force env to win over CLI defaults (LOG_PATH etc.)  
    try:  
        from PIPE.pipe_1g_env_force_overrides import apply_env_force_overrides  
  
        apply_env_force_overrides(cfg, environ=os.environ)  
    except Exception:  
        pass  
  
  
def _normalize_cfg_aliases(cfg: MutableMapping[str, Any]) -> None:  
    # Worklist aliases  
    wl_path = cfg.get("WORKLIST_PATH")  
    wl_xlsx = cfg.get("WORKLIST_XLSX")  
  
    if isinstance(wl_path, str) and wl_path.strip() and not (isinstance(wl_xlsx, str) and wl_xlsx.strip()):  
        cfg["WORKLIST_XLSX"] = wl_path.strip()  
  
    if isinstance(cfg.get("WORKLIST_XLSX"), str) and str(cfg["WORKLIST_XLSX"]).strip():  
        cfg["INPUT_XLSX"] = str(cfg["WORKLIST_XLSX"]).strip()  
        cfg.setdefault("WORKLIST_PATH", str(cfg["WORKLIST_XLSX"]).strip())  
  
    # Sheet aliases  
    if isinstance(cfg.get("WORKLIST_SHEET"), str) and str(cfg["WORKLIST_SHEET"]).strip():  
        cfg.setdefault("SHEET", str(cfg["WORKLIST_SHEET"]).strip())  
    elif isinstance(cfg.get("SHEET"), str) and str(cfg["SHEET"]).strip():  
        cfg.setdefault("WORKLIST_SHEET", str(cfg["SHEET"]).strip())  
  
    # Logging/manifest path aliases  
    if isinstance(cfg.get("LOG_PATH"), str) and str(cfg["LOG_PATH"]).strip():  
        cfg.setdefault("LOG_JSONL_PATH", str(cfg["LOG_PATH"]).strip())  
  
    if isinstance(cfg.get("MANIFEST_PATH"), str) and str(cfg["MANIFEST_PATH"]).strip():  
        cfg.setdefault("STATE_MANIFEST_PATH", str(cfg["MANIFEST_PATH"]).strip())  
  
    # STOP_ON_ERROR aliases  
    soe = _truthy(cfg.get("STOP_ON_ERROR"))  
    if soe is not None:  
        cfg["STOP_ON_ERROR"] = soe  
        cfg.setdefault("stop_on_error", soe)  
        cfg.setdefault("FAIL_FAST", soe)  
  
    # HEADLESS / BROWSER aliases  
    headless = _truthy(cfg.get("HEADLESS"))  
    if headless is not None:  
        cfg["HEADLESS"] = headless  
        cfg.setdefault("headless", headless)  
  
    browser = cfg.get("BROWSER")  
    if isinstance(browser, str) and browser.strip():  
        cfg["BROWSER"] = browser.strip()  
        cfg.setdefault("browser", browser.strip())  
  
    # EXPLICIT_WAIT aliases  
    ew = cfg.get("EXPLICIT_WAIT")  
    if ew is not None:  
        cfg.setdefault("EXPLICIT_WAIT_SEC", ew)  
        cfg.setdefault("WAIT_EXPLICIT_SEC", ew)  
  
  
def _default_paths_if_missing(cfg: MutableMapping[str, Any]) -> None:  
    if not (isinstance(cfg.get("MANIFEST_PATH"), str) and str(cfg["MANIFEST_PATH"]).strip()):  
        fd, p = tempfile.mkstemp(prefix="pipe_1e_manifest_", suffix=".jsonl")  
        os.close(fd)  
        cfg["MANIFEST_PATH"] = p  
        cfg.setdefault("STATE_MANIFEST_PATH", p)  
  
    # NOTE: LOG path selection is now handled by PIPE-1H policy via select_log_jsonl_path().  
    # This fallback remains for backward-compatibility if caller bypasses run_pipeline().  
    if not (isinstance(cfg.get("LOG_PATH"), str) and str(cfg["LOG_PATH"]).strip()):  
        fd, p = tempfile.mkstemp(prefix="pipe_1e_log_", suffix=".jsonl")  
        os.close(fd)  
        cfg["LOG_PATH"] = p  
        cfg.setdefault("LOG_JSONL_PATH", p)  
  
  
# ----------------------------  
# XLSX introspection (stdlib-only) to align sheet/header with generated workbooks  
# ----------------------------  
  
_NS_MAIN = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}  
_NS_REL = {"r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}  
_NS_PKG_REL = {"pr": "http://schemas.openxmlformats.org/package/2006/relationships"}  
  
  
def _xlsx_sheet_names(xlsx_path: str) -> List[str]:  
    try:  
        with zipfile.ZipFile(xlsx_path, "r") as z:  
            wb = z.read("xl/workbook.xml")  
        root = ET.fromstring(wb)  
        names: List[str] = []  
        for sh in root.findall(".//m:sheets/m:sheet", _NS_MAIN):  
            name = sh.get("name")  
            if name:  
                names.append(name)  
        return names  
    except Exception:  
        return []  
  
  
def _col_letters_to_index(col: str) -> int:  
    # A -> 1, B -> 2, ..., Z -> 26, AA -> 27 ...  
    n = 0  
    for ch in col.upper():  
        if "A" <= ch <= "Z":  
            n = n * 26 + (ord(ch) - ord("A") + 1)  
    return n  
  
  
def _cell_ref_col_index(ref: str) -> int:  
    # "B12" -> 2  
    letters = []  
    for ch in ref:  
        if ch.isalpha():  
            letters.append(ch)  
        else:  
            break  
    return _col_letters_to_index("".join(letters)) or 0  
  
  
def _xlsx_first_header(xlsx_path: str, preferred_sheet: Optional[str] = None) -> Optional[str]:  
    """  
    Best-effort: read first header cell (A1) from the preferred sheet.  
    Supports inlineStr; sharedStrings best-effort (returns None if not present).  
    """  
    try:  
        with zipfile.ZipFile(xlsx_path, "r") as z:  
            wb_xml = ET.fromstring(z.read("xl/workbook.xml"))  
            rels_xml = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))  
  
            rid_to_target: Dict[str, str] = {}  
            for rel in rels_xml.findall(".//pr:Relationship", _NS_PKG_REL):  
                rid = rel.get("Id")  
                target = rel.get("Target")  
                if rid and target:  
                    rid_to_target[rid] = target  
  
            # pick sheet  
            sheet_elems = wb_xml.findall(".//m:sheets/m:sheet", _NS_MAIN)  
            target: Optional[str] = None  
            for sh in sheet_elems:  
                name = sh.get("name")  
                rid = sh.get(f"{{{_NS_REL['r']}}}id")  # r:id  
                if not rid:  
                    continue  
                if preferred_sheet and name == preferred_sheet:  
                    target = rid_to_target.get(rid)  
                    break  
            if target is None and sheet_elems:  
                rid0 = sheet_elems[0].get(f"{{{_NS_REL['r']}}}id")  
                if rid0:  
                    target = rid_to_target.get(rid0)  
  
            if not target:  
                return None  
  
            sheet_path = "xl/" + target.lstrip("/")  
            sheet_xml = ET.fromstring(z.read(sheet_path))  
  
            row1 = sheet_xml.find(".//m:sheetData/m:row[@r='1']", _NS_MAIN)  
            if row1 is None:  
                return None  
  
            cells = []  
            for c in row1.findall("m:c", _NS_MAIN):  
                ref = c.get("r") or ""  
                col_idx = _cell_ref_col_index(ref)  
                t = c.get("t")  
  
                val: Optional[str] = None  
                if t == "inlineStr":  
                    tnode = c.find("m:is/m:t", _NS_MAIN)  
                    if tnode is not None and tnode.text is not None:  
                        val = tnode.text  
                # sharedStrings ("s") not implemented here; keep None.  
                if val is not None and col_idx:  
                    cells.append((col_idx, val))  
  
            if not cells:  
                return None  
            cells.sort(key=lambda x: x[0])  
            return cells[0][1].strip() if cells[0][1].strip() else None  
    except Exception:  
        return None  
  
  
def _ensure_worklist_sheet_and_header(cfg: MutableMapping[str, Any]) -> None:  
    """  
    If INPUT-1B defaults (e.g. sheet='locations') do not match the provided workbook,  
    override cfg['WORKLIST_SHEET'] to the first sheet found in the xlsx.  
  
    Also, if WORKLIST_ID_COLUMN is missing, best-effort infer it from A1 and set  
    common header alias keys so INPUT-1B can read it.  
    """  
    xlsx = None  
    for k in ("WORKLIST_XLSX", "WORKLIST_PATH", "INPUT_XLSX"):  
        v = cfg.get(k)  
        if isinstance(v, str) and v.strip() and os.path.exists(v.strip()):  
            xlsx = v.strip()  
            break  
    if not xlsx:  
        return  
  
    names = _xlsx_sheet_names(xlsx)  
    if names:  
        wanted = None  
        for k in ("WORKLIST_SHEET", "SHEET"):  
            v = cfg.get(k)  
            if isinstance(v, str) and v.strip():  
                wanted = v.strip()  
                break  
        if not wanted or wanted not in names:  
            cfg["WORKLIST_SHEET"] = names[0]  
            cfg["SHEET"] = names[0]  
  
    # Infer header only if not already provided.  
    existing_id = cfg.get("WORKLIST_ID_COLUMN")  
    if not (isinstance(existing_id, str) and existing_id.strip()):  
        header = _xlsx_first_header(  
            xlsx,  
            preferred_sheet=cfg.get("WORKLIST_SHEET") if isinstance(cfg.get("WORKLIST_SHEET"), str) else None,  
        )  
        if header:  
            cfg["WORKLIST_ID_COLUMN"] = header  
            for hk in ("WORKLIST_HEADER", "WORKLIST_ID_HEADER", "EXCEL_HEADER", "INPUT_HEADER", "HEADER"):  
                if not (isinstance(cfg.get(hk), str) and str(cfg.get(hk)).strip()):  
                    cfg[hk] = header  
  
  
# ----------------------------  
# Steps handling (STEPS inline or STEPS_PATH)  
# ----------------------------  
  
  
def _coerce_steps_inline(v: Any) -> List[Dict[str, Any]]:  
    if isinstance(v, str):  
        v = json.loads(v)  
  
    if isinstance(v, dict) and "steps" in v:  
        v = v["steps"]  
  
    if not isinstance(v, list) or any(not isinstance(s, dict) for s in v):  
        raise ValueError("cfg['STEPS'] must be a list[dict] (or JSON string / {'steps': [...]})")  
  
    return v  # type: ignore[return-value]  
  
  
def _materialize_inline_steps_to_file(steps: List[Dict[str, Any]]) -> str:  
    fd, p = tempfile.mkstemp(prefix="pipe_1e_steps_", suffix=".json")  
    os.close(fd)  
    with open(p, "w", encoding="utf-8") as f:  
        json.dump({"steps": steps}, f, indent=2)  
    return p  
  
  
def _load_steps(cfg: MutableMapping[str, Any]) -> List[Dict[str, Any]]:  
    load_steps_from_cfg = _resolve_load_steps_from_cfg()  
  
    if "STEPS" in cfg and cfg.get("STEPS") not in (None, ""):  
        steps_inline = _coerce_steps_inline(cfg.get("STEPS"))  
        if not (isinstance(cfg.get("STEPS_PATH"), str) and str(cfg.get("STEPS_PATH")).strip()):  
            cfg["STEPS_PATH"] = _materialize_inline_steps_to_file(steps_inline)  
  
    return load_steps_from_cfg(cfg)  
  
  
# ----------------------------  
# Step-level visibility (best-effort, via JSONL structured logs)  
# ----------------------------  
  
  
def _pick_log_jsonl_path(cfg: MutableMapping[str, Any]) -> Optional[str]:  
    for k in ("LOG_JSONL_PATH", "LOG_PATH"):  
        v = cfg.get(k)  
        if isinstance(v, str) and v.strip():  
            return v.strip()  
    return None  
  
  
def _read_jsonl_events(path: str) -> List[Dict[str, Any]]:  
    events: List[Dict[str, Any]] = []  
    try:  
        if not path or not os.path.exists(path):  
            return events  
        with open(path, "r", encoding="utf-8", errors="replace") as f:  
            for line in f:  
                s = line.strip()  
                if not s:  
                    continue  
                if not (s.startswith("{") and s.endswith("}")):  
                    continue  
                try:  
                    obj = json.loads(s)  
                except Exception:  
                    continue  
                if isinstance(obj, dict):  
                    events.append(obj)  
    except Exception:  
        return events  
    return events  
  
  
def _safe_step_inputs(step: Dict[str, Any]) -> Dict[str, Any]:  
    # Minimal + avoid secrets  
    allow = (  
        "name",  
        "url",  
        "selector_ref",  
        "selector",  
        "by",  
        "strategy",  
        "timeout",  
        "condition",  
        "seconds",  
        "path",  
        "save_as",  
        "script",  # truncated  
    )  
    out: Dict[str, Any] = {}  
    for k in allow:  
        if k in step and step.get(k) not in (None, ""):  
            if k == "script":  
                s = str(step.get("script"))  
                out[k] = s if len(s) <= 200 else (s[:200] + "...[truncated]")  
            else:  
                out[k] = step.get(k)  
  
    # never include secrets (common keys)  
    for sk in ("secret", "password", "token", "api_key"):  
        if sk in out:  
            out.pop(sk, None)  
  
    return out  
  
  
def _build_step_logs_from_events(  
    *,  
    steps: List[Dict[str, Any]],  
    events: List[Dict[str, Any]],  
    run_id: Optional[str],  
    current_id: Optional[str] = None,  
) -> List[Dict[str, Any]]:  
    # Filter events to this run_id when possible  
    if run_id:  
        filtered: List[Dict[str, Any]] = []  
        for e in events:  
            rid = e.get("run_id") or e.get("RUN_ID")  
            if rid == run_id:  
                filtered.append(e)  
        events = filtered  
  
    # Optional per-item filter (prevents multi-item smearing)  
    if current_id:  
        filtered2: List[Dict[str, Any]] = []  
        for e in events:  
            if str(e.get("current_id")) == str(current_id):  
                filtered2.append(e)  
        events = filtered2  
  
    logs: List[Dict[str, Any]] = []  
    by_index: Dict[int, Dict[str, Any]] = {}  
  
    for i, st in enumerate(steps):  
        action = str(st.get("action", "")).strip()  
        row: Dict[str, Any] = {  
            "index": i,  
            "action": action,  
            "inputs": _safe_step_inputs(st),  
            "status": "unknown",  # success|failure|unknown  
        }  
        logs.append(row)  
        by_index[i] = row  
  
    def _event_step_index(e: Dict[str, Any]) -> Optional[int]:  
        idx = e.get("step_index")  
        if idx is None:  
            idx = e.get("index")  
        if idx is None and isinstance(e.get("fields"), dict):  
            idx = e["fields"].get("step_index")  
        try:  
            return int(idx)  # type: ignore[arg-type]  
        except Exception:  
            return None  
  
    def _event_error_message(e: Dict[str, Any]) -> Optional[str]:  
        for k in ("error_message", "error", "exception", "exc"):  
            v = e.get(k)  
            if isinstance(v, str) and v.strip():  
                return v.strip()  
        if isinstance(e.get("fields"), dict):  
            for k in ("error_message", "error", "exception", "exc"):  
                v = e["fields"].get(k)  
                if isinstance(v, str) and v.strip():  
                    return v.strip()  
        msg = e.get("message")  
        if isinstance(msg, str) and msg.strip():  
            return msg.strip()  
        return None  
  
    for e in events:  
        ev = (e.get("event") or e.get("type") or "").strip()  
        if ev not in {  
            "step_start",  
            "step_success",  
            "step_error",  
            "action_success",  
            "action_error",  
            "step_failure",  
            "action_failure",  
        }:  
            continue  
  
        idx_i = _event_step_index(e)  
        if idx_i is None:  
            continue  
  
        row = by_index.get(idx_i)  
        if not row:  
            continue  
  
        # Never allow a later error to downgrade a real success for that step index.  
        if row.get("status") == "success" and ev in {  
            "step_error",  
            "action_error",  
            "step_failure",  
            "action_failure",  
        }:  
            continue  
  
        if ev in {"step_success", "action_success"}:  
            row["status"] = "success"  
            row.pop("error", None)  
        elif ev in {"step_error", "action_error", "step_failure", "action_failure"}:  
            row["status"] = "failure"  
            msg = _event_error_message(e)  
            if msg:  
                row["error"] = msg  
        else:  
            row.setdefault("status", "unknown")  
  
    return logs  
  
  
# ----------------------------  
# Public API  
# ----------------------------  
  
  
def exit_code_for_summary(summary: Any) -> int:  
    """  
    0 if all ok, 2 if any failures, 1 if fatal/invalid summary.  
    """  
    if not isinstance(summary, dict):  
        return 1  
  
    ok = summary.get("ok")  
    if isinstance(ok, bool):  
        return 0 if ok else 2  
  
    # Prefer explicit failure counts if present  
    for fk in ("failed", "failed_count"):  
        failed = summary.get(fk)  
        if isinstance(failed, int) and not isinstance(failed, bool):  
            return 0 if failed == 0 else 2  
  
    # If we only have success counts, require success == total_items to be "all ok"  
    total = summary.get("total_items")  
    for sk in ("success_count", "success"):  
        success = summary.get(sk)  
        if isinstance(success, int) and not isinstance(success, bool):  
            if isinstance(total, int) and total >= 0:  
                return 0 if success == total else 2  
            # Can't prove it's all-ok -> treat as failure-completed, not success  
            return 2  
  
    # If we only have a boolean success flag (rare), treat False as failure.  
    success_bool = summary.get("success")  
    if isinstance(success_bool, bool):  
        return 0 if success_bool else 2  
  
    return 1  
  
  
def run_pipeline(cfg: MutableMapping[str, Any]) -> Tuple[Dict[str, Any], int]:  
    """  
    Run an end-to-end pipeline using PIPE-1A orchestrator.  
  
    Returns:  
        (summary_dict, exit_code)  
    """  
    if cfg is None:  
        return ({"ok": False, "fatal": True, "error": "cfg is required"}, 1)  
  
    log_jsonl_path: Optional[str] = None  
    log_is_temp: bool = False  
  
    try:  
        _apply_env_defaults(cfg)  
        _normalize_cfg_aliases(cfg)  
  
        # PIPE-1H: select an explicit JSONL log path (prefer user-provided LOG_JSONL_PATH/LOG_PATH),  
        # otherwise create a temp jsonl (eligible for cleanup).  
        log_jsonl_path, log_is_temp = select_log_jsonl_path(cfg, environ=os.environ)  
  
        # Ensure downstream modules + any env readers see the chosen path  
        if log_jsonl_path:  
            cfg["LOG_PATH"] = log_jsonl_path  
            cfg["LOG_JSONL_PATH"] = log_jsonl_path  
            os.environ["LOG_PATH"] = log_jsonl_path  
            os.environ["LOG_JSONL_PATH"] = log_jsonl_path   
        
        # IMPORTANT: CLI may have already configured logging; force rebind to our file  
        try:  
            from LOG.log_1b_logger_reset import setup_logging_force  
            setup_logging_force(cfg)  
        except Exception:  
            pass  
  
        _default_paths_if_missing(cfg)  
  
        # Critical robustness: align configured sheet/header with the actual workbook  
        # if caller didn't specify them (or specified a missing sheet).  
        _ensure_worklist_sheet_and_header(cfg)  
  
        steps = _load_steps(cfg)  
        run_worklist = _resolve_run_worklist()  
  
        summary = run_worklist(cfg, steps)  
  
        # Ensure file handlers are flushed/closed before reading LOG_JSONL_PATH.  
        # (Also repeated in finally; shutdown() is idempotent.)  
        try:  
            logging.shutdown()  
        except Exception:  
            pass  
  
        # NEW: rebuild step-level logs from JSONL events (best-effort).  
        # IMPORTANT: overwrite existing step_logs so PIPE-1A’s noisy events don’t mis-attribute statuses.  
        if isinstance(summary, dict):  
            log_path = _pick_log_jsonl_path(cfg)  
            events = _read_jsonl_events(log_path) if log_path else []  
  
            rid: Optional[str] = None  
            if isinstance(summary.get("run_id"), str) and summary.get("run_id"):  
                rid = str(summary.get("run_id"))  
            elif isinstance(cfg.get("RUN_ID"), str) and cfg.get("RUN_ID"):  
                rid = str(cfg.get("RUN_ID"))  
  
            # If PIPE-1A returned per-item details, fix those too (best-effort).  
            items = summary.get("items")  
            if isinstance(items, list) and items:  
                for it in items:  
                    if not isinstance(it, dict):  
                        continue  
                    item_id = it.get("item_id")  
                    if isinstance(item_id, str) and item_id:  
                        it["step_logs"] = _build_step_logs_from_events(  
                            steps=steps,  
                            events=events,  
                            run_id=rid,  
                            current_id=item_id,  
                        )  
                # For convenience, set top-level step_logs to the last item’s step_logs  
                last = items[-1]  
                if isinstance(last, dict) and isinstance(last.get("step_logs"), list):  
                    summary["step_logs"] = last["step_logs"]  
                else:  
                    summary["step_logs"] = _build_step_logs_from_events(  
                        steps=steps,  
                        events=events,  
                        run_id=rid,  
                    )  
            else:  
                summary["step_logs"] = _build_step_logs_from_events(  
                    steps=steps,  
                    events=events,  
                    run_id=rid,  
                )  
  
        code = exit_code_for_summary(summary)  
        if isinstance(summary, dict):  
            summary.setdefault("exit_code", code)  
        return (summary if isinstance(summary, dict) else {"summary": summary}, code)  
  
    except Exception as e:  
        return ({"ok": False, "fatal": True, "error": f"{type(e).__name__}: {e}"}, 1)  
  
    finally:  
        # Ensure file handlers are released (important on Windows so temp dirs can be removed).  
        try:  
            logging.shutdown()  
        except Exception:  
            pass  
  
        # Only clean up JSONL log when PIPE-1H created it as a temp file.  
        if log_jsonl_path:  
            maybe_cleanup_log_jsonl_path(log_jsonl_path, is_temp=log_is_temp)  
  
  
def main() -> int:  
    """  
    Minimal runnable entrypoint (env-driven).  
    Example:  
        set WORKLIST_PATH=...  
        set STEPS_PATH=...  
        python -m PIPE.pipe_1e_runner  
    """  
    cfg: Dict[str, Any] = {}  
    summary, code = run_pipeline(cfg)  
    try:  
        print(json.dumps(summary, indent=2, default=str))  
    except Exception:  
        print(summary)  
    return code  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  