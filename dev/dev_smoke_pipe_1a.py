# dev_smoke_pipe_1a.py  
"""  
Dev smoke test for PIPE-1A run orchestrator.  
  
Creates a tiny 2-ID worklist (as an .xlsx) and runs a short step sequence against  
example.com through the full pipeline:  
INPUT-1B -> LOOP-1B -> ACT-1B -> STATE-1B, with LOG-1A enabled.  
  
Run:  
  python dev_smoke_pipe_1a.py  
"""  
  
from __future__ import annotations  
  
import json  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from PIPE.pipe_1a_run_orchestrator import run_worklist  
  
  
def _write_demo_xlsx(path: Path) -> None:  
    # Assumes openpyxl is available (likely already required by INPUT-1B).  
    from openpyxl import Workbook  # type: ignore  
  
    wb = Workbook()  
    ws = wb.active  
    ws.title = "Worklist"  
    ws.append(["id"])  
    ws.append(["ID-001"])  
    ws.append(["ID-002"])  
    path.parent.mkdir(parents=True, exist_ok=True)  
    wb.save(path)  
  
  
def main() -> int:  
    tmp_dir = Path(".dev_tmp").resolve()  
    xlsx_path = tmp_dir / "worklist.xlsx"  
    _write_demo_xlsx(xlsx_path)  
  
    # Provide a broad set of likely INPUT-1B keys (INPUT-1B will use whichever it expects).  
    # This avoids redefining INPUT-1B while making the smoke test resilient.  
    cfg = {  
        "BROWSER": "edge",  
        "HEADLESS": "true",  
        "EXPLICIT_WAIT": 15,  
        "STOP_ON_ERROR": True,  
        "LOG_LEVEL": "INFO",  
        "LOG_PATH": str(tmp_dir / "run.log"),  
        # Common possible INPUT keys:  
        "INPUT_PATH": str(xlsx_path),  
        "INPUT_XLSX_PATH": str(xlsx_path),  
        "WORKLIST_PATH": str(xlsx_path),  
        "WORKLIST_XLSX": str(xlsx_path),  
        "EXCEL_PATH": str(xlsx_path),  
        "WORKLIST_SHEET": "Worklist",
        "WORKLIST_HEADER": "id",
        "SHEET": "Worklist",  
        "SHEET_NAME": "Worklist",  
        "WORKSHEET": "Worklist",  
        "ID_COLUMN": "id",  
        "KEY_COLUMN": "id",  
        "WORKLIST_ID_COLUMN": "id",  
        # Common possible STATE keys:  
        "MANIFEST_PATH": str(tmp_dir / "manifest.jsonl"),  
        "STATE_PATH": str(tmp_dir / "manifest.jsonl"),  
    }  
  
    steps = [  
        {"action": "get", "url": "https://example.com", "step_id": "s1"},  
        {"action": "wait_for_element", "by": "css", "selector": "h1", "step_id": "s2"},  
        {"action": "js", "step_id": "s3", "script": "return {ok:true, title: document.title};", "save_as": "PAGE"},  
    ]  
  
    summary = run_worklist(cfg, steps)  
    print(json.dumps(summary, indent=2))  
    print(f"Manifest (if written): {cfg.get('MANIFEST_PATH')}")  
    print(f"Log file (if enabled): {cfg.get('LOG_PATH')}")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  