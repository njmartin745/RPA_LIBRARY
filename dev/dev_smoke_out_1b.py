"""  
How to run:  
  python dev/dev_smoke_out_1b.py  
"""  
  
from __future__ import annotations  
  
import tempfile  
from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  
  
from OUT.out_1b_artifact_manager import normalize_download  
  
  
def _write_file(path: Path, data: bytes) -> Path:  
    path.parent.mkdir(parents=True, exist_ok=True)  
    path.write_bytes(data)  
    return path  
  
  
def main() -> int:  
    with tempfile.TemporaryDirectory(prefix="dev_smoke_out_1b_") as td:  
        base = Path(td)  
        downloads = base / "downloads"  
        out_dir = base / "out"  
        archive_dir = base / "archive"  
  
        # 1) Create a fake downloaded file and normalize it.  
        dl1 = _write_file(downloads / "report.xlsx", b"first")  
        p1 = normalize_download(  
            dl1,  
            out_dir=out_dir,  
            run_id="RUN1",  
            item_id="A100",  
            base_name="report",  
            overwrite=False,  
            archive_dir=None,  
        )  
  
        # 2) Create another fake downloaded file with same source name; normalize again with overwrite=False.  
        dl2 = _write_file(downloads / "report.xlsx", b"second")  
        p2 = normalize_download(  
            dl2,  
            out_dir=out_dir,  
            run_id="RUN1",  
            item_id="A100",  
            base_name="report",  
            overwrite=False,  
            archive_dir=None,  
        )  
  
        ok = True  
        ok = ok and p1.exists() and p2.exists()  
        ok = ok and (p1 != p2)  
        ok = ok and ("__v2" in p2.name or "__v3" in p2.name)  # allow future suffixes  
        ok = ok and (p1.read_bytes() == b"first")  
        ok = ok and (p2.read_bytes() == b"second")  
  
        # 3) Now test archive_dir + overwrite=True  
        #    - existing canonical file should be archived  
        #    - new file should be placed at canonical name  
        dl3 = _write_file(downloads / "report.xlsx", b"third")  
        p3 = normalize_download(  
            dl3,  
            out_dir=out_dir,  
            run_id="RUN1",  
            item_id="A100",  
            base_name="report",  
            overwrite=True,  
            archive_dir=archive_dir,  
        )  
  
        # canonical name should match p1 (not versioned)  
        ok = ok and (p3.name == p1.name)  
        ok = ok and p3.exists()  
        ok = ok and (p3.read_bytes() == b"third")  
  
        # archived should contain at least one file (the prior canonical)  
        archived_files = list(archive_dir.glob("*"))  
        ok = ok and (len(archived_files) >= 1)  
  
        print("\n=== dev_smoke_out_1b ===")  
        print(f"out_dir:      {out_dir}")  
        print(f"archive_dir:  {archive_dir}")  
        print(f"first:        {p1}")  
        print(f"second:       {p2}")  
        print(f"third:        {p3}")  
        if archived_files:  
            print(f"archived[0]:   {archived_files[0]}")  
  
        if ok:  
            print("PASS: dev_smoke_out_1b")  
            return 0  
  
        print("FAIL: dev_smoke_out_1b")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  