import io  
from contextlib import redirect_stdout  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))  
  
from CLI.cli_2b_unified import main  
  
  
def _run_cli(argv):  
    buf = io.StringIO()  
    with redirect_stdout(buf):  
        code = main(argv)  
    return code, buf.getvalue()  
  
  
def main_smoke() -> None:  
    out_dir = Path(".dev_tmp/cli_2b_smoke")  
    out_dir.mkdir(parents=True, exist_ok=True)  
  
    # auto command (build only)  
    code1, out1 = _run_cli(  
        ["auto", "open example.com and verify page title", "--output-dir", str(out_dir)]  
    )  
    assert code1 in (0, 1)  # allow build failure if environment lacks BUILD deps, but must not crash  
    assert "AUTO" in out1  
  
    # doctor command (must not throw, should print something)  
    code2, out2 = _run_cli(["doctor"])  
    assert code2 in (0, 1)  
    assert "DOCTOR" in out2  
  
    print("dev_smoke_cli_2b.py: PASS")  
    print(out1.strip().splitlines()[:12])  
    print(out2.strip().splitlines()[:12])  
  
  
if __name__ == "__main__":  
    main_smoke()  