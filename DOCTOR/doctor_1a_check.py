# DOCTOR/doctor_1a_check.py  
"""  
DOCTOR-1A — Environment Self-Check (“preflight”)  
  
Deterministic preflight checker:  
- No Selenium required (optional import only to validate installation)  
- No driver launching (file existence only)  
- Best-effort git branch detection (no subprocess)  
  
Public API:  
  run_preflight(root=".", strict=False, cfg=None) -> dict  
  format_preflight_report(result: dict) -> str  
"""  
  
from __future__ import annotations  
  
import json  
import os  
import sys  
from contextlib import contextmanager  
from dataclasses import dataclass  
from datetime import datetime, timezone  
from pathlib import Path  
from typing import Any, Dict, List, Optional, Tuple  
  
__all__ = [  
    "run_preflight",  
    "format_preflight_report",  
]  
  
  
def _utc_now_iso() -> str:  
    return datetime.now(timezone.utc).isoformat()  
  
  
@contextmanager  
def _prepend_sys_path(p: Path):  
    p_str = str(p)  
    had = p_str in sys.path  
    if not had:  
        sys.path.insert(0, p_str)  
    try:  
        yield  
    finally:  
        if not had:  
            try:  
                sys.path.remove(p_str)  
            except ValueError:  
                pass  
  
  
def _status_normalize(status: str) -> str:  
    s = (status or "").strip().lower()  
    if s in ("ok", "warn", "fail"):  
        return s  
    return "warn"  
  
  
def _make_check(name: str, status: str, details: str = "", hint: str = "") -> dict:  
    return {  
        "name": name,  
        "status": _status_normalize(status),  
        "details": details or "",  
        "hint": hint or "",  
    }  
  
  
def _is_windows() -> bool:  
    return os.name == "nt"  
  
  
def _touch_writeable_dir(d: Path) -> Tuple[bool, str]:  
    """  
    Ensures directory exists and is writable (best-effort) by creating & deleting a small file.  
    """  
    try:  
        d.mkdir(parents=True, exist_ok=True)  
    except Exception as e:  
        return False, f"Could not create dir: {d.as_posix()} ({type(e).__name__}: {e})"  
  
    test_file = d / ".doctor_write_test"  
    try:  
        test_file.write_text("ok\n", encoding="utf-8")  
        test_file.unlink(missing_ok=True)  # py3.8+ supports missing_ok  
        return True, f"Directory writable: {d.as_posix()}"  
    except TypeError:  
        # For older Python, fallback  
        try:  
            test_file.write_text("ok\n", encoding="utf-8")  
            if test_file.exists():  
                test_file.unlink()  
            return True, f"Directory writable: {d.as_posix()}"  
        except Exception as e:  
            return False, f"Directory not writable: {d.as_posix()} ({type(e).__name__}: {e})"  
    except Exception as e:  
        return False, f"Directory not writable: {d.as_posix()} ({type(e).__name__}: {e})"  
  
  
def _safe_json_load(p: Path) -> Tuple[bool, str]:  
    try:  
        raw = p.read_text(encoding="utf-8")  
    except Exception as e:  
        return False, f"Could not read: {p.as_posix()} ({type(e).__name__}: {e})"  
    try:  
        json.loads(raw)  
        return True, f"Valid JSON: {p.as_posix()}"  
    except Exception as e:  
        return False, f"Invalid JSON: {p.as_posix()} ({type(e).__name__}: {e})"  
  
  
def _list_workflow_json_files(workflows_dir: Path) -> List[Path]:  
    if not workflows_dir.exists() or not workflows_dir.is_dir():  
        return []  
    files = [p for p in workflows_dir.rglob("*.json") if p.is_file()]  
    return sorted(files, key=lambda x: x.as_posix().lower())  
  
  
def _detect_git_branch(root: Path) -> Optional[str]:  
    """  
    Best-effort, no subprocess:  
    - Reads .git/HEAD and tries to parse current branch name  
    """  
    git_dir = root / ".git"  
    head = git_dir / "HEAD"  
    if not git_dir.exists() or not head.exists():  
        return None  
    try:  
        s = head.read_text(encoding="utf-8", errors="replace").strip()  
    except Exception:  
        return "unknown"  
  
    if s.startswith("ref:"):  
        ref = s.split(":", 1)[1].strip()  
        # typically: refs/heads/main  
        parts = ref.split("/")  
        if len(parts) >= 3 and parts[0] == "refs" and parts[1] == "heads":  
            return "/".join(parts[2:])  
        return ref  
    # detached HEAD (hash)  
    if len(s) >= 7:  
        return f"detached@{s[:12]}"  
    return "unknown"  
  
  
