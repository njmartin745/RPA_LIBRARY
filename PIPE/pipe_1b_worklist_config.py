"""  
PIPE-1B — Worklist configuration adapter  
=======================================  
  
Purpose  
-------  
Provide a stable adapter between PIPE orchestrators and INPUT providers by:  
- Normalizing worklist configuration from `cfg`  
- Accepting multiple aliases for Excel sheet and ID column  
- Loading a list of work item IDs via INPUT-1B (Excel provider) using introspection  
  
Public API  
----------  
resolve_worklist_spec(cfg) -> {"path": str, "sheet": str, "id_column": str}  
load_ids(cfg) -> list[str]  
"""  
  
from __future__ import annotations  
  
import importlib  
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional  
  
__all__ = ["resolve_worklist_spec", "load_ids"]  
  
  
# -----------------------------  
# Config normalization helpers  
# -----------------------------  
def _is_present(v: Any) -> bool:  
    if v is None:  
        return False  
    if isinstance(v, str):  
        return bool(v.strip())  
    return True  
  
  
def _as_str(v: Any) -> str:  
    # Path-like objects are fine; just stringify.  
    return str(v).strip()  
  
  
def _first_present(cfg: Mapping[str, Any], keys: Iterable[str]) -> Optional[Any]:  
    for k in keys:  
        if k in cfg and _is_present(cfg.get(k)):  
            return cfg.get(k)  
    return None  
  
  
def resolve_worklist_spec(cfg: Mapping[str, Any]) -> Dict[str, str]:  
    """  
    Normalize worklist configuration from `cfg`.  
  
    Accepted aliases  
    ----------------  
    Path:  
      - WORKLIST_PATH, WORKLIST_XLSX, INPUT_XLSX  
      - EXCEL_PATH, INPUT_EXCEL_PATH, RPA_EXCEL_PATH  
      - worklist.path (nested dict), excel.path (nested dict)  
  
    Sheet:  
      - WORKLIST_SHEET, WORKLIST_SHEET_NAME, EXCEL_SHEET, SHEET, SHEET_NAME  
      - worklist.sheet, excel.sheet  
  
    ID column:  
      - WORKLIST_ID_COLUMN, ID_COLUMN, EXCEL_ID_COLUMN, EXCEL_KEY_COLUMN, KEY_COLUMN  
      - worklist.id_column, excel.id_column  
    """  
    if cfg is None:  
        cfg = {}  
  
    # Support nested configuration (non-breaking convenience)  
    worklist_nested = cfg.get("WORKLIST") or cfg.get("worklist")  
    excel_nested = cfg.get("EXCEL") or cfg.get("excel")  
  
    wl: Mapping[str, Any] = worklist_nested if isinstance(worklist_nested, Mapping) else {}  
    ex: Mapping[str, Any] = excel_nested if isinstance(excel_nested, Mapping) else {}  
  
    path_aliases = (  
        "WORKLIST_PATH",  
        "WORKLIST_XLSX",  
        "INPUT_XLSX",  
        "EXCEL_PATH",  
        "INPUT_EXCEL_PATH",  
        "RPA_EXCEL_PATH",  
    )  
    sheet_aliases = (  
        "WORKLIST_SHEET",  
        "WORKLIST_SHEET_NAME",  
        "EXCEL_SHEET",  
        "SHEET",  
        "SHEET_NAME",  
    )  
    id_col_aliases = (  
        "WORKLIST_ID_COLUMN",  
        "ID_COLUMN",  
        "EXCEL_ID_COLUMN",  
        "EXCEL_KEY_COLUMN",  
        "KEY_COLUMN",  
    )  
  
    path_val = _first_present(cfg, path_aliases)  
    if not _is_present(path_val):  
        path_val = _first_present(wl, ("path", "excel_path")) or _first_present(ex, ("path", "excel_path"))  
  
    sheet_val = _first_present(cfg, sheet_aliases)  
    if not _is_present(sheet_val):  
        sheet_val = _first_present(wl, ("sheet", "sheet_name")) or _first_present(ex, ("sheet", "sheet_name"))  
  
    id_col_val = _first_present(cfg, id_col_aliases)  
    if not _is_present(id_col_val):  
        id_col_val = _first_present(wl, ("id_column", "key_column")) or _first_present(  
            ex, ("id_column", "key_column")  
        )  
  
    missing: List[str] = []  
    if not _is_present(path_val):  
        missing.append(  
            "path (one of: WORKLIST_PATH, WORKLIST_XLSX, INPUT_XLSX, EXCEL_PATH, INPUT_EXCEL_PATH, "  
            "RPA_EXCEL_PATH, or nested worklist.path)"  
        )  
    if not _is_present(sheet_val):  
        missing.append(  
            "sheet (one of: WORKLIST_SHEET, WORKLIST_SHEET_NAME, EXCEL_SHEET, SHEET, SHEET_NAME, "  
            "or nested worklist.sheet)"  
        )  
    if not _is_present(id_col_val):  
        missing.append(  
            "id_column (one of: WORKLIST_ID_COLUMN, ID_COLUMN, EXCEL_ID_COLUMN, EXCEL_KEY_COLUMN, KEY_COLUMN, "  
            "or nested worklist.id_column)"  
        )  
    if missing:  
        raise KeyError("Missing required worklist configuration: " + "; ".join(missing))  
  
    return {  
        "path": _as_str(path_val),  
        "sheet": _as_str(sheet_val),  
        "id_column": _as_str(id_col_val),  
    }  
  
  
