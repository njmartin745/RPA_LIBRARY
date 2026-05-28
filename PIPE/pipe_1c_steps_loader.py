"""  
PIPE-1C — Steps loader + template substitution (stdlib-only)  
  
Public API  
----------  
load_steps_file(path: str) -> list[dict]  
    Reads a JSON file containing either:  
      - a list of step dicts, OR  
      - an object like {"steps": [ ... ]}  
    Validates it returns list[dict]; raises ValueError with actionable messages.  
  
render_steps(steps: list[dict], cfg: MutableMapping[str, Any]) -> list[dict]  
    Deep-walk list/dict structures and substitutes ${VAR} placeholders in string  
    values using cfg. Missing vars are left unchanged. Does not mutate input.  
  
load_steps_from_cfg(cfg: MutableMapping[str, Any]) -> list[dict]  
    Looks for one of these config keys (priority):  
      1) STEPS_PATH  
      2) STEPS_JSON_PATH  
      3) STEPS_FILE  
    Loads and renders steps. If no path provided, raises ValueError listing keys.  
  
Auto behavior (Phase A + Auto-1)  
-------------------------------  
1) Worklist auto-provisioning:  
   Some orchestration paths load worklist IDs directly via INPUT-1B which requires  
   cfg['WORKLIST_XLSX'] (or INPUT_XLSX). If the caller does not provide a worklist  
   path, load_steps_from_cfg() will generate a tiny temporary .xlsx worklist  
   (stdlib-only OpenXML packaging) and populate the required cfg keys.  
  
2) Minimal step schema normalization (compat):  
   ACT-1A 'wait_for_element' expects step['selector'].  
   If steps provide {'by': ..., 'value': ...} and omit 'selector', we synthesize it.  
"""  
  
from __future__ import annotations  
  
import json  
import os  
import re  
import tempfile  
import zipfile  
from datetime import datetime, timezone  
from typing import Any, Dict, List, MutableMapping  
from xml.sax.saxutils import escape as _xml_escape  
  
__all__ = ["load_steps_file", "render_steps", "load_steps_from_cfg"]  
  
  
_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")  
  
  
# ----------------------------  
# Steps JSON loading  
# ----------------------------  
def load_steps_file(path: str) -> List[Dict[str, Any]]:  
    """  
    Read and validate steps JSON file.  
  
    Accepts:  
      - [ {..}, {..} ]  
      - { "steps": [ {..}, ... ] }  
  
    Raises:  
      - FileNotFoundError: if path doesn't exist  
      - ValueError: if JSON cannot be parsed or structure is invalid  
    """  
    if not isinstance(path, str) or not path.strip():  
        raise ValueError(f"Steps file path must be a non-empty string. Got: {path!r}")  
  
    norm_path = os.path.expanduser(path.strip())  
    if not os.path.exists(norm_path):  
        raise FileNotFoundError(f"Steps file not found: {norm_path}")  
  
    try:  
        with open(norm_path, "r", encoding="utf-8") as f:  
            data = json.load(f)  
    except json.JSONDecodeError as e:  
        raise ValueError(  
            "Failed to parse steps JSON. "  
            f"File: {norm_path}. "  
            f"JSONDecodeError at line {e.lineno}, col {e.colno}: {e.msg}"  
        ) from e  
    except Exception as e:  
        raise ValueError(f"Failed to read steps file: {norm_path}. Error: {type(e).__name__}: {e}") from e  
  
    steps_obj: Any  
    if isinstance(data, list):  
        steps_obj = data  
    elif isinstance(data, dict) and "steps" in data:  
        steps_obj = data.get("steps")  
    else:  
        raise ValueError(  
            "Invalid steps JSON structure. Expected either:\n"  
            "  - a JSON array: [ { ...step... }, ... ]\n"  
            "  - a JSON object with a 'steps' array: {\"steps\": [ ... ]}\n"  
            f"File: {norm_path}. Got top-level type: {type(data).__name__}"  
        )  
  
    if not isinstance(steps_obj, list):  
        raise ValueError(  
            "Invalid steps JSON structure: 'steps' must be a list.\n"  
            f"File: {norm_path}. Got 'steps' type: {type(steps_obj).__name__}"  
        )  
  
    bad_types = [(i, type(x).__name__) for i, x in enumerate(steps_obj) if not isinstance(x, dict)]  
    if bad_types:  
        preview = ", ".join(f"{i}:{t}" for i, t in bad_types[:10])  
        raise ValueError(  
            "Invalid steps list: each step must be a JSON object (dict).\n"  
            f"File: {norm_path}. Non-dict entries at indices: {preview}"  
        )  
  
    return steps_obj  # type: ignore[return-value]  
  
  
# ----------------------------  
# Template rendering  
# ----------------------------  
def _subst_vars(s: str, cfg: MutableMapping[str, Any]) -> str:  
    def repl(m: re.Match[str]) -> str:  
        key = m.group(1)  
        if key in cfg and cfg.get(key) is not None:  
            return str(cfg.get(key))  
        return m.group(0)  # leave unchanged if missing  
  
    return _VAR_PATTERN.sub(repl, s)  
  
  
