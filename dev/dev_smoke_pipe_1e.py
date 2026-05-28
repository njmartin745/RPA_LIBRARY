"""  
How to run:  
  python dev_smoke_pipe_1e.py  
"""  
  
from __future__ import annotations  
  
import importlib  
import json  
import tempfile  
import traceback  
import zipfile  
from datetime import datetime, timezone  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
      
from typing import Any, Dict, List, Tuple  
from xml.sax.saxutils import escape as _xml_escape  
  
from PIPE.pipe_1e_runner import run_pipeline  
  
  
def _detect_input_defaults() -> Tuple[str, str]:  
    sheet_default = "Worklist"  
    header_default = "ACCOUNT_ID"  
    try:  
        m = importlib.import_module("INPUT.input_1b_excel_provider")  
    except Exception:  
        return sheet_default, header_default  
  
    for name in ("DEFAULT_SHEET", "WORKLIST_SHEET_DEFAULT", "SHEET_DEFAULT", "WORKLIST_SHEET"):  
        v = getattr(m, name, None)  
        if isinstance(v, str) and v.strip():  
            sheet_default = v.strip()  
            break  
  
    for name in ("DEFAULT_HEADER", "DEFAULT_ID_HEADER", "WORKLIST_HEADER_DEFAULT", "ID_HEADER_DEFAULT"):  
        v = getattr(m, name, None)  
        if isinstance(v, str) and v.strip():  
            header_default = v.strip()  
            break  
  
    return sheet_default, header_default  
  
  
def _col_letter(n: int) -> str:  
    return chr(ord("A") + (n - 1))  
  
  
def _cell_inline_str(r: int, c: int, text: str) -> str:  
    ref = f"{_col_letter(c)}{r}"  
    t = _xml_escape(text)  
    return f'<c r="{ref}" t="inlineStr"><is><t>{t}</t></is></c>'  
  
  
def _write_minimal_xlsx(path: str, sheet_name: str, headers: List[str], rows: List[List[str]]) -> None:  
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
        "<sheetData>" + "".join(sheet_rows) + "</sheetData>"  
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
        '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'  
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
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '  
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'  
        "<dc:title>PIPE-1E Smoke Worklist</dc:title>"  
        "<dc:creator>dev_smoke_pipe_1e</dc:creator>"  
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'  
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'  
        "</cp:coreProperties>"  
    )  
  
    app_xml = (  
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'  
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '  
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'  
        "<Application>dev_smoke_pipe_1e</Application>"  
        "</Properties>"  
    )  
  
    rels_xml = (  
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'  
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'  
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '  
        'Target="xl/workbook.xml"/>'  
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '  
        'Target="docProps/core.xml"/>'  
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '  
        'Target="docProps/app.xml"/>'  
        "</Relationships>"  
    )  
  
    content_types_xml = (  
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'  
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'  
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'  
        '<Default Extension="xml" ContentType="application/xml"/>'  
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'  
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'  
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'  
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
  
  
def main() -> int:  
    try:  
        with tempfile.TemporaryDirectory(prefix="dev_smoke_pipe_1e_") as td:  
            run_dir = Path(td)  
            sheet, header = _detect_input_defaults()  
  
            worklist_path = run_dir / "worklist.xlsx"  
            _write_minimal_xlsx(str(worklist_path), sheet_name=sheet, headers=[header], rows=[["A001"], ["A002"]])  
  
            manifest_path = run_dir / "manifest.jsonl"  
            log_path = run_dir / "run.log.jsonl"  
  
            steps_inline: List[Dict[str, Any]] = [  
                {"action": "get", "url": "https://example.com"},  
                {"action": "wait_for_element", "by": "css", "value": "h1"},  
                # MUST return an object/dict (not a string)  
                {"action": "js", "script": "return {ok: true, title: document.title, url: document.location.href};", "save_as": "page_info"},  
            ]  
  
            cfg: Dict[str, Any] = {  
                "WORKLIST_PATH": str(worklist_path),  
                "STEPS": steps_inline,  
                "MANIFEST_PATH": str(manifest_path),  
                "LOG_PATH": str(log_path),  
  
                "HEADLESS": True,  
                "BROWSER": "edge",  
  
                # optional knobs supported by runner (safe if ignored by underlying modules)  
                "STOP_ON_ERROR": True,  
                "EXPLICIT_WAIT": 10,  
            }  
  
            summary, code = run_pipeline(cfg)  
  
            print("\n=== dev_smoke_pipe_1e ===")  
            print(f"run_dir:   {run_dir}")  
            print(f"worklist:  {worklist_path} (sheet={sheet!r}, header={header!r})")  
            print(f"manifest:  {manifest_path}")  
            print(f"log:       {log_path}")  
            print("summary:")  
            print(json.dumps(summary, indent=2, default=str))  
  
            if code == 0:  
                print("\nPASS: dev_smoke_pipe_1e")  
            else:  
                print(f"\nFAIL: dev_smoke_pipe_1e (exit_code={code})")  
  
            return code  
  
    except Exception as e:  
        print("\nFAIL: dev_smoke_pipe_1e (exception)")  
        print(f"Error: {type(e).__name__}: {e}")  
        traceback.print_exc()  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  