# -----------------------------  
# Provider adapter / loader  
# -----------------------------  
def _normalize_ids(raw: Any) -> List[str]:  
    """  
    Convert provider output to list[str] with basic sanitation.  
    Filters empty values and obvious 'nan'/'none' string artifacts.  
    """  
    if raw is None:  
        return []  
  
    # pandas Series / numpy arrays often expose .tolist()  
    if hasattr(raw, "tolist") and callable(getattr(raw, "tolist")):  
        raw = raw.tolist()  
  
    if isinstance(raw, (str, bytes)):  
        raise TypeError(f"Worklist provider returned a scalar ({type(raw).__name__}); expected an iterable of IDs.")  
  
    try:  
        iterable = list(raw)  
    except TypeError as e:  
        raise TypeError(  
            f"Worklist provider returned non-iterable ({type(raw).__name__}); expected an iterable of IDs."  
        ) from e  
  
    out: List[str] = []  
    for v in iterable:  
        if v is None:  
            continue  
        if isinstance(v, Mapping):  
            raise TypeError("Worklist provider returned mapping/dict items; expected plain ID values (strings).")  
        s = str(v).strip()  
        if not s:  
            continue  
        if s.lower() in {"nan", "none", "null"}:  
            continue  
        out.append(s)  
    return out  
  
  
def load_ids(cfg: Mapping[str, Any]) -> List[str]:  
    """  
    Load worklist IDs using INPUT-1B (Excel provider) when available.  
  
    This function:  
    - Normalizes cfg -> worklist spec (path/sheet/id_column)  
    - Imports INPUT.input_1b_excel_provider  
    - Populates compatibility aliases expected by INPUT-1B (e.g., WORKLIST_XLSX / INPUT_XLSX, and header aliases)  
    - Uses introspection to call a compatible loader function  
    - Returns list[str] of IDs or raises clear errors  
    """  
    spec = resolve_worklist_spec(cfg)  
  
    # Build a compatibility cfg that satisfies multiple possible key conventions.  
    # Do NOT mutate caller cfg.  
    compat_cfg: Dict[str, Any] = dict(cfg or {})  
    compat_cfg.update(  
        {  
            # PIPE-facing  
            "WORKLIST_PATH": spec["path"],  
            "WORKLIST_SHEET": spec["sheet"],  
            "WORKLIST_SHEET_NAME": spec["sheet"],  
            "WORKLIST_ID_COLUMN": spec["id_column"],  
            "ID_COLUMN": spec["id_column"],  
            # Common/legacy  
            "EXCEL_PATH": spec["path"],  
            "EXCEL_SHEET": spec["sheet"],  
            "EXCEL_KEY_COLUMN": spec["id_column"],  
            "KEY_COLUMN": spec["id_column"],  
            "EXCEL_ID_COLUMN": spec["id_column"],  
        }  
    )  
  
    # INPUT-1B expects WORKLIST_XLSX or INPUT_XLSX for the workbook path.  
    if not _is_present(compat_cfg.get("WORKLIST_XLSX")):  
        compat_cfg["WORKLIST_XLSX"] = spec["path"]  
    if not _is_present(compat_cfg.get("INPUT_XLSX")):  
        compat_cfg["INPUT_XLSX"] = spec["path"]  
  
    # INPUT-1B uses a "header" concept (defaulting to 'ACCOUNT_ID' if not provided).  
    # Provide header aliases derived from the resolved id_column.  
    # Only set if missing/blank to avoid overriding user intent.  
    for k in (  
        "WORKLIST_HEADER",  
        "WORKLIST_ID_HEADER",  
        "INPUT_HEADER",  
        "EXCEL_HEADER",  
        "HEADER",  
        # additional safe aliases seen in similar configs  
        "WORKLIST_COLUMN",  
        "WORKLIST_KEY_COLUMN",  
    ):  
        if not _is_present(compat_cfg.get(k)):  
            compat_cfg[k] = spec["id_column"]  
  
    try:  
        mod = importlib.import_module("INPUT.input_1b_excel_provider")  
    except Exception as e:  
        raise ImportError(  
            "INPUT-1B Excel provider not available. Expected module: 'INPUT.input_1b_excel_provider'."  
        ) from e  
  
    # Prefer explicit list-returning function names; fall back to iterator forms.  
    candidates: List[tuple[str, Callable[[], Any]]] = []  
  
    for fn_name in ("load_worklist_ids", "load_ids", "get_ids"):  
        fn = getattr(mod, fn_name, None)  
        if callable(fn):  
            candidates.append((fn_name, lambda fn=fn: fn(compat_cfg)))  
  
    iter_fn = getattr(mod, "iter_worklist_ids", None)  
    if callable(iter_fn):  
        candidates.append(("iter_worklist_ids", lambda: list(iter_fn(compat_cfg))))  
  
    if not candidates:  
        public_callables = sorted(  
            n for n in dir(mod) if not n.startswith("_") and callable(getattr(mod, n, None))  
        )  
        raise AttributeError(  
            "INPUT.input_1b_excel_provider does not expose a supported loader API. "  
            "Expected one of: load_worklist_ids(cfg), iter_worklist_ids(cfg), load_ids(cfg), get_ids(cfg). "  
            f"Available callables: {public_callables}"  
        )  
  
    last_err: Optional[BaseException] = None  
    for _name, thunk in candidates:  
        try:  
            raw_ids = thunk()  
            return _normalize_ids(raw_ids)  
        except Exception as e:  
            last_err = e  
  
    raise RuntimeError(  
        "Failed to load worklist IDs via INPUT-1B provider. "  
        f"Worklist spec: path={spec['path']!r}, sheet={spec['sheet']!r}, id_column={spec['id_column']!r}. "  
        f"Tried provider functions: {[n for n, _ in candidates]!r}. "  
        f"Last error: {type(last_err).__name__}: {last_err}"  
    ) from last_err  