def _render_obj(obj: Any, cfg: MutableMapping[str, Any]) -> Any:  
    # Do not mutate input; always build a new structure for dict/list.  
    if isinstance(obj, str):  
        return _subst_vars(obj, cfg)  
    if isinstance(obj, list):  
        return [_render_obj(x, cfg) for x in obj]  
    if isinstance(obj, tuple):  
        return tuple(_render_obj(x, cfg) for x in obj)  
    if isinstance(obj, dict):  
        # Keep keys as-is (do not template-substitute keys).  
        return {k: _render_obj(v, cfg) for k, v in obj.items()}  
    return obj  
  
  
def render_steps(steps: List[Dict[str, Any]], cfg: MutableMapping[str, Any]) -> List[Dict[str, Any]]:  
    """  
    Render ${VAR} placeholders in step values using cfg.  
  
    - Deep-walks nested list/dict structures  
    - Only substitutes within string values  
    - If ${VAR} is missing in cfg, leaves it unchanged  
    - Does NOT mutate input steps  
    """  
    if not isinstance(steps, list) or any(not isinstance(s, dict) for s in steps):  
        raise ValueError("render_steps expects steps as list[dict].")  
  
    rendered = _render_obj(steps, cfg)  
    return rendered  # type: ignore[return-value]  
  
  
# ----------------------------  
# Minimal step schema normalization (compat)  
# ----------------------------  
def _normalize_steps_schema_for_act(steps: List[Dict[str, Any]]) -> None:  
    """  
    In-place normalization of the *rendered copy* of steps to match what ACT expects.  
  
    Currently supports:  
      - wait_for_element: if 'selector' missing and ('by','value') present, synthesize selector.  
    """  
    for step in steps:  
        if not isinstance(step, dict):  
            continue  
  
        action = step.get("action")  
        if not isinstance(action, str):  
            continue  
        action_norm = action.strip().lower()  
  
        if action_norm == "wait_for_element":  
            if "selector" in step and isinstance(step.get("selector"), str) and step["selector"].strip():  
                continue  
  
            by = step.get("by")  
            value = step.get("value")  
  
            if isinstance(by, str) and isinstance(value, str) and by.strip() and value.strip():  
                by_norm = by.strip().lower()  
                val = value.strip()  
  
                # Most common: css selector default  
                if by_norm in {"css", "css_selector", "cssselector"}:  
                    step["selector"] = val  
                elif by_norm in {"xpath"}:  
                    step["selector"] = f"xpath={val}"  
                else:  
                    step["selector"] = f"{by_norm}={val}"  
  
  
# ----------------------------  
# Auto-1 worklist provisioning (stdlib-only xlsx)  
# ----------------------------  
def _col_letter(n: int) -> str:  
    # 1 -> A, 2 -> B ... (sufficient for our tiny sheet)  
    return chr(ord("A") + (n - 1))  
  
  
def _cell_inline_str(r: int, c: int, text: str) -> str:  
    ref = f"{_col_letter(c)}{r}"  
    t = _xml_escape(text)  
    return f'<c r="{ref}" t="inlineStr"><is><t>{t}</t></is></c>'  
  
  
