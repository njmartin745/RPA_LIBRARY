"""  
Dev smoke test — PIPE-1B (worklist configuration adapter)  
  
Purpose  
-------  
Validate that PIPE.pipe_1b_worklist_config correctly:  
1) Resolves configuration into a normalized worklist spec  
2) Loads IDs from an Excel worklist via INPUT-1B through the PIPE-1B adapter  
  
How it works  
------------  
- If env var WORKLIST_PATH points to an existing Excel file, the script uses it.  
- Otherwise, it attempts to generate a temporary .xlsx using pandas (if available).  
  
Config keys used (required by test)  
-----------------------------------  
- WORKLIST_PATH  
- WORKLIST_SHEET  
- WORKLIST_ID_COLUMN  
"""  
  
from __future__ import annotations  
  
import os  
import sys  
import tempfile  
import traceback  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT)) 

from PIPE.pipe_1b_worklist_config import resolve_worklist_spec, load_ids  
  
  
def _try_build_temp_excel(path: Path, sheet: str, id_column: str) -> None:  
    """  
    Attempt to create a temporary Excel file with a simple ID column.  
    Requires pandas + an Excel writer engine (e.g., openpyxl).  
    """  
    try:  
        import pandas as pd  # type: ignore  
    except Exception as e:  
        raise RuntimeError(  
            "Could not import pandas to generate a temporary Excel worklist. "  
            "Either install pandas+openpyxl OR set env var WORKLIST_PATH to an existing .xlsx file."  
        ) from e  
  
    df = pd.DataFrame(  
        {  
            id_column: ["A001", "A002", "A003", "A004", "A005", "A006"],  
            "OTHER_COL": ["x", "y", "z", "u", "v", "w"],  
        }  
    )  
  
    try:  
        # Prefer openpyxl for xlsx; if unavailable, pandas will raise.  
        with pd.ExcelWriter(path, engine="openpyxl") as writer:  # type: ignore[arg-type]  
            df.to_excel(writer, index=False, sheet_name=sheet)  
    except Exception as e:  
        raise RuntimeError(  
            "Failed to write temporary Excel file. Ensure 'openpyxl' is installed "  
            "(pip install openpyxl)."  
        ) from e  
  
  
def main() -> int:  
    # Required keys per intake requirements  
    sheet = os.environ.get("WORKLIST_SHEET", "Worklist")  
    id_column = os.environ.get("WORKLIST_ID_COLUMN", "ID")  
  
    env_path = os.environ.get("WORKLIST_PATH")  
    tmp_dir = None  
  
    try:  
        if env_path and Path(env_path).expanduser().exists():  
            worklist_path = str(Path(env_path).expanduser().resolve())  
            print(f"[dev_smoke_pipe_1b] Using WORKLIST_PATH from env: {worklist_path}")  
        else:  
            tmp_dir = tempfile.TemporaryDirectory(prefix="dev_smoke_pipe_1b_")  
            worklist_path = str(Path(tmp_dir.name) / "worklist.xlsx")  
            print(f"[dev_smoke_pipe_1b] No valid WORKLIST_PATH provided; generating temp Excel at: {worklist_path}")  
            _try_build_temp_excel(Path(worklist_path), sheet=sheet, id_column=id_column)  
  
        cfg = {  
            "WORKLIST_PATH": worklist_path,  
            "WORKLIST_SHEET": sheet,  
            "WORKLIST_ID_COLUMN": id_column,  
        }  
  
        print("\n[dev_smoke_pipe_1b] 1) resolve_worklist_spec(cfg)")  
        spec = resolve_worklist_spec(cfg)  
        print("[dev_smoke_pipe_1b] Resolved spec:")  
        print(spec)  
  
        print("\n[dev_smoke_pipe_1b] 2) load_ids(cfg)")  
        ids = load_ids(cfg)  
  
        print(f"[dev_smoke_pipe_1b] Loaded IDs: {len(ids)}")  
        print(f"[dev_smoke_pipe_1b] First few IDs: {ids[:5]}")  
  
        # Basic sanity  
        if not isinstance(ids, list) or any(not isinstance(x, str) for x in ids):  
            raise AssertionError("load_ids(cfg) did not return list[str].")  
  
        return 0  
  
    except Exception as e:  
        print("\n[dev_smoke_pipe_1b] FAILED")  
        print(f"[dev_smoke_pipe_1b] Error: {type(e).__name__}: {e}")  
        print("[dev_smoke_pipe_1b] Traceback:")  
        traceback.print_exc()  
        print(  
            "\n[dev_smoke_pipe_1b] Diagnostics / Next steps:\n"  
            "- Ensure INPUT/input_1b_excel_provider.py is present and importable.\n"  
            "- If you do not have pandas/openpyxl installed, set WORKLIST_PATH to an existing .xlsx file.\n"  
            "- Optionally set WORKLIST_SHEET and WORKLIST_ID_COLUMN env vars to match your file."  
        )  
        return 1  
  
    finally:  
        if tmp_dir is not None:  
            tmp_dir.cleanup()  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  