def _candidate_driver_names(browser: str) -> List[str]:  
    b = (browser or "").strip().lower()  
    if b == "edge":  
        return ["msedgedriver.exe", "msedgedriver"] if not _is_windows() else ["msedgedriver.exe", "msedgedriver"]  
    if b == "chrome":  
        return ["chromedriver.exe", "chromedriver"] if not _is_windows() else ["chromedriver.exe", "chromedriver"]  
    # unknown -> both  
    return ["msedgedriver.exe", "msedgedriver", "chromedriver.exe", "chromedriver"]  
  
  
def _resolve_driver_candidates(  
    *, root: Path, cfg: dict  
) -> List[Tuple[str, Path]]:  
    """  
    Returns list of (source_label, candidate_path).  
    Avoid printing env var values; label indicates source.  
    """  
    candidates: List[Tuple[str, Path]] = []  
  
    browser = str(cfg.get("BROWSER") or "").strip().lower()  
    names = _candidate_driver_names(browser if browser in ("edge", "chrome") else "")  
  
    # cfg DRIVER_PATH may be direct file or dir  
    dp = cfg.get("DRIVER_PATH")  
    if isinstance(dp, (str, Path)) and str(dp).strip():  
        dp_path = (root / Path(dp)).resolve() if not Path(dp).is_absolute() else Path(dp)  
        if dp_path.is_dir():  
            for n in names:  
                candidates.append(("cfg:DRIVER_PATH(dir)", dp_path / n))  
        else:  
            candidates.append(("cfg:DRIVER_PATH(file)", dp_path))  
  
    # env RPA_DRIVER_PATH (treat as file or dir); do not expose actual value  
    env_dp = os.environ.get("RPA_DRIVER_PATH")  
    if isinstance(env_dp, str) and env_dp.strip():  
        env_path = Path(env_dp)  
        if not env_path.is_absolute():  
            env_path = (root / env_path).resolve()  
        if env_path.is_dir():  
            for n in names:  
                candidates.append(("env:RPA_DRIVER_PATH(dir)", env_path / n))  
        else:  
            candidates.append(("env:RPA_DRIVER_PATH(file)", env_path))  
  
    # conventional drivers/  
    drivers_dir = (root / "drivers").resolve()  
    for n in names:  
        candidates.append(("root:drivers/", drivers_dir / n))  
  
    # dedupe deterministically by path  
    seen = set()  
    out: List[Tuple[str, Path]] = []  
    for label, p in candidates:  
        key = p.as_posix()  
        if key in seen:  
            continue  
        seen.add(key)  
        out.append((label, p))  
    return out  
  
  
def _import_registry_best_effort() -> Tuple[bool, str]:  
    """  
    Based on REGISTRY-1A implementation variability, try common module names.  
    """  
    candidates = [  
        "REGISTRY.registry_1a_store",  
        "REGISTRY.registry_1a_registry",  
        "REGISTRY.registry_1a_loader",  
        "REGISTRY.registry_1a_load",  
        "REGISTRY.registry_1a",  
    ]  
    last_err: Optional[Exception] = None  
    for name in candidates:  
        try:  
            __import__(name)  
            return True, f"Imported {name}"  
        except Exception as e:  
            last_err = e  
    return False, f"Could not import REGISTRY module candidates (last: {type(last_err).__name__ if last_err else 'n/a'})"  
  
  