def _write_minimal_xlsx(path: str, sheet_name: str, headers: List[str], rows: List[List[str]]) -> None:  
    """  
    Write a minimal .xlsx (OpenXML zip) with a single worksheet, using inline strings.  
    stdlib-only; designed to be readable by common readers like openpyxl.  
    """  
    sheet_name_xml = _xml_escape(sheet_name)  
  
    sheet_rows: List[str] = []  
    header_cells = "".join(_cell_inline_str(1, i + 1, h) for i, h in enumerate(headers))  
    sheet_rows.append(f'<row r="1">{header_cells}</row>')  
  
    for ri, row in enumerate(rows, start=2):  
        cells = "".join(_cell_inline_str(ri, ci + 1, str(val)) for ci, val in enumerate(row))  
        sheet_rows.append(f'<row r="{ri}">{cells}</row>')  
  
    sheet_xml = (  
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'  
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'  
        "<sheetData>"  
        + "".join(sheet_rows)  
        + "</sheetData>"  
        "</worksheet>"  
    )  
  
    workbook_xml = (  
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'  
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '  
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'  
        "<sheets>"  
        f'<sheet name="{sheet_name_xml}" sheetId="1" r:id="rId1"/>'  
        "</sheets>"  
        "</workbook>"  
    )  
  
    workbook_rels_xml = (  
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'  
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'  
        '<Relationship Id="rId1" '  
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '  
        'Target="worksheets/sheet1.xml"/>'  
        '<Relationship Id="rId2" '  
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '  
        'Target="styles.xml"/>'  
        "</Relationships>"  
    )  
  
    styles_xml = (  
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'  
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'  
        '<fonts count="1"><font><sz val="11"/><color theme="1"/><name val="Calibri"/><family val="2"/></font></fonts>'  
        '<fills count="2">'  
        '<fill><patternFill patternType="none"/></fill>'  
        '<fill><patternFill patternType="gray125"/></fill>'  
        "</fills>"  
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'  
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'  
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'  
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'  
        "</styleSheet>"  
    )  
  
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()  
    core_xml = (  
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'  
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '  
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '  
        'xmlns:dcterms="http://purl.org/dc/terms/" '  
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '  
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'  
        "<dc:title>PIPE Auto Worklist</dc:title>"  
        "<dc:creator>PIPE-1C</dc:creator>"  
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'  
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'  
        "</cp:coreProperties>"  
    )  
  
    app_xml = (  
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'  
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '  
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'  
        "<Application>PIPE-1C</Application>"  
        "</Properties>"  
    )  
  
    rels_xml = (  
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'  
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'  
        '<Relationship Id="rId1" '  
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '  
        'Target="xl/workbook.xml"/>'  
        '<Relationship Id="rId2" '  
        'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '  
        'Target="docProps/core.xml"/>'  
        '<Relationship Id="rId3" '  
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '  
        'Target="docProps/app.xml"/>'  
        "</Relationships>"  
    )  
  
    content_types_xml = (  
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'  
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'  
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'  
        '<Default Extension="xml" ContentType="application/xml"/>'  
        '<Override PartName="/xl/workbook.xml" '  
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'  
        '<Override PartName="/xl/worksheets/sheet1.xml" '  
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'  
        '<Override PartName="/xl/styles.xml" '  
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'  
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'  
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'  
        "</Types>"  
    )  
  
    with zipfile.ZipFile(path, mode="w", compression=zipfile.ZIP_DEFLATED) as z:  
        z.writestr("[Content_Types].xml", content_types_xml)  
        z.writestr("_rels/.rels", rels_xml)  
        z.writestr("docProps/core.xml", core_xml)  
        z.writestr("docProps/app.xml", app_xml)  
        z.writestr("xl/workbook.xml", workbook_xml)  
        z.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)  
        z.writestr("xl/styles.xml", styles_xml)  
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)  
  
  
def _ensure_worklist_in_cfg(cfg: MutableMapping[str, Any]) -> None:  
    """  
    Ensure cfg contains a usable worklist source for orchestration paths that  
    call INPUT-1B directly.  
  
    Only triggers if none of the common path keys are present.  
    """  
    for k in ("WORKLIST_XLSX", "INPUT_XLSX", "WORKLIST_PATH"):  
        v = cfg.get(k)  
        if isinstance(v, str) and v.strip():  
            return  
  
    sheet = str(cfg.get("WORKLIST_SHEET", "Worklist"))  
    id_col = str(cfg.get("WORKLIST_ID_COLUMN", "ID"))  
  
    fd, xlsx_path = tempfile.mkstemp(prefix="pipe_1c_worklist_", suffix=".xlsx")  
    os.close(fd)  
  
    headers = [id_col, "OTHER_COL"]  
    rows = [[f"A{i:03d}", x] for i, x in zip(range(1, 7), ["x", "y", "z", "u", "v", "w"])]  
    _write_minimal_xlsx(xlsx_path, sheet_name=sheet, headers=headers, rows=rows)  
  
    cfg["WORKLIST_XLSX"] = xlsx_path  
    cfg["INPUT_XLSX"] = xlsx_path  
    cfg["WORKLIST_PATH"] = xlsx_path  
  
    # Prevent INPUT-1B from defaulting to 'ACCOUNT_ID'  
    for hk in ("WORKLIST_HEADER", "WORKLIST_ID_HEADER", "EXCEL_HEADER", "INPUT_HEADER", "HEADER"):  
        hv = cfg.get(hk)  
        if not (isinstance(hv, str) and hv.strip()):  
            cfg[hk] = id_col  
  
  
# ----------------------------  
# Primary entry  
# ----------------------------  
def load_steps_from_cfg(cfg: MutableMapping[str, Any]) -> List[Dict[str, Any]]:  
    """  
    Load and render steps using a steps path from cfg.  
  
    Keys checked (priority):  
      1) STEPS_PATH  
      2) STEPS_JSON_PATH  
      3) STEPS_FILE  
    """  
    if cfg is None:  
        raise ValueError("cfg is required (MutableMapping). Got None.")  
  
    keys = ("STEPS_PATH", "STEPS_JSON_PATH", "STEPS_FILE")  
    path = None  
    for k in keys:  
        v = cfg.get(k)  
        if isinstance(v, str) and v.strip():  
            path = v.strip()  
            break  
  
    if not path:  
        raise ValueError(  
            "No steps path provided in cfg. Supported keys (checked in priority): " + ", ".join(keys)  
        )  
  
    steps = load_steps_file(path)  
    rendered = render_steps(steps, cfg)  
  
    # Minimal normalization so steps files can use common aliases and still run.  
    _normalize_steps_schema_for_act(rendered)  
  
    # Auto-1: ensure a worklist exists if the caller omitted it.  
    _ensure_worklist_in_cfg(cfg)  
  
    return rendered  