def run_preflight(  
    *,  
    root: str | Path = ".",  
    strict: bool = False,  
    cfg: dict | None = None,  
) -> dict:  
    rootp = Path(root).resolve()  
    cfg_in = cfg if isinstance(cfg, dict) else {}  
  
    checks: List[dict] = []  
  
    def add(name: str, status: str, details: str = "", hint: str = "") -> None:  
        st = _status_normalize(status)  
        if strict and st == "warn":  
            st = "fail"  
        checks.append(_make_check(name, st, details, hint))  
  
    # A) Python deps: selenium importable (warn by default, fail if strict)  
    try:  
        __import__("selenium")  
        add("deps.selenium", "ok", "selenium is importable")  
    except Exception:  
        add(  
            "deps.selenium",  
            "warn",  
            "selenium not importable",  
            "Install selenium (pip install selenium) to run browser workflows.",  
        )  
  
    # B) Driver binaries existence (file existence only)  
    browser = str(cfg_in.get("BROWSER") or "").strip().lower()  
    candidates = _resolve_driver_candidates(root=rootp, cfg=cfg_in)  
  
    found = None  
    found_label = None  
    for label, p in candidates:  
        if p.exists() and p.is_file():  
            found = p  
            found_label = label  
            break  
  
    if browser in ("edge", "chrome"):  
        if found is not None:  
            add("driver.binary", "ok", f"Found {browser} driver at {found.as_posix()} ({found_label})")  
        else:  
            add(  
                "driver.binary",  
                "fail",  
                f"No {browser} driver found",  
                "Set cfg DRIVER_PATH, or set env RPA_DRIVER_PATH, or place driver in root/drivers/.",  
            )  
    else:  
        # cfg missing: warning if none found  
        if found is not None:  
            add("driver.binary", "ok", f"Found driver at {found.as_posix()} ({found_label})")  
        else:  
            add(  
                "driver.binary",  
                "warn",  
                "No driver found (cfg missing BROWSER)",  
                "Set cfg BROWSER=edge|chrome and provide driver (cfg DRIVER_PATH / env RPA_DRIVER_PATH / root/drivers/).",  
            )  
  
    # C) Required directories exist or can be created (write access)  
    for dname in ("downloads", "artifacts", "reports", "history"):  
        ok, msg = _touch_writeable_dir(rootp / dname)  
        add(  
            f"dir.{dname}",  
            "ok" if ok else "fail",  
            msg,  
            "Ensure the directory exists and is writable.",  
        )  
  
    # D) Workflows  
    workflows_dir = rootp / str(cfg_in.get("WORKFLOWS_DIR") or "workflows")  
    if workflows_dir.exists() and workflows_dir.is_dir():  
        wf_files = _list_workflow_json_files(workflows_dir)  
        if wf_files:  
            add("workflows.present", "ok", f"Found {len(wf_files)} workflow json file(s) in {workflows_dir.as_posix()}")  
        else:  
            add(  
                "workflows.present",  
                "fail",  
                f"No workflow .json files found in {workflows_dir.as_posix()}",  
                "Add at least one workflow JSON under workflows/.",  
            )  
    else:  
        add("workflows.present", "fail", f"Missing workflows dir: {workflows_dir.as_posix()}", "Create workflows/ and add a workflow json.")  
  
    # E) Selectors  
    selectors_path = rootp / str(cfg_in.get("SELECTORS_PATH") or "data/selectors.json")  
    if selectors_path.exists() and selectors_path.is_file():  
        ok, msg = _safe_json_load(selectors_path)  
        add("selectors.json", "ok" if ok else "fail", msg, "Fix JSON or ensure selectors file exists.")  
    else:  
        add("selectors.json", "fail", f"Missing selectors file: {selectors_path.as_posix()}", "Create data/selectors.json with valid JSON.")  
  
    # F) Schema/Registry  
    schema_dir = rootp / str(cfg_in.get("SCHEMA_DIR") or "SCHEMA")  
    if schema_dir.exists() and schema_dir.is_dir():  
        add("schema.present", "ok", f"Schema dir exists: {schema_dir.as_posix()}")  
    else:  
        add("schema.present", "fail", f"Missing schema dir: {schema_dir.as_posix()}", "Ensure SCHEMA/ exists (or set cfg SCHEMA_DIR).")  
  
    # Registry import (best-effort)  
    # Ensure root is importable for package checks when running from elsewhere  
    with _prepend_sys_path(rootp):  
        ok, msg = _import_registry_best_effort()  
    add(  
        "registry.import",  
        "ok" if ok else "warn",  
        msg,  
        "Ensure REGISTRY package exists and is importable (or verify registry file location).",  
    )  
  
    # G) Optional Git sanity  
    branch = _detect_git_branch(rootp)  
    if branch is None:  
        add("git.branch", "warn", "No .git detected", "If this is a git repo, ensure .git/ exists.")  
    else:  
        add("git.branch", "ok", f"Git: {branch}")  
  
    # Summarize  
    ok_n = sum(1 for c in checks if c["status"] == "ok")  
    warn_n = sum(1 for c in checks if c["status"] == "warn")  
    fail_n = sum(1 for c in checks if c["status"] == "fail")  
  
    overall_ok = fail_n == 0 and (warn_n == 0 if strict else True)  
  
    return {  
        "ok": bool(overall_ok),  
        "generated_at": _utc_now_iso(),  
        "root": rootp.as_posix(),  
        "strict": bool(strict),  
        "checks": checks,  
        "summary": {"ok": ok_n, "warn": warn_n, "fail": fail_n},  
    }  
  
  
def format_preflight_report(result: dict) -> str:  
    if not isinstance(result, dict):  
        return "Invalid preflight result.\n"  
  
    ok = result.get("ok")  
    root = result.get("root")  
    strict = result.get("strict")  
    gen = result.get("generated_at")  
    summ = result.get("summary") or {}  
    checks = result.get("checks") or []  
  
    lines: List[str] = []  
    lines.append("DOCTOR-1A Preflight Report")  
    lines.append(f"- root: {root}")  
    lines.append(f"- generated_at_utc: {gen}")  
    lines.append(f"- strict: {strict}")  
    lines.append(f"- overall_ok: {ok}")  
    lines.append(f"- summary: ok={summ.get('ok')} warn={summ.get('warn')} fail={summ.get('fail')}")  
    lines.append("")  
  
    for c in checks:  
        if not isinstance(c, dict):  
            continue  
        name = c.get("name")  
        status = c.get("status")  
        details = c.get("details") or ""  
        hint = c.get("hint") or ""  
        lines.append(f"[{status}] {name}: {details}")  
        if hint:  
            lines.append(f"      hint: {hint}")  
  
    return "\n".join(lines).rstrip() + "